
from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
OUT = BASE / "reference-td1.csv"

@dataclass(frozen=True)
class Case:
    id: str
    start: str | None = None
    end: str | None = None
    age_on: str | None = None
    age_at_order: bool = False
    products: tuple[str, ...] = ()

CASES = [
    Case("C01", "2026-03-01 00:00:00", "2026-06-01 00:00:00"),
    Case("C02", age_on="2026-09-25"),
    Case("C03", "2026-01-01 00:00:00", "2026-07-01 00:00:00", products=("a", "b", "c")),
    Case("C04", "2026-01-01 00:00:00", "2026-10-01 00:00:00"),
    Case("C05", "2026-06-01 00:00:00", "2026-06-02 00:00:00"),
    Case("C06", "2025-01-01 00:00:00", "2026-01-01 00:00:00"),
    Case("C07", "2026-05-31 00:00:00", "2026-06-01 00:00:00"),
    Case("C08", age_on="2026-09-24"),
    Case("C09", age_on="2026-09-26"),
    Case("C10", age_at_order=True),
    Case("C11", age_on="2026-12-01"),
    Case("C12", products=("a", "b", "c")),
    Case("C13", "2026-04-01 00:00:00", "2026-05-01 00:00:00", products=("a", "c")),
    Case("C14", "2026-10-01 00:00:00", "2026-12-01 00:00:00", products=("a", "b", "c")),
    Case("C15", "2026-03-01 00:00:00", "2026-06-01 00:00:00", age_on="2026-09-25"),
    Case("C16", age_on="2026-09-25", products=("a", "b", "c")),
    Case("C17", "2026-01-01 00:00:00", "2026-07-01 00:00:00", age_on="2026-09-25", products=("a", "b", "c")),
    Case("C18", "2026-05-01 00:00:00", "2026-06-01 00:00:00", age_at_order=True),
    Case("C19", "2026-09-01 00:00:00", "2026-10-01 00:00:00", age_on="2026-09-25", products=("d",)),
    Case("C20", "2026-06-01 00:00:00", "2026-09-01 00:00:00"),
]

def sql_for(c: Case) -> str:
    # Une seule requête SELECT, une seule colonne, une seule ligne.
    clauses: list[str] = []
    if c.start:
        clauses.append(f"o.date >= '{c.start}'")
    if c.end:
        clauses.append(f"o.date < '{c.end}'")
    if c.products:
        clauses.append("o.product_id IN (" + ", ".join("'" + p + "'" for p in c.products) + ")")
    if c.age_on:
        yr = f"CAST(strftime('%Y', '{c.age_on}') AS INTEGER)"
        by = "CAST(strftime('%Y', c.birth_date) AS INTEGER)"
        before_birthday = f"(strftime('%m-%d', '{c.age_on}') < strftime('%m-%d', c.birth_date))"
        clauses.append(f"({yr} - {by} - {before_birthday}) = 25")
    if c.age_at_order:
        yr = "CAST(strftime('%Y', o.date) AS INTEGER)"
        by = "CAST(strftime('%Y', c.birth_date) AS INTEGER)"
        before_birthday = "(strftime('%m-%d', o.date) < strftime('%m-%d', c.birth_date))"
        clauses.append(f"({yr} - {by} - {before_birthday}) = 25")
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return ("SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents "
            "FROM orders AS o JOIN product AS p ON p.product_id = o.product_id "
            "JOIN customers AS c ON c.customer_id = o.customer_id" + where + ";")

def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def completed_age(born: date, ref: date) -> int:
    return ref.year - born.year - ((ref.month, ref.day) < (born.month, born.day))

def independently_from_csv(c: Case, orders, prices, births) -> int:
    money = 0
    start = datetime.fromisoformat(c.start) if c.start else None
    end = datetime.fromisoformat(c.end) if c.end else None
    age_reference = date.fromisoformat(c.age_on) if c.age_on else None
    for row in orders:
        placed = datetime.fromisoformat(row["date"])
        if start is not None and placed < start:
            continue
        if end is not None and placed >= end:
            continue
        if c.products and row["product_id"] not in c.products:
            continue
        born = births[row["customer_id"]]
        if age_reference is not None and completed_age(born, age_reference) != 25:
            continue
        if c.age_at_order and completed_age(born, placed.date()) != 25:
            continue
        money += int(row["quantity_product"]) * prices[row["product_id"]]
    return money

def main():
    prices = {r["product_id"]: int(r["price"]) for r in read_csv("product.csv")}
    births = {r["customer_id"]: date.fromisoformat(r["birth_date"]) for r in read_csv("customers.csv")}
    orders = read_csv("orders.csv")
    # Lecture seule, aucune modification de la base distribuée.
    db_uri = (DATA / "boutique.sqlite").resolve().as_uri() + "?mode=ro"
    records = []
    with sqlite3.connect(db_uri, uri=True) as con:
        con.execute("PRAGMA query_only = 1")
        for c in CASES:
            sql = sql_for(c)
            query_rows = con.execute(sql).fetchall()
            if len(query_rows) != 1 or len(query_rows[0]) != 1:
                raise RuntimeError(f"{c.id} does not return exactly one scalar")
            value = query_rows[0][0]
            control = independently_from_csv(c, orders, prices, births)
            if not isinstance(value, int) or value != control:
                raise AssertionError(f"{c.id} mismatch: sqlite={value}; CSV={control}")
            print(f"{c.id}  SQL={value:>8} cents   CSV={control:>8} cents   OK")
            records.append({"case_id": c.id, "sql": sql, "revenue_cents": value})
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "sql", "revenue_cents"])
        writer.writeheader()
        writer.writerows(records)
    print(f"\n20/20 vérifications SQL/CSV réussies. Fichier : {OUT}")

if __name__ == "__main__":
    main()
