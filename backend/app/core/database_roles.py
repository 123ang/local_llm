import re
from contextlib import asynccontextmanager

from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine


DATABASE_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def quote_database_identifier(identifier: str) -> str:
    if not DATABASE_IDENTIFIER_RE.fullmatch(identifier):
        raise ValueError("Unsafe PostgreSQL identifier")
    return f'"{identifier}"'


def dataset_role_statements(
    table_name: str,
    importer_role: str = settings.DATASET_IMPORT_DB_ROLE,
    reader_role: str = settings.TEXT_TO_SQL_DB_ROLE,
) -> tuple[str, str]:
    return (
        f"SET LOCAL ROLE {quote_database_identifier(importer_role)}",
        (
            f"GRANT SELECT ON TABLE {quote_database_identifier(table_name)} "
            f"TO {quote_database_identifier(reader_role)}"
        ),
    )


@asynccontextmanager
async def dataset_write_transaction():
    async with engine.begin() as connection:
        set_role_sql = (
            f"SET LOCAL ROLE "
            f"{quote_database_identifier(settings.DATASET_IMPORT_DB_ROLE)}"
        )
        await connection.execute(text(set_role_sql))
        yield connection


async def grant_text_to_sql_select(connection, table_name: str) -> None:
    _, grant_sql = dataset_role_statements(table_name)
    await connection.execute(text(grant_sql))
