"""Lightweight schema migration manager."""

import sqlalchemy as sa

from ani_watch.storage.models import Base


MIGRATION_VERSION = 1


def upgrade(engine) -> None:
    """Create the current schema and record its version."""
    metadata = sa.MetaData()
    version_table = sa.Table(
        "schema_version",
        metadata,
        sa.Column("version", sa.Integer, primary_key=True),
    )
    metadata.create_all(engine)

    with engine.begin() as connection:
        current = connection.execute(
            sa.select(version_table.c.version).limit(1)
        ).scalar_one_or_none()

        if current is None:
            Base.metadata.create_all(engine)
            connection.execute(
                sa.insert(version_table).values(version=MIGRATION_VERSION)
            )
        elif current < MIGRATION_VERSION:
            Base.metadata.create_all(engine)
            connection.execute(
                version_table.update().values(
                    version=MIGRATION_VERSION
                )
            )
