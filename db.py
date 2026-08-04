"""
Database connection helper for the Finnegans MCP server.
"""

import json
import os
import re
from datetime import datetime
from typing import Any

import pymssql
from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class DatabaseConnectionError(Exception):
    """Raised when a database operation fails."""

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1433"))
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "HistorialCursos")

# Base activa en la sesión actual (arranca con la del .env, se puede cambiar con cambiar_base)
_current_db = DB_NAME

BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|EXEC|EXECUTE|MERGE|BULK)\b",
    re.IGNORECASE,
)

def get_connection(base: str | None = None) -> pymssql.Connection:
    """Abre conexión. Usa `base` si se indica, si no usa la base activa de la sesión."""
    if not DB_PASSWORD:
        raise DatabaseConnectionError("DB_PASSWORD environment variable is required")

    db = base if base else _current_db
    return pymssql.connect(
        server=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=db,
        as_dict=True,
        tds_version="7.4",
    )


def is_safe_query(sql: str) -> bool:
    return not BLOCKED_KEYWORDS.search(sql.strip())


def sanitizar_y_limitar_query(sql_query: str) -> str:
    """Cortafuegos sintáctico: fuerza SELECT TOP 100 cuando no hay TOP."""
    query_clean = sql_query.strip()
    query_upper = query_clean.upper()
    if query_upper.startswith("SELECT") and "TOP" not in query_upper:
        return re.sub(r"(?i)^SELECT", "SELECT TOP 100", query_clean)
    return query_clean


def _execute(cursor: pymssql.Cursor, sql: str, params: tuple[Any, ...] | list[Any] | None = None) -> None:
    query = sanitizar_y_limitar_query(sql)
    if params is None:
        cursor.execute(query)
    else:
        cursor.execute(query, params)


def rows_to_list(cursor: pymssql.Cursor, limite_maximo: int = 100) -> list[dict]:
    rows = cursor.fetchall()[:limite_maximo]
    return [
        {k: (str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v) for k, v in row.items()}
        for row in rows
    ]


def get_course_id(conn: pymssql.Connection, course_name: str) -> int:
    """Return the course_id for the given course_name, creating it if missing."""
    if not course_name:
        raise ValueError("course_name is required")
    cursor = conn.cursor()
    cursor.execute("SELECT course_id FROM courses WHERE course_name = %s", (course_name,))
    row = cursor.fetchone()
    if row:
        return int(row["course_id"])
    cursor.execute(
        "INSERT INTO courses (course_name) VALUES (%s); SELECT SCOPE_IDENTITY() AS course_id;",
        (course_name,),
    )
    row = cursor.fetchone()
    if row and row.get("course_id") is not None:
        return int(row["course_id"])
    raise DatabaseConnectionError("Failed to retrieve or create course_id")


def get_stage_id(conn: pymssql.Connection, stage_name: str) -> int:
    """Return the stage_id for the given stage_name, creating it if missing."""
    if not stage_name:
        raise ValueError("stage_name is required")
    cursor = conn.cursor()
    cursor.execute("SELECT stage_id FROM stages WHERE stage_name = %s", (stage_name,))
    row = cursor.fetchone()
    if row:
        return int(row["stage_id"])
    cursor.execute(
        "INSERT INTO stages (stage_name) VALUES (%s); SELECT SCOPE_IDENTITY() AS stage_id;",
        (stage_name,),
    )
    row = cursor.fetchone()
    if row and row.get("stage_id") is not None:
        return int(row["stage_id"])
    raise DatabaseConnectionError("Failed to retrieve or create stage_id")


def fetch_course_progress(conn: pymssql.Connection, user_email: str) -> tuple[str, str, datetime] | None:
    """Fetch the current course progress for the given user email."""
    if not user_email:
        raise ValueError("user_email is required")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            sp.user_email,
            c.course_name,
            s.stage_name,
            sp.updated_at
        FROM student_progress sp
        JOIN courses c ON sp.current_course_id = c.course_id
        JOIN stages s ON sp.current_stage_id = s.stage_id
        WHERE sp.user_email = %s
        """,
        (user_email,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return row["course_name"], row["stage_name"], row["updated_at"]


def save_course_progress(conn: pymssql.Connection, user_email: str, course_id: int, stage_id: int) -> datetime:
    """Insert or update student progress and return the timestamp when the record was saved."""
    if not user_email:
        raise ValueError("user_email is required")
    if not course_id or not stage_id:
        raise ValueError("course_id and stage_id are required")

    now = datetime.utcnow()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 AS existe FROM student_progress WHERE user_email = %s", (user_email,))
    exists = cursor.fetchone() is not None
    if exists:
        cursor.execute(
            "UPDATE student_progress SET current_course_id = %s, current_stage_id = %s, updated_at = %s WHERE user_email = %s",
            (course_id, stage_id, now, user_email),
        )
    else:
        cursor.execute(
            "INSERT INTO student_progress (user_email, current_course_id, current_stage_id, updated_at) VALUES (%s, %s, %s, %s)",
            (user_email, course_id, stage_id, now, ),
        )
    conn.commit()
    return now


def _run_query(sql: str) -> str:
    """Núcleo interno: ejecuta el SQL en la base indicada (o en la activa)."""
    if not is_safe_query(sql):
        return json.dumps({
            "error": "Solo se permiten consultas de lectura (SELECT). "
                     "Sentencias de escritura o DDL no están permitidas."
        }, ensure_ascii=False)
    try:
        conn = get_connection(_current_db)
        cursor = conn.cursor()
        _execute(cursor, sql)
        if cursor.description is None:
            conn.close()
            return json.dumps({"mensaje": "Sin filas devueltas."}, ensure_ascii=False)
        result = rows_to_list(cursor)
        conn.close()
        return json.dumps({"base": _current_db, "filas": len(result), "datos": result},
                          ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

