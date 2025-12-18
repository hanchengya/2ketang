# 第二课堂自动登录系统

自动登录第二课堂平台，自动处理滑块验证码。

## 使用方法

1. 安装依赖：
```bash
pip install selenium
```

2. 修改 `main.py` 中的配置：
```python
USERNAME = "你的学号"
PASSWORD = "你的密码"
```

3. 运行：
```bash
python main.py
```

## 原理

通过JS逆向获取滑块验证码的缺口位置（`block_x`），加上校准偏移值后执行滑动。
