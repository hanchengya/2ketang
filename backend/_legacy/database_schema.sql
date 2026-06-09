-- 第二课堂活动通知系统 - 数据库初始化脚本
-- 执行前请确保已连接到2ketang数据库

USE 2ketang;

-- 1. 修改students表，添加email字段（如果不存在）
-- 使用存储过程来安全地添加列
DELIMITER $$

DROP PROCEDURE IF EXISTS add_email_column$$
CREATE PROCEDURE add_email_column()
BEGIN
    DECLARE column_exists INT DEFAULT 0;

    SELECT COUNT(*) INTO column_exists
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = '2ketang'
    AND TABLE_NAME = 'students'
    AND COLUMN_NAME = 'email';

    IF column_exists = 0 THEN
        ALTER TABLE students ADD COLUMN email VARCHAR(255) COMMENT '邮箱地址' AFTER mobile;
        ALTER TABLE students ADD INDEX idx_email (email);
        SELECT '已添加email字段' AS message;
    ELSE
        SELECT 'email字段已存在' AS message;
    END IF;
END$$

DELIMITER ;

CALL add_email_column();
DROP PROCEDURE IF EXISTS add_email_column;

-- 插入测试数据
UPDATE students SET email = '19161931205@163.com' WHERE code = '20232818';

-- 2. 创建activity_notifications表（活动通知记录表）
CREATE TABLE IF NOT EXISTS activity_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    act_id INT NOT NULL COMMENT '活动ID',
    notification_type ENUM('new_activity', 'sign_in', 'sign_out') NOT NULL COMMENT '通知类型',
    sent_at DATETIME NOT NULL COMMENT '发送时间',
    recipient_count INT DEFAULT 0 COMMENT '接收人数',
    success_count INT DEFAULT 0 COMMENT '成功发送数',
    fail_count INT DEFAULT 0 COMMENT '失败发送数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_act_notification (act_id, notification_type),
    INDEX idx_sent_at (sent_at),
    INDEX idx_act_id (act_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='活动通知记录表';

-- 3. 创建activity_participants表（活动参与者表）
CREATE TABLE IF NOT EXISTS activity_participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    act_id INT NOT NULL COMMENT '活动ID',
    student_code VARCHAR(50) NOT NULL COMMENT '学号',
    student_name VARCHAR(100) COMMENT '学生姓名',
    sign_in_time DATETIME COMMENT '签到时间',
    sign_out_time DATETIME COMMENT '签退时间',
    credits DECIMAL(5,2) COMMENT '获得学分',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_act_student (act_id, student_code),
    INDEX idx_act_id (act_id),
    INDEX idx_student_code (student_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='活动参与者表';

-- 4. 创建email_logs表（邮件发送日志表）
CREATE TABLE IF NOT EXISTS email_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    act_id INT NOT NULL COMMENT '活动ID',
    recipient_email VARCHAR(255) NOT NULL COMMENT '收件人邮箱',
    student_code VARCHAR(50) COMMENT '学号',
    email_type ENUM('new_activity', 'sign_in', 'sign_out') NOT NULL COMMENT '邮件类型',
    subject VARCHAR(500) COMMENT '邮件主题',
    status ENUM('pending', 'sent', 'failed') DEFAULT 'pending' COMMENT '发送状态',
    error_message TEXT COMMENT '错误信息',
    sent_at DATETIME COMMENT '发送时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_act_id (act_id),
    INDEX idx_student_code (student_code),
    INDEX idx_status (status),
    INDEX idx_sent_at (sent_at),
    INDEX idx_recipient_email (recipient_email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='邮件发送日志表';

-- 5. 创建users表（管理员用户表）
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    email VARCHAR(255) COMMENT '邮箱',
    role ENUM('admin', 'operator') DEFAULT 'operator' COMMENT '角色',
    is_active TINYINT DEFAULT 1 COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员用户表';

-- 插入默认管理员账号（用户名：admin，密码：admin123）
-- 密码哈希使用bcrypt生成
INSERT IGNORE INTO users (username, password_hash, role)
VALUES ('admin', '$2b$12$5BJACBReXMmIVuAwCCgjpOFhGK48Radr3k/dgCou9HW2DkMpZBdAC', 'admin');

-- 修复早期初始化脚本中admin默认密码哈希不匹配admin123的问题
UPDATE users
SET password_hash = '$2b$12$5BJACBReXMmIVuAwCCgjpOFhGK48Radr3k/dgCou9HW2DkMpZBdAC'
WHERE username = 'admin'
AND password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/VXlTW';

-- 显示创建结果
SELECT '数据库初始化完成！' AS message;
SELECT COUNT(*) AS student_count, '有邮箱的学生数' AS description FROM students WHERE email IS NOT NULL;
SELECT COUNT(*) AS user_count, '管理员用户数' AS description FROM users;
SELECT COUNT(*) AS notification_table, 'activity_notifications表' AS description FROM information_schema.TABLES WHERE TABLE_SCHEMA = '2ketang' AND TABLE_NAME = 'activity_notifications';
SELECT COUNT(*) AS participant_table, 'activity_participants表' AS description FROM information_schema.TABLES WHERE TABLE_SCHEMA = '2ketang' AND TABLE_NAME = 'activity_participants';
SELECT COUNT(*) AS email_log_table, 'email_logs表' AS description FROM information_schema.TABLES WHERE TABLE_SCHEMA = '2ketang' AND TABLE_NAME = 'email_logs';
