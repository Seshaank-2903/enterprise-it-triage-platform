import os
import sys
from logging.config import fileConfig

# Ensure backend directory is in Python sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

from app.models.models import Base
from app.core.config import settings

# Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata

# Standard SQLAlchemy naming convention for constraint naming in batch mode (SQLite / Postgres)
if not target_metadata.naming_convention:
    target_metadata.naming_convention = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

# Escape '%' characters in database URL to prevent ConfigParser interpolation errors
escaped_db_url = settings.DATABASE_URL.replace("%", "%%")
config.set_main_option("sqlalchemy.url", escaped_db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine.
    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    is_sqlite = url.startswith("sqlite")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=is_sqlite,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Executes migrations using an established connection."""
    is_sqlite = connection.dialect.name == "sqlite"

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=is_sqlite,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Handles connection reuse when invoked programmatically (e.g. in tests)
    or initializes an engine safely with dialect-specific options.
    """
    # 1. Reuse existing connection if passed in configuration attributes (e.g., test suites)
    provided_connection = config.attributes.get("connection", None)
    if provided_connection is not None:
        do_run_migrations(provided_connection)
        return

    # 2. Extract configuration section safely
    section = config.get_section(config.config_ini_section)
    if section is None:
        section = {}

    connect_args = {}
    if "sqlite" in settings.DATABASE_URL:
        connect_args["check_same_thread"] = False

    # 3. Create engine with thread-safety and connection pooling fallback
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
