"""Lightweight schema migration manager.

For a fresh database this creates the current SQLAlchemy schema. A version
table makes migration progress explicit without coupling the application to a
specific database server.
"""

from sqlalchemy import Integer, MetaData, Table, insert, select

from ani_watch.storage.models import Base


MIGRATION_VERSION = 1


def upgrade(engine) -> None:
    """Apply the current schema and record its version."""
    version_table = Table(
        "schema_version",
        MetaData(),
        # The version table is deliberately defined independently so this
        # routine works before the rest of the schema exists.
        __import__("sqlalchemy").Column("version", Integer, primary_key=True),
    )
    version_table.metadata.create_all(engine)

    with engine.begin() as connection:
        current = connection.execute(select(version_table.c.version).limit(1)).scalar_one_or_none()
        if current is None:
            Base.metadata.create_all(engine)
            connection.execute(insert(version_table).values(version=MIGRATION_VERSION))
        elif current < MIGRATION_VERSION:
            Base.metadata.create_all(engine)
            connection.execute(
                version_table.update().values(version=MIGRATION_VERSION)
            )
