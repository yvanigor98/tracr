import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from tracr.config import settings
from tracr.db.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

EXCLUDE_SCHEMAS = {"tiger", "tiger_data", "topology"}
EXCLUDE_TABLES = {
    "spatial_ref_sys", "county_lookup", "countysub_lookup",
    "direction_lookup", "geocode_settings", "geocode_settings_default",
    "loader_lookuptables", "loader_platform", "loader_variables",
    "pagc_gaz", "pagc_lex", "pagc_rules", "place_lookup",
    "secondary_unit_lookup", "state_lookup", "street_type_lookup",
    "tabblock20", "zip_lookup", "zip_lookup_all", "zip_lookup_base",
    "zip_state", "zip_state_loc", "addr", "addrfeat", "bg", "county",
    "cousub", "edges", "faces", "featnames", "place", "state",
    "tabblock", "tract", "zcta5", "layer", "topology",
}


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        if name in EXCLUDE_TABLES:
            return False
        if hasattr(object, "schema") and object.schema in EXCLUDE_SCHEMAS:
            return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
