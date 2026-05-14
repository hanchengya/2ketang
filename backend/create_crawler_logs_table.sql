-- 创建爬虫日志表
CREATE TABLE IF NOT EXISTS `crawler_logs` (
  `task_id` VARCHAR(36) PRIMARY KEY COMMENT '任务ID',
  `task_type` ENUM('activities', 'details', 'students', 'participants') NOT NULL COMMENT '任务类型',
  `status` ENUM('pending', 'running', 'stopped', 'completed', 'failed') NOT NULL DEFAULT 'pending' COMMENT '任务状态',
  `current_count` INT DEFAULT 0 COMMENT '当前进度',
  `total_count` INT DEFAULT 0 COMMENT '总数',
  `log_content` TEXT COMMENT '日志内容',
  `started_at` TIMESTAMP NULL COMMENT '开始时间',
  `finished_at` TIMESTAMP NULL COMMENT '完成时间',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_task_type` (`task_type`),
  INDEX `idx_status` (`status`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='爬虫日志表';
