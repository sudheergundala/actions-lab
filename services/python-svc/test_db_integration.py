import os

import psycopg
import pytest

DATABASE_URL = os.environ.get("DATABASE_URL")


@pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL not set; needs PostgreSQL")
def test_can_write_and_read_an_order():
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS orders (id serial PRIMARY KEY, sku text NOT NULL)"
        )
        conn.execute("INSERT INTO orders (sku) VALUES (%s)", ("SKU-1",))
        row = conn.execute(
            "SELECT count(*) FROM orders WHERE sku = %s", ("SKU-1",)
        ).fetchone()
    assert row[0] >= 1
