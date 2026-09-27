---
name: data-access
description: "Use when the task needs data out of the platform database: counts, lookups, reports. Do not use for editing data, which is never permitted."
---

# Reading platform data

## When to use

A question whose answer lives in a table you were granted.

## How

1. `list_tables` first. The list is the whole of your access; a table absent from it does not exist for you.
2. `describe_table` before writing SQL. Guessing a column name costs a round trip.
3. `query_database` with an explicit column list and a LIMIT. `SELECT *` on an unfamiliar table is how a context window is wasted.

## Refusals

A denied table means the grant does not cover it. Say so plainly and name the table; do not try a synonym, a view or a join that reaches it sideways.
