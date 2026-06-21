#!/usr/bin/env python
"""Seed local development data.

Inserts a handful of categories and expenses for a dev user so the dashboard
isn't empty. Safe to re-run (upserts by natural key). Requires `make up` and
applied migrations. Intended for local/dev only — never run against prod.

Usage:
    cd services/api && uv run python ../../scripts/seed.py
"""
from __future__ import annotations

# TODO: import the app's session + models once they exist, e.g.
#   from app.db import session_scope
#   from app.models import Category, Expense
#
# DEV_USER_ID is a placeholder until a real Better Auth user id is wired in.

DEV_USER_ID = "dev-user"


def main() -> None:
    print("seed: not yet implemented — wire up app.db + app.models first")


if __name__ == "__main__":
    main()
