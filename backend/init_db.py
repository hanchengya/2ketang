#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
容器启动:等 MySQL ready → create_all → 确保 admin/admin123 存在
"""
import sys
import time

import bcrypt
from sqlalchemy import text

from app.database import Base, engine, SessionLocal
from app.models import (  # noqa: F401
    Student, Activity, ActivityDetail,
    ActivityNotification, ActivityParticipant, EmailLog,
    User, CrawlerLog,
)


def wait_for_mysql(max_retry=60, delay=2):
    last_err = None
    for attempt in range(1, max_retry + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[init_db] MySQL ready (attempt {attempt})", flush=True)
            return True
        except Exception as e:
            last_err = e
            print(f"[init_db] Waiting for MySQL... ({attempt}/{max_retry}): {type(e).__name__}: {str(e)[:140]}", flush=True)
            time.sleep(delay)
    print(f"[init_db] FATAL: last error: {last_err}", flush=True)
    return False


def ensure_admin_user():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print(f"[init_db] admin user exists (id={existing.id})", flush=True)
            return
        pwd_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
        admin = User(username="admin", password_hash=pwd_hash,
                     email="admin@2ketang.local", role="admin", is_active=1)
        db.add(admin)
        db.commit()
        print("[init_db] default admin created: admin / admin123", flush=True)
    finally:
        db.close()


def main():
    if not wait_for_mysql():
        sys.exit(1)
    print("[init_db] creating tables...", flush=True)
    Base.metadata.create_all(bind=engine)
    print("[init_db] tables ready", flush=True)
    ensure_admin_user()
    print("[init_db] DONE", flush=True)


if __name__ == "__main__":
    main()
