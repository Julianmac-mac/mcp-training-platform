"""Legacy database access layer kept separate from the training-platform MCP flow.

This module is intentionally isolated because it contains example code related to
HR/talent queries that is not part of the published MCP surface.
"""

from __future__ import annotations

import os
from typing import Any

import pymssql
from dotenv import load_dotenv

from db import DatabaseConnectionError, _execute, get_connection, rows_to_list

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class LegacyDatabaseService:
    """Historic service layer for HR/talent-oriented SQL access."""

    def check_connection(self) -> dict[str, str]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            _execute(cursor, "SELECT DB_NAME() AS database_name, @@VERSION AS version")
            row = cursor.fetchone()
            conn.close()
            return {
                "status": "connected",
                "host": os.getenv("DB_HOST", "localhost"),
                "database": row["database_name"] if row else os.getenv("DB_NAME", "HistorialCursos"),
            }
        except Exception as exc:
            raise DatabaseConnectionError(str(exc)) from exc

    def execute_select(self, query: str) -> list[dict]:
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
        except Exception as exc:
            raise DatabaseConnectionError(str(exc)) from exc

    def search_collaborators(self, email: str | None = None) -> list[dict]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            if not email:
                raise DatabaseConnectionError("email is required")
            _execute(cursor, "SELECT TOP 10 nombre, apellido, email FROM Colaboradores WHERE email = %s", (email,))
            rows = rows_to_list(cursor)
            conn.close()
            return rows
        except Exception as exc:
            raise DatabaseConnectionError(str(exc)) from exc

    def get_employee_360(self, colaborador_id: int) -> dict[str, Any]:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            _execute(cursor, "SELECT TOP 1 colaborador_id, nombre, apellido FROM Colaboradores WHERE colaborador_id = %s", (colaborador_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                raise DatabaseConnectionError(f"Collaborator {colaborador_id} not found")
            return {"colaborador_id": row["colaborador_id"], "nombre": row["nombre"], "apellido": row["apellido"]}
        except Exception as exc:
            raise DatabaseConnectionError(str(exc)) from exc
