from typing import Any, List, Optional

from agno.db.postgres import PostgresDb
from agno.utils.log import log_info, log_warning
from sqlalchemy import text
from sqlalchemy.engine import Engine

# Columns agno 2.x sessions table requires that agno 1.x didn't have
_SESSIONS_MIGRATION_COLUMNS = {
    "session_type": "VARCHAR(50)",
    "agent_id": "VARCHAR(64)",
    "team_id": "VARCHAR(64)",
    "workflow_id": "VARCHAR(64)",
    "agent_data": "JSONB",
    "team_data": "JSONB",
    "workflow_data": "JSONB",
    "metadata": "JSONB",
    "runs": "JSONB",
    "summary": "JSONB",
}


class PostgresStorage(PostgresDb):
    """Compatibility wrapper: maps agno 1.x PostgresStorage API to agno 2.x PostgresDb."""

    def __init__(
        self,
        db_url: Optional[str] = None,
        db_engine: Optional[Engine] = None,
        table_name: Optional[str] = None,
        schema: Optional[str] = None,
        mode: Optional[str] = None,
        auto_upgrade_schema: bool = False,
        **kwargs,
    ):
        super().__init__(
            db_url=db_url,
            db_engine=db_engine,
            db_schema=schema,
            session_table=table_name,
            **kwargs,
        )
        self.mode = mode
        self._table_name = table_name
        self._schema = schema or "public"
        self._auto_migrate_sessions_table()

    def _auto_migrate_sessions_table(self) -> None:
        """Add missing agno 2.x columns to an existing agno 1.x sessions table."""
        if not self._table_name:
            return
        try:
            with self.Session() as sess:
                result = sess.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema = :schema AND table_name = :table"
                    ),
                    {"schema": self._schema, "table": self._table_name},
                )
                existing = {row[0] for row in result}

            missing = {col: dtype for col, dtype in _SESSIONS_MIGRATION_COLUMNS.items() if col not in existing}
            if not missing:
                return

            log_warning(f"Auto-migrating sessions table {self._schema}.{self._table_name}: adding {list(missing.keys())}")
            with self.Session() as sess, sess.begin():
                for col, dtype in missing.items():
                    sess.execute(
                        text(f'ALTER TABLE "{self._schema}"."{self._table_name}" ADD COLUMN IF NOT EXISTS "{col}" {dtype}')
                    )
            log_info(f"Sessions table {self._schema}.{self._table_name} migrated to agno 2.x schema")
        except Exception as e:
            log_warning(f"Could not auto-migrate sessions table: {e}")

    def read(self, session_id: str, user_id: Optional[str] = None) -> Optional[Any]:
        return self.get_session(session_id=session_id, user_id=user_id)

    def upsert(self, session: Any) -> Optional[Any]:
        return self.upsert_session(session=session)

    def get_recent_sessions(
        self, limit: Optional[int] = None, user_id: Optional[str] = None
    ) -> List[Any]:
        result = self.get_sessions(user_id=user_id, limit=limit)
        if isinstance(result, tuple):
            return result[0]
        return result or []


class PostgresMemoryDb(PostgresDb):
    """Compatibility wrapper: maps agno 1.x PostgresMemoryDb API to agno 2.x PostgresDb."""

    def __init__(
        self,
        db_url: Optional[str] = None,
        db_engine: Optional[Engine] = None,
        table_name: Optional[str] = None,
        schema: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            db_url=db_url,
            db_engine=db_engine,
            db_schema=schema,
            memory_table=table_name,
            **kwargs,
        )
