"""
活动状态自动修正

爬虫只爬"待审核 / 报名中 / 进行中"三个 tab,不爬"已结束"。
所以一个进行中的活动结束以后,如果不再被爬虫扫到,DB 里 finish_status 会一直停留在"进行中"。

这里根据 start_time / end_time 把这种过期状态修正过来,
不依赖再次爬取。

转换规则(只向前演进,不会把已结束改回进行中):
  - finish_status ∈ {报名中, 进行中} 且 end_time < 现在     →  已结束
  - finish_status == 报名中 且 start_time ≤ 现在 < end_time  →  进行中

不动 "待审核" 状态(那是平台审核流,跟时间无关)。
"""
import threading
import time as _time
from datetime import datetime
from typing import Dict

from sqlalchemy import text
from sqlalchemy.orm import Session


# 模块级节流:同一进程内最多每 N 秒跑一次
_RECONCILE_MIN_INTERVAL = 60  # 秒
_last_reconcile_ts = 0.0
_lock = threading.Lock()


def reconcile_activity_status(db: Session) -> Dict[str, int]:
    """
    根据 start_time / end_time 修正 finish_status。
    用 SQL UPDATE 一次性更新,不在 Python 里逐行循环,O(transitions) 而不是 O(N)。
    """
    now = datetime.now()

    # 1. 报名中 / 进行中 → 已结束 (end_time 已过)
    r1 = db.execute(
        text(
            """
            UPDATE activities
            SET finish_status = '已结束'
            WHERE end_time IS NOT NULL
              AND end_time < :now
              AND finish_status IN ('报名中', '进行中')
            """
        ),
        {"now": now},
    )

    # 2. 报名中 → 进行中 (start_time 已到,end_time 还没到)
    r2 = db.execute(
        text(
            """
            UPDATE activities
            SET finish_status = '进行中'
            WHERE start_time IS NOT NULL
              AND end_time IS NOT NULL
              AND start_time <= :now
              AND end_time > :now
              AND finish_status = '报名中'
            """
        ),
        {"now": now},
    )

    db.commit()

    return {
        "to_finished": r1.rowcount or 0,
        "to_ongoing": r2.rowcount or 0,
    }


def maybe_reconcile(db: Session) -> Dict[str, int]:
    """
    限频版本: 同一进程内 60 秒最多 reconcile 一次。
    供 public API 在每次列表请求前调用。
    """
    global _last_reconcile_ts
    now = _time.time()

    with _lock:
        if now - _last_reconcile_ts < _RECONCILE_MIN_INTERVAL:
            return {"to_finished": 0, "to_ongoing": 0, "skipped": True}
        _last_reconcile_ts = now

    return reconcile_activity_status(db)
