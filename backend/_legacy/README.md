# _legacy — 已归档的一次性脚本

这里放**已执行完、不再需要**的一次性脚本,仅作历史参考,不参与运行/构建。
(渐进式重构 阶段 0 归档,见 ../../重构审计报告.md)

| 文件 | 原用途 | 为什么归档 |
|---|---|---|
| `init_database.py` | 早期建库脚本(读 database_schema.sql) | 已被 `../init_db.py`(ORM create_all)取代 |
| `database_schema.sql` | 手写建表 SQL | 已过时且不完整(缺 activities / activity_details 表),无代码引用;真实 schema 以 ORM models 为准 |
| `create_crawler_logs_table.py` / `.sql` | 一次性建 crawler_logs 表 | 已执行,表已存在 |
| `add_crawler_log_id.sql` | 一次性给 crawler_logs 加自增 id | 已执行 |
| `add_qq_groups_field.py` | 一次性给 activity_details 加 qq_groups 字段 | 已执行 |
| `check_students_table.py` | 一次性检查 students 表结构 | 调试用,已无意义 |
| `update_password.py` / `update_admin_password.sql` | 一次性改 admin 密码哈希 | 已执行 |

> schema 变更今后应通过正式迁移管理(见路线图阶段 3),不要再往这里加脚本。
