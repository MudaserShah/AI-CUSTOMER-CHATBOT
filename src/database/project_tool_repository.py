import json
import uuid
from typing import Optional

from psycopg.types.json import Jsonb

from src.database.base_repository import BaseRepository
from src.database.db_utils import handle_db_errors


class ProjectToolRepository(BaseRepository):
    @staticmethod
    def _map_tool(row) -> Optional[dict]:
        if not row:
            return None
        return {
            "id": row[0],
            "project_id": row[1],
            "name": row[2],
            "description": row[3],
            "method": row[4],
            "endpoint_url": row[5],
            "headers": row[6] or {},
            "parameters_schema": row[7] or {},
            "created_at": row[8],
        }

    @handle_db_errors
    def create_tool(
        self,
        project_id: str,
        name: str,
        description: str,
        method: str = "GET",
        endpoint_url: str = "",
        headers: Optional[dict] = None,
        parameters_schema: Optional[dict] = None,
    ) -> dict:
        tool_id = f"tool_{uuid.uuid4().hex[:12]}"
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO project_tools (
                        id, project_id, name, description, method, endpoint_url, headers, parameters_schema
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, project_id, name, description, method, endpoint_url, headers, parameters_schema, created_at;
                    """,
                    (
                        tool_id,
                        project_id,
                        name,
                        description,
                        method.upper(),
                        endpoint_url,
                        Jsonb(headers or {}),
                        Jsonb(parameters_schema or {}),
                    ),
                )
                row = cur.fetchone()
                return self._map_tool(row)

    @handle_db_errors
    def list_tools_for_project(self, project_id: str) -> list[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, name, description, method, endpoint_url, headers, parameters_schema, created_at
                    FROM project_tools
                    WHERE project_id = %s
                    ORDER BY created_at ASC;
                    """,
                    (project_id,),
                )
                rows = cur.fetchall()
                return [self._map_tool(r) for r in rows if r]

    @handle_db_errors
    def get_tool(self, tool_id: str) -> Optional[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, project_id, name, description, method, endpoint_url, headers, parameters_schema, created_at
                    FROM project_tools
                    WHERE id = %s;
                    """,
                    (tool_id,),
                )
                row = cur.fetchone()
                return self._map_tool(row)

    @handle_db_errors
    def delete_tool(self, tool_id: str) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM project_tools
                    WHERE id = %s;
                    """,
                    (tool_id,),
                )
                return cur.rowcount > 0
