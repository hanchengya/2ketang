-- 更新admin用户的密码哈希
UPDATE users
SET password_hash = '$2b$12$5BJACBReXMmIVuAwCCgjpOFhGK48Radr3k/dgCou9HW2DkMpZBdAC'
WHERE username = 'admin';

-- 验证更新
SELECT username, role, LEFT(password_hash, 20) as password_prefix FROM users WHERE username = 'admin';
