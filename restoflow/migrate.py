from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.engine import Engine

from restoflow import models  # noqa: F401
from restoflow.database import Base, engine

_CONSTANT_DEFAULTS = {
    "integer": "0", "small_integer": "0", "big_integer": "0",
    "float": "0", "numeric": "0", "real": "0", "boolean": "0",
    "datetime": "'2000-01-01 00:00:00'", "date": "'2000-01-01'",
    "time": "'00:00:00'",
}


def _default_ddl(col) -> str:
    kind = col.type.__visit_name__.lower()
    if kind in ("varchar", "string", "text"):
        return "DEFAULT ''"
    return f"DEFAULT {_CONSTANT_DEFAULTS.get(kind, '0')}"


def ensure_schema(eng: Engine = engine) -> list[str]:
    applied: list[str] = []
    inspector = sa_inspect(eng)
    tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in tables:
            table.create(eng)
            applied.append(f"CREATE {table.name}")
            continue
        have = {c["name"] for c in inspector.get_columns(table.name)}
        for col in table.columns:
            if col.name in have:
                continue
            ddl = [f'ALTER TABLE "{table.name}"',
                   f'ADD COLUMN "{col.name}"',
                   col.type.compile(eng.dialect)]
            if col.nullable:
                ddl.append("NULL")
            else:
                ddl.append("NOT NULL")
                ddl.append(_default_ddl(col))
            with eng.begin() as conn:
                conn.execute(text(" ".join(ddl)))
            applied.append(f"ADD {table.name}.{col.name}")
    return applied


if __name__ == "__main__":
    changes = ensure_schema()
    print("✅ Миграции:", changes or "не требуются")