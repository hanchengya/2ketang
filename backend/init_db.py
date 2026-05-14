#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
容器启动时执行:
  1. 等 MySQL 可达
  2. 调用 SQLAlchemy Base.metadata.create_all 建出所有表
  3. 确保默认管理员账号 admin/admin123 存在

幂等:已存在的表/用户会跳过,可以反复运行。
"""
import sys
import time

import bcrypt
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

# 导入所有 model,让 Base.metadata 收齐表结构
from app.database import Base, engine, SessionLocal
from app.models import (  # noqa: F401
    Student,
    Activity,
    ActivityDetail,
    ActivityNotification,
    ActivityParticipant,
    EmailLog,
    User,
    CrawlerLog,
)


def wait_for_mysql(max_retry: int = 60, delay: int = 2) -> bool:
    """轮询等 MySQL 准备好"""
    for attempt in range(1, max_retry + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[init_db] MySQL ready (attempt {attempt})")
            return True
        except OperationalError:
            print(f"[init_db] Waiting for MySQL... ({attempt}/{max_retry})")
            time.sleep(delay)
    return False


def ensure_admin_user() -> None:
    """确保默认管理员存在(admin/admin123)"""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print(f"[init_db] admin user exists (id={existing.id}), skip")
            return

        pwd_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
        admin = User(
            username="admin",
            password_hash=pwd_hash,
            email="admin@2ketang.local",
            role="admin",
            is_active=1,
        )
        db.add(admin)
        db.commit()
        print("[init_db] default admin created: admin / admin123")
    finally:
        db.close()


def main() -> None:
    if not wait_for_mysql():
        print("[init_db] FATAL: MySQL not ready after retries")
        sys.exit(1)

    print("[init_db] creating tables (idempotent)...")
    Base.metadata.create_all(bind=engine)
    print("[init_db] tables ready")

    ensure_admin_user()

    print("[init_db] DONE")


if __name__ == "__main__":
    main()
