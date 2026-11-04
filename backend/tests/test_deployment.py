import pytest
from sqlalchemy import create_engine, select, func
from app.database import Base
from app.db_url import database_url
from app.models import Upload, Snapshot
from app import crud
from migrate_sqlite import migrate


def test_postgresql_url_preserves_credentials_and_ssl():
    url = database_url("postgres://user:p%40ss@host/db?sslmode=require&channel_binding=require")
    assert url.drivername == "postgresql+psycopg"
    assert url.password == "p@ss"
    assert url.query["sslmode"] == "require"
    assert url.query["channel_binding"] == "require"
    assert database_url("sqlite:///local.db").drivername == "sqlite"


def test_postgresql_driver_loads_without_connecting():
    engine = create_engine(database_url("postgresql://user:password@localhost/test?sslmode=require"))
    assert engine.dialect.driver == "psycopg"
    engine.dispose()


def test_host_configuration_paths_and_free_plan():
    from pathlib import Path
    import tomllib
    import yaml

    root = Path(__file__).resolve().parents[2]
    netlify = tomllib.loads((root / "netlify.toml").read_text())
    assert (root / netlify["build"]["base"] / "package.json").is_file()
    assert netlify["build"]["publish"] == "dist"
    render = yaml.safe_load((root / "render.yaml").read_text())
    service = render["services"][0]
    assert service["plan"] == "free"
    assert (root / service["rootDir"] / "requirements.txt").is_file()
    assert "$PORT" in service["startCommand"]
    assert not render.get("databases")


def test_migration_preserves_history_and_refuses_nonempty_target(db_session):
    crud.create_upload(db_session, "test.xlsx", [{"loan_id": "A", "days_past_due": 31}])
    target = create_engine("sqlite:///:memory:")
    counts = migrate(db_session.get_bind(), target)
    assert counts == {"users": 0, "uploads": 1, "snapshots": 1}
    with target.connect() as connection:
        assert connection.scalar(select(Snapshot.__table__.c.loan_id)) == "A"
    with pytest.raises(ValueError, match="must be empty"):
        migrate(db_session.get_bind(), target)
    with target.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(Upload)) == 1
