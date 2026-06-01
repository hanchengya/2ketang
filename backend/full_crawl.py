#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合爬取脚本 (一次登录跑完整流程)

流程:
  1. 爬取活动列表 (全部 9 个状态 tab), 每条带平台真实状态, 存库
  2. 对"待开始 / 进行中"的活动逐个爬详情 (含 QQ 群识别), 存库
  3. 对"待开始 / 进行中"的活动逐个爬参与者列表 (发放学分 tab), 存库

为什么详情/参与者只跑"待开始/进行中":
  - 已完结(4000+)的详情/参与者基本不再变, 跑全量太慢且无意义
  - 报名中的活动还没开始发学分, 参与者列表通常为空
  - 待开始/进行中才是"快要签到 / 正在进行"需要实时数据的活动

用法 (容器内):
    docker exec 2ketang-backend python /app/full_crawl.py
    # 可选: 限定状态  --status 进行中
    # 可选: 只跑前 N 个  --limit 10
    # 可选: 跳过参与者  --no-participants

注意: 这是脱离 Web 任务管理的独立脚本, 直接写库。
      管理端的"爬虫控制"走的是另一套 (带任务/日志/可停止)。
"""
import sys
import time
import argparse
from datetime import datetime

sys.path.insert(0, "/app")
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.crawlers.login import login
from app.crawlers.activity_crawler import crawl_all_tabs, ACTIVITY_TABS
from app.crawlers.detail_crawler import crawl_activity_detail
from app.crawlers.participant_crawler import crawl_activity_participants
from app.services.crawler_service import CrawlerService


# 第 2、3 步只处理这些状态的活动
ACTIVE_STATUSES = {"待开始", "进行中"}


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", default="", help="只爬某个状态 (默认: 待开始+进行中)")
    parser.add_argument("--limit", type=int, default=0, help="详情/参与者最多处理前 N 个 (0=不限)")
    parser.add_argument("--no-participants", action="store_true", help="跳过参与者爬取")
    parser.add_argument("--no-details", action="store_true", help="跳过详情爬取")
    args = parser.parse_args()

    target_statuses = {args.status} if args.status else set(ACTIVE_STATUSES)

    db = SessionLocal()
    svc = CrawlerService(db)
    driver = None

    log("=" * 56)
    log("综合爬取开始")
    log(f"详情/参与者目标状态: {sorted(target_statuses)}")
    log("=" * 56)

    try:
        # ---------- 登录 ----------
        log("登录第二课堂...")
        driver = login()
        if not driver:
            log("登录失败, 退出")
            return 1
        svc.driver = driver
        log("登录成功")

        # ========== 第 1 步: 活动列表 (全部 tab) ==========
        log("\n[1/3] 爬取活动列表 (全部状态 tab)...")
        grouped = crawl_all_tabs(driver)
        svc._save_activities_to_db(grouped)

        # 收集"目标状态"的活动 ID
        active_ids = []
        for status, acts in grouped.items():
            if status in target_statuses:
                for a in acts:
                    aid = a.get("actId") or a.get("act_id")
                    if aid:
                        active_ids.append(aid)
        active_ids = list(dict.fromkeys(active_ids))  # 去重保序

        if args.limit > 0:
            active_ids = active_ids[: args.limit]

        log(f"\n目标活动 ({sorted(target_statuses)}): {len(active_ids)} 个")
        log(f"  IDs: {active_ids}")

        # ========== 第 2 步: 活动详情 (含 QQ 群) ==========
        if args.no_details:
            log("\n[2/3] 跳过详情爬取 (--no-details)")
        else:
            log(f"\n[2/3] 爬取 {len(active_ids)} 个活动详情 (含 QQ 群识别)...")
            details = []
            for i, aid in enumerate(active_ids, 1):
                log(f"  [{i}/{len(active_ids)}] 详情 {aid}")
                try:
                    d = crawl_activity_detail(driver, aid)
                    if d:
                        if d.get("qq_groups"):
                            log(f"      QQ群: {d.get('qq_groups')}")
                        details.append(d)
                except Exception as e:
                    log(f"      详情 {aid} 失败: {e}")
                time.sleep(2)
            if details:
                svc._save_activity_details_to_db(details)

        # ========== 第 3 步: 参与者 (仅待开始/进行中) ==========
        if args.no_participants:
            log("\n[3/3] 跳过参与者爬取 (--no-participants)")
        else:
            log(f"\n[3/3] 爬取 {len(active_ids)} 个活动的参与者...")
            results = []
            for i, aid in enumerate(active_ids, 1):
                log(f"  [{i}/{len(active_ids)}] 参与者 {aid}")
                try:
                    r = crawl_activity_participants(driver, aid)
                    if r:
                        n = len(r.get("participants", []))
                        log(f"      参与者 {n} 人")
                        results.append(r)
                except Exception as e:
                    log(f"      参与者 {aid} 失败: {e}")
                time.sleep(2)
            if results:
                svc._save_participants_to_db(results)

        log("\n" + "=" * 56)
        log("综合爬取完成")
        log("=" * 56)
        return 0

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        db.close()


if __name__ == "__main__":
    sys.exit(main())
