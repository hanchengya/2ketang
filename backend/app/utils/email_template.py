#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件模板
"""
from typing import Dict, Any
from datetime import datetime


def render_new_activity_email(activity: Dict[str, Any]) -> str:
    """
    渲染新活动通知邮件

    Args:
        activity: 活动信息字典

    Returns:
        HTML格式的邮件内容
    """
    # 格式化时间
    def format_time(dt):
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d %H:%M")
        return str(dt) if dt else "待定"

    # 格式化是否需要作业
    job_required = "是" if activity.get("job") else "否"

    template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h2 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .field {{
            margin: 15px 0;
            padding: 12px;
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }}
        .label {{
            font-weight: bold;
            color: #667eea;
            display: block;
            margin-bottom: 5px;
        }}
        .value {{
            color: #555;
            word-wrap: break-word;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}
        .highlight {{
            color: #e74c3c;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🎉 数智维新工作室提醒您</h2>
            <p>有一个新的二课活动可以报名了！</p>
        </div>
        <div class="content">
            <div class="field">
                <span class="label">📌 1. 活动名称</span>
                <span class="value">{act_name}</span>
            </div>
            <div class="field">
                <span class="label">📂 2. 活动分类</span>
                <span class="value">{class_name}</span>
            </div>
            <div class="field">
                <span class="label">🏢 3. 活动主办方</span>
                <span class="value">{org_name}</span>
            </div>
            <div class="field">
                <span class="label">⏰ 4. 活动时间</span>
                <span class="value">{start_time} 至 {end_time}</span>
            </div>
            <div class="field">
                <span class="label">📍 5. 活动场地</span>
                <span class="value">{pitch_address}</span>
            </div>
            <div class="field">
                <span class="label">📝 6. 是否需要提交作业</span>
                <span class="value">{job_required}</span>
            </div>
            <div class="field">
                <span class="label">📄 7. 活动简介</span>
                <span class="value">{introduce}</span>
            </div>
            <div class="field">
                <span class="label">💬 8. 活动QQ群</span>
                <span class="value highlight">{qq_groups}</span>
            </div>
            <div class="field">
                <span class="label">👥 9. 活动限制人数</span>
                <span class="value">{people_limit}</span>
            </div>
            <div class="field">
                <span class="label">⏳ 10. 报名截止时间</span>
                <span class="value highlight">{enroll_end_time}</span>
            </div>
            <div class="field">
                <span class="label">🏫 11. 可参与院系</span>
                <span class="value">{college_name}</span>
            </div>
            <div class="field">
                <span class="label">🎓 12. 可参与年级</span>
                <span class="value">{grade_name}</span>
            </div>
        </div>
        <div class="footer">
            <p>此邮件由第二课堂活动通知系统自动发送，请勿回复</p>
            <p>如有疑问，请联系数智维新工作室</p>
        </div>
    </div>
</body>
</html>
    """

    return template.format(
        act_name=activity.get("act_name", "未知活动"),
        class_name=activity.get("class_name", "未分类"),
        org_name=activity.get("org_name", "未知主办方"),
        start_time=format_time(activity.get("start_time")),
        end_time=format_time(activity.get("end_time")),
        pitch_address=activity.get("pitch_address") or "待定",
        job_required=job_required,
        introduce=activity.get("introduce") or "暂无简介",
        qq_groups=activity.get("qq_groups") or "暂无",
        people_limit=activity.get("people_limit") or "不限",
        enroll_end_time=format_time(activity.get("enroll_end_time")),
        college_name=activity.get("college_name") or "不限",
        grade_name=activity.get("grade_name") or "不限"
    )


