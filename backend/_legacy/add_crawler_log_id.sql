-- 为 crawler_logs 表添加自增ID列
-- 先备份数据，然后重建表

-- 1. 创建临时表保存数据
CREATE TABLE IF NOT EXISTS crawler_logs_backup AS SELECT * FROM crawler_logs;

-- 2. 删除原表
DROP TABLE IF EXISTS crawler_logs;

-- 3. 重建表，添加自增ID
CREATE TABLE crawler_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
    task_id VARCHAR(36) NOT NULL UNIQUE COMMENT '任务ID',
    task_type VARCHAR(20) NOT NULL COMMENT '任务类型',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态',
    current_count INT DEFAULT 0 COMMENT '当前进度',
    total_count INT DEFAULT 0 COMMENT '总数',
    log_content TEXT COMMENT '日志内容',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    finished_at TIMESTAMP NULL COMMENT '完成时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_task_id (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬虫日志表';

-- 4. 恢复数据
INSERT INTO crawler_logs (task_id, task_type, status, current_count, total_count, log_content, started_at, finished_at, created_at, updated_at)
SELECT task_id, task_type, status, current_count, total_count, log_content, started_at, finished_at, created_at, updated_at
FROM crawler_logs_backup;

-- 5. 删除备份表
DROP TABLE IF EXISTS crawler_logs_backup;
