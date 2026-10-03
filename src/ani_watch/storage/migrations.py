"""Lightweight schema migration manager."""

from sqlalchemy import Column, Integer, MetaData, Table, insert, select

from ani_watch.storage.models import Base


MIGRATION_VERSION = 1


def upgrade(engine) -> None:
    """Create the current schema and record its version."""
    metadata = MetaData()
    version_table = Table(
        "schema_version",
        metadata,
        Column("version", Integer, primary_key=True),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        current = connection.execute(
            select(version_table.c.version).limit(1)
        ).scalar_one_or_none()

        if current is None:
            Base.metadata.create_all(engine)
            connection.execute(
                insert(version_table).values(version=MIGRATION_VERSION)
            )
        elif current < MIGRATION_VERSION:
            Base.metadata.create_all(engine)
            connection.execute(
                version_table.update().values(
                    version=MIGRATION_VERSION
                )
            )