def render_sign_in_email(activity: Dict[str, Any]) -> str:
    """
    渲染签到提醒邮件

    Args:
        activity: 活动信息字典

    Returns:
        HTML格式的邮件内容
    """
    def format_time(dt):
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d %H:%M")
        return str(dt) if dt else "待定"

    template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h2 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .field {{
            margin: 15px 0;
            padding: 12px;
            background-color: #fff5f5;
            border-left: 4px solid #f5576c;
            border-radius: 4px;
        }}
        .label {{
            font-weight: bold;
            color: #f5576c;
            display: block;
            margin-bottom: 5px;
        }}
        .value {{
            color: #555;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}
        .urgent {{
            background-color: #ffe6e6;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            text-align: center;
            color: #e74c3c;
            font-weight: bold;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>⏰ 数智维新工作室提醒您</h2>
            <p>有一个二课活动可能开始签到了！</p>
        </div>
        <div class="content">
            <div class="urgent">
                ⚠️ 请及时前往活动现场签到！
            </div>
            <div class="field">
                <span class="label">📌 活动名称</span>
                <span class="value">{act_name}</span>
            </div>
            <div class="field">
                <span class="label">⏰ 活动时间</span>
                <span class="value">{start_time} 至 {end_time}</span>
            </div>
            <div class="field">
                <span class="label">📍 活动场地</span>
                <span class="value">{pitch_address}</span>
            </div>
            <div class="field">
                <span class="label">💬 活动QQ群</span>
                <span class="value">{qq_groups}</span>
            </div>
        </div>
        <div class="footer">
            <p>此邮件由第二课堂活动通知系统自动发送，请勿回复</p>
            <p>如有疑问，请联系数智维新工作室</p>
        </div>
    </div>
</body>
</html>
    """

    return template.format(
        act_name=activity.get("act_name", "未知活动"),
        start_time=format_time(activity.get("start_time")),
        end_time=format_time(activity.get("end_time")),
        pitch_address=activity.get("pitch_address") or "待定",
        qq_groups=activity.get("qq_groups") or "暂无"
    )


def render_sign_out_email(activity: Dict[str, Any]) -> str:
    """
    渲染签退提醒邮件

    Args:
        activity: 活动信息字典

    Returns:
        HTML格式的邮件内容
    """
    def format_time(dt):
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d %H:%M")
        return str(dt) if dt else "待定"

    template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h2 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .field {{
            margin: 15px 0;
            padding: 12px;
            background-color: #f0f9ff;
            border-left: 4px solid #00f2fe;
            border-radius: 4px;
        }}
        .label {{
            font-weight: bold;
            color: #00a8cc;
            display: block;
            margin-bottom: 5px;
        }}
        .value {{
            color: #555;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}
        .urgent {{
            background-color: #e6f7ff;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            text-align: center;
            color: #0066cc;
            font-weight: bold;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>✅ 数智维新工作室提醒您</h2>
            <p>有一个二课活动可能开始签退了！</p>
        </div>
        <div class="content">
            <div class="urgent">
                ⚠️ 请及时前往活动现场签退！
            </div>
            <div class="field">
                <span class="label">📌 活动名称</span>
                <span class="value">{act_name}</span>
            </div>
            <div class="field">
                <span class="label">⏰ 活动时间</span>
                <span class="value">{start_time} 至 {end_time}</span>
            </div>
            <div class="field">
                <span class="label">📍 活动场地</span>
                <span class="value">{pitch_address}</span>
            </div>
            <div class="field">
                <span class="label">💬 活动QQ群</span>
                <span class="value">{qq_groups}</span>
            </div>
        </div>
        <div class="footer">
            <p>此邮件由第二课堂活动通知系统自动发送，请勿回复</p>
            <p>如有疑问，请联系数智维新工作室</p>
        </div>
    </div>
</body>
</html>
    """

    return template.format(
        act_name=activity.get("act_name", "未知活动"),
        start_time=format_time(activity.get("start_time")),
        end_time=format_time(activity.get("end_time")),
        pitch_address=activity.get("pitch_address") or "待定",
        qq_groups=activity.get("qq_groups") or "暂无"
    )
