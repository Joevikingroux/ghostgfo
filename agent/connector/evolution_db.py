"""Pastel Evolution MS SQL Server connection.

Uses pyodbc + FreeTDS (Linux) or the native ODBC driver (Windows).
Connection is always opened read-only.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

try:
    import pyodbc
except ImportError:
    pyodbc = None  # type: ignore[assignment]


_DRIVERS_PREFERRED = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "FreeTDS",
    "SQL Server",
]


def _find_driver() -> str:
    if pyodbc is None:
        raise RuntimeError("pyodbc not installed")
    installed = [d for d in pyodbc.drivers()]
    for pref in _DRIVERS_PREFERRED:
        for d in installed:
            if pref.lower() in d.lower():
                return d
    raise RuntimeError(
        f"No compatible ODBC driver found. Installed: {installed}. "
        "Install 'ODBC Driver 17 for SQL Server' or FreeTDS."
    )


def build_connection_string(
    server: str,
    database: str,
    username: str,
    password: str,
    *,
    port: int = 1433,
    timeout: int = 30,
) -> str:
    driver = _find_driver()
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Connect Timeout={timeout};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "ApplicationIntent=ReadOnly;"  # SQL Server 2012+ read-only routing
    )


@contextmanager
def connect(
    server: str,
    database: str,
    username: str,
    password: str,
    **kwargs: Any,
) -> Generator[Any, None, None]:
    """Context manager that yields an open pyodbc Connection."""
    conn_str = build_connection_string(server, database, username, password, **kwargs)
    conn = pyodbc.connect(conn_str, autocommit=False)
    try:
        yield conn
    finally:
        conn.close()


def run_query(conn: Any, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Execute a SELECT and return rows as list of dicts."""
    cursor = conn.cursor()
    cursor.execute(sql, params)
    columns = [col[0] for col in cursor.description]
    rows = []
    for row in cursor.fetchall():
        rows.append(dict(zip(columns, row)))
    cursor.close()
    return rows


def test_connection(server: str, database: str, username: str, password: str) -> bool:
    """Return True if the connection succeeds. Used during --install."""
    try:
        with connect(server, database, username, password) as conn:
            run_query(conn, "SELECT 1 AS ping")
        return True
    except Exception:
        return False
