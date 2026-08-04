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


def _execute(cursor: pymssql.Cursor, sql: str) -> None:
    cursor.execute(sanitizar_y_limitar_query(sql))


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


class DatabaseService:
    """Service layer for read-only SQL Server access."""

    def check_connection(self) -> dict[str, str]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            _execute(cursor, "SELECT DB_NAME() AS database_name, @@VERSION AS version")
            row = cursor.fetchone()
            conn.close()
            return {
                "status": "connected",
                "host": DB_HOST,
                "database": row["database_name"] if row else _current_db,
            }
        except Exception as exc:
            raise DatabaseConnectionError(str(exc)) from exc

    def list_tables(self) -> list[str]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            _execute(
                cursor,
                "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_SCHEMA, TABLE_NAME",
            )
            rows = cursor.fetchall()[:100]
            conn.close()
            return [f"{row['TABLE_SCHEMA']}.{row['TABLE_NAME']}" for row in rows]
        except Exception as exc:
            raise DatabaseConnectionError(str(exc)) from exc

    def execute_select(self, query: str) -> list[dict]:
        if not is_safe_query(query):
            raise DatabaseConnectionError(
                "Only read-only queries (SELECT) are allowed."
            )
        try:
            conn = get_connection()
            cursor = conn.cursor()
            _execute(cursor, query)
            if cursor.description is None:
                conn.close()
                return []
            rows = rows_to_list(cursor)
            conn.close()
            return rows
        except DatabaseConnectionError:
            raise
        except Exception as exc:
            raise DatabaseConnectionError(str(exc)) from exc

    def search_collaborators(
        self,
        email: str | None = None,
        nombre_busqueda: str | None = None,
        apellido_busqueda: str | None = None,
    ) -> list[dict]:
        """Search for collaborators by email, first name, and/or last name."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Build WHERE clause dynamically
            where_parts = []
            if email:
                email_safe = email.replace("'", "''")
                where_parts.append(f"c.email = '{email_safe}'")
            if nombre_busqueda:
                search_term = nombre_busqueda.replace("'", "''")
                where_parts.append(f"c.nombre LIKE '%{search_term}%'")
            if apellido_busqueda:
                search_term = apellido_busqueda.replace("'", "''")
                where_parts.append(f"c.apellido LIKE '%{search_term}%'")
            
            if not where_parts:
                conn.close()
                raise DatabaseConnectionError(
                    "Must provide email, nombre_busqueda, and/or apellido_busqueda"
                )
            
            where_clause = " AND ".join(where_parts)
            
            sql = f"""
            SELECT 
                c.colaborador_id, 
                c.nombre, 
                c.apellido, 
                c.email,
                COALESCE(r.nombre_rol, 'N/A') AS nombre_rol,
                COALESCE(e.nombre_equipo, 'N/A') AS nombre_equipo
            FROM Colaboradores c
            LEFT JOIN Roles r ON c.rol_id = r.rol_id
            LEFT JOIN Equipos e ON c.equipo_id = e.equipo_id
            WHERE {where_clause}
            ORDER BY c.nombre, c.apellido
            """
            
            _execute(cursor, sql)
            rows = rows_to_list(cursor)
            conn.close()
            return rows
        except Exception as exc:
            raise DatabaseConnectionError(f"Search failed: {str(exc)}") from exc

    def get_employee_360(self, colaborador_id: int) -> dict[str, Any]:
        """Retrieve complete 360 view for a single collaborator."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            sql = f"""
            SELECT 
                c.colaborador_id, 
                c.nombre, 
                c.apellido, 
                c.email,
                COALESCE(r.nombre_rol, 'N/A') AS nombre_rol,
                COALESCE(s.nivel_seniority, 'N/A') AS nivel_seniority,
                COALESCE(e.nombre_equipo, 'N/A') AS nombre_equipo,
                COALESCE(l.nombre + ' ' + l.apellido, 'N/A') AS lider_directo,
                COALESCE(g.nombre + ' ' + g.apellido, 'N/A') AS gerente_area
            FROM Colaboradores c
            LEFT JOIN Roles r ON c.rol_id = r.rol_id
            LEFT JOIN Seniorities s ON c.seniority_id = s.seniority_id
            LEFT JOIN Equipos e ON c.equipo_id = e.equipo_id
            LEFT JOIN Colaboradores l ON e.lider_id = l.colaborador_id
            LEFT JOIN Colaboradores g ON e.gerente_id = g.colaborador_id
            WHERE c.colaborador_id = {colaborador_id}
            """
            
            _execute(cursor, sql)
            row = cursor.fetchone()
            if not row:
                conn.close()
                raise DatabaseConnectionError(f"Collaborator {colaborador_id} not found")
            
            result = dict(row)
            
            # Get skills
            _execute(cursor,f"""
            SELECT 
                sk.nombre_tecnologia,
                cs.nivel_experiencia
            FROM Colaborador_Skills cs
            INNER JOIN Skills sk ON cs.skill_id = sk.skill_id
            WHERE cs.colaborador_id = {colaborador_id}
            ORDER BY sk.nombre_tecnologia
            """)
            skills_rows = rows_to_list(cursor)
            result["habilidades"] = [
                f"{s['nombre_tecnologia']} (Nivel: {s['nivel_experiencia']})" 
                for s in skills_rows
            ] if skills_rows else []
            
            # Get courses
            _execute(cursor,f"""
            SELECT 
                cc.nombre_curso,
                ch.fecha_inicio
            FROM Colaborador_Cursos ch
            INNER JOIN Cursos_Capacitaciones cc ON ch.curso_id = cc.curso_id
            WHERE ch.colaborador_id = {colaborador_id}
            ORDER BY ch.fecha_inicio DESC
            """)
            courses_rows = rows_to_list(cursor)
            result["historial_cursos"] = [
                f"{c['nombre_curso']} [Inicio: {c['fecha_inicio']}]" 
                for c in courses_rows
            ] if courses_rows else []

            _execute(cursor,f"""
            SELECT CASE
                WHEN EXISTS (
                    SELECT 1 FROM Asignaciones_Tareas a
                    WHERE a.colaborador_id = {colaborador_id} AND a.en_desarrollo = 1
                ) THEN 0 ELSE 1 END AS disponible
            """)
            disponible_row = cursor.fetchone()
            result["disponible"] = bool(disponible_row["disponible"]) if disponible_row else True

            _execute(cursor,f"""
            SELECT
                a.asignacion_id,
                p.descripcion AS proyecto,
                pr.descripcion AS prioridad,
                sk.nombre_tecnologia AS tecnologia,
                a.horas,
                a.fecha_inicio,
                a.en_desarrollo
            FROM Asignaciones_Tareas a
            INNER JOIN Proyectos p ON a.proyecto_id = p.proyecto_id
            INNER JOIN Prioridades pr ON a.prioridad_id = pr.prioridad_id
            INNER JOIN Skills sk ON a.tecnologia_id = sk.skill_id
            WHERE a.colaborador_id = {colaborador_id}
              AND a.fecha_vencimiento IS NULL
            ORDER BY a.fecha_inicio DESC
            """)
            result["tareas_sin_fecha_vencimiento"] = rows_to_list(cursor)
            
            conn.close()
            return result
        except Exception as exc:
            raise DatabaseConnectionError(f"360 view retrieval failed: {str(exc)}") from exc

    @staticmethod
    def _row_to_persona(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "nombre": row["nombre"],
            "apellido": row["apellido"],
            "mail": row["email"],
            "rol": row.get("nombre_rol") or "N/A",
            "seniority": row.get("nivel_seniority") or "N/A",
        }

    @staticmethod
    def _row_to_contacto(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "nombre": row["nombre"],
            "apellido": row["apellido"],
            "email": row["email"],
        }

    def _fetch_colaborador_contacto(
        self, cursor: pymssql.Cursor, colaborador_id: int | None
    ) -> dict[str, Any] | None:
        if colaborador_id is None:
            return None
        _execute(cursor,
            f"""
            SELECT c.nombre, c.apellido, c.email
            FROM Colaboradores c
            WHERE c.colaborador_id = {colaborador_id}
            """
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_contacto(dict(row))

    def get_team_consolidated_metrics(self, nombre_equipo: str) -> dict[str, Any] | None:
        """Return team roster, leadership, referents, and total sprint hours."""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            equipo_safe = nombre_equipo.replace("'", "''")

            _execute(cursor,
                f"""
                SELECT equipo_id, nombre_equipo, lider_id, gerente_id
                FROM Equipos
                WHERE nombre_equipo = '{equipo_safe}'
                """
            )
            equipo = cursor.fetchone()
            if not equipo:
                conn.close()
                return None

            equipo_id = equipo["equipo_id"]

            _execute(cursor,
                f"""
                SELECT
                    c.nombre,
                    c.apellido,
                    c.email,
                    COALESCE(r.nombre_rol, 'N/A') AS nombre_rol,
                    COALESCE(s.nivel_seniority, 'N/A') AS nivel_seniority
                FROM Colaboradores c
                LEFT JOIN Roles r ON c.rol_id = r.rol_id
                LEFT JOIN Seniorities s ON c.seniority_id = s.seniority_id
                WHERE c.equipo_id = {equipo_id}
                ORDER BY c.nombre, c.apellido
                """
            )
            miembros = [
                self._row_to_persona(dict(row))
                for row in rows_to_list(cursor)
            ]

            _execute(cursor,
                f"""
                SELECT c.nombre, c.apellido, c.email
                FROM Referentes ref
                INNER JOIN Colaboradores c ON ref.colaborador_id = c.colaborador_id
                WHERE ref.equipo_id = {equipo_id}
                ORDER BY c.nombre, c.apellido
                """
            )
            referentes = [
                self._row_to_contacto(dict(row))
                for row in rows_to_list(cursor)
            ]

            lider = self._fetch_colaborador_contacto(cursor, equipo["lider_id"])
            gerente = self._fetch_colaborador_contacto(cursor, equipo["gerente_id"])

            conn.close()
            return {
                "nombre": equipo["nombre_equipo"],
                "miembros": miembros,
                "referentes": referentes,
                "lider": lider,
                "gerente": gerente,
            }
        except Exception as exc:
            raise DatabaseConnectionError(
                f"Team consolidated metrics retrieval failed: {str(exc)}"
            ) from exc

    def search_talent_by_technology(self, nombre_tecnologia: str) -> list[dict]:
            """Find collaborators with a given skill, knowledge origin, and availability."""
            try:
                conn = get_connection()
                cursor = conn.cursor()
                tech_safe = nombre_tecnologia.replace("'", "''")

                sql = f"""
                SELECT
                    c.nombre, c.apellido, c.email, cs.nivel_experiencia,
                    CASE WHEN cs.adquirido_finnegans = 1 THEN 'Capacitación Interna'
                        ELSE 'Experiencia Previa' END AS origen_conocimiento,
                    ISNULL(CAST(a.fecha_vencimiento AS VARCHAR), 'Disponible de Inmediato')
                        AS proxima_liberacion
                FROM Colaboradores c
                INNER JOIN Colaborador_Skills cs ON c.colaborador_id = cs.colaborador_id
                INNER JOIN Skills sk ON cs.skill_id = sk.skill_id
                LEFT JOIN Asignaciones_Tareas a
                    ON c.colaborador_id = a.colaborador_id AND a.en_desarrollo = 1
                WHERE sk.nombre_tecnologia = '{tech_safe}'
                ORDER BY c.apellido, c.nombre
                """

                _execute(cursor, sql)
                rows = rows_to_list(cursor)
                conn.close()
                return rows
            except Exception as exc:
                raise DatabaseConnectionError(
                    f"Talent search failed: {str(exc)}"
                ) from exc

    def get_skills_catalog_and_training_gaps(self) -> dict[str, list[dict]]:
        """Return master skills dictionary and uncertified course gaps."""
        try:
            conn = get_connection()
            cursor = conn.cursor()

            _execute(cursor,
                """
                SELECT skill_id, nombre_tecnologia, categoria, tipo
                FROM Skills
                ORDER BY nombre_tecnologia
                """
            )
            diccionario_maestro = rows_to_list(cursor)

            _execute(cursor,
                """
                SELECT
                    c.nombre + ' ' + c.apellido AS colaborador,
                    cc.nombre_curso,
                    ch.fecha_inicio
                FROM Colaborador_Cursos ch
                INNER JOIN Cursos_Capacitaciones cc ON ch.curso_id = cc.curso_id
                INNER JOIN Colaboradores c ON ch.colaborador_id = c.colaborador_id
                WHERE ch.fecha_certificacion IS NULL
                ORDER BY ch.fecha_inicio DESC
                """
            )
            gaps_capacitacion = rows_to_list(cursor)
            conn.close()
            return {
                "diccionario_maestro": diccionario_maestro,
                "gaps_capacitacion": gaps_capacitacion,
            }
        except Exception as exc:
            raise DatabaseConnectionError(
                f"Skills catalog and training gaps retrieval failed: {str(exc)}"
            ) from exc

