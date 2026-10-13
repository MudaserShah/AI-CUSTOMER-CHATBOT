import uuid
from typing import Optional

from src.database.base_repository import BaseRepository
from src.database.db_utils import handle_db_errors


class ProjectRepository(BaseRepository):
    @staticmethod
    def _map_project(row) -> Optional[dict]:
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "slug": row[2],
            "api_key": row[3],
            "system_prompt": row[4],
            "llm_model": row[5],
            "widget_title": row[6],
            "widget_greeting": row[7],
            "primary_color": row[8],
            "created_at": row[9],
        }

    @handle_db_errors
    def get_project(self, project_id: str) -> Optional[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, slug, api_key, system_prompt, llm_model,
                           widget_title, widget_greeting, primary_color, created_at
                    FROM projects
                    WHERE id = %s;
                    """,
                    (project_id,),
                )
                row = cur.fetchone()
                return self._map_project(row)

    @handle_db_errors
    def get_project_by_api_key(self, api_key: str) -> Optional[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, slug, api_key, system_prompt, llm_model,
                           widget_title, widget_greeting, primary_color, created_at
                    FROM projects
                    WHERE api_key = %s;
                    """,
                    (api_key,),
                )
                row = cur.fetchone()
                return self._map_project(row)

    @handle_db_errors
    def get_project_by_slug(self, slug: str) -> Optional[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, slug, api_key, system_prompt, llm_model,
                           widget_title, widget_greeting, primary_color, created_at
                    FROM projects
                    WHERE slug = %s;
                    """,
                    (slug,),
                )
                row = cur.fetchone()
                return self._map_project(row)

    @handle_db_errors
    def create_project(
        self,
        name: str,
        slug: str,
        project_id: Optional[str] = None,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        llm_model: Optional[str] = None,
        widget_title: str = "AI Support Assistant",
        widget_greeting: str = "Hello! How can I help you today?",
        primary_color: str = "#2563eb",
    ) -> dict:
        if not project_id:
            project_id = f"proj_{uuid.uuid4().hex[:12]}"
        if not api_key:
            api_key = f"pk_live_{uuid.uuid4().hex}"

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO projects (
                        id, name, slug, api_key, system_prompt, llm_model,
                        widget_title, widget_greeting, primary_color
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, name, slug, api_key, system_prompt, llm_model,
                              widget_title, widget_greeting, primary_color, created_at;
                    """,
                    (
                        project_id,
                        name,
                        slug,
                        api_key,
                        system_prompt,
                        llm_model,
                        widget_title,
                        widget_greeting,
                        primary_color,
                    ),
                )
                row = cur.fetchone()
                return self._map_project(row)

    @handle_db_errors
    def list_projects(self) -> list[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, slug, api_key, system_prompt, llm_model,
                           widget_title, widget_greeting, primary_color, created_at
                    FROM projects
                    ORDER BY created_at ASC;
                    """
                )
                rows = cur.fetchall()
                return [self._map_project(r) for r in rows if r]

    @handle_db_errors
    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        llm_model: Optional[str] = None,
        widget_title: Optional[str] = None,
        widget_greeting: Optional[str] = None,
        primary_color: Optional[str] = None,
    ) -> Optional[dict]:
        updates = []
        params = []
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if system_prompt is not None:
            updates.append("system_prompt = %s")
            params.append(system_prompt)
        if llm_model is not None:
            updates.append("llm_model = %s")
            params.append(llm_model)
        if widget_title is not None:
            updates.append("widget_title = %s")
            params.append(widget_title)
        if widget_greeting is not None:
            updates.append("widget_greeting = %s")
            params.append(widget_greeting)
        if primary_color is not None:
            updates.append("primary_color = %s")
            params.append(primary_color)

        if not updates:
            return self.get_project(project_id)

        params.append(project_id)
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE projects
                    SET {", ".join(updates)}
                    WHERE id = %s
                    RETURNING id, name, slug, api_key, system_prompt, llm_model,
                              widget_title, widget_greeting, primary_color, created_at;
                    """,
                    tuple(params),
                )
                row = cur.fetchone()
                return self._map_project(row)
