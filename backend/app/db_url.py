"""Select the installed PostgreSQL driver without altering URL credentials."""
from sqlalchemy.engine import make_url


def database_url(value):
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://"):]
    url = make_url(value)
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg")
    return url
