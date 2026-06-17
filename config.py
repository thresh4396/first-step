"""
「第一步」配置文件
所有常量、默认值、文本模板集中管理
"""

import os
import sys

# ---- 路径 ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 数据文件
STREAK_FILE = os.path.join(DATA_DIR, "streak.json")
CAPTURE_FILE = os.path.join(DATA_DIR, "capture_pool.json")
DAILY_LOG_FILE = os.path.join(DATA_DIR, "daily_log.json")
CALENDAR_FILE = os.path.join(DATA_DIR, "calendar.json")
TODAY_TASK_FILE = os.path.join(DATA_DIR, "today_task.json")
REVIEW_FILE = os.path.join(DATA_DIR, "reviews.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
HABITS_FILE = os.path.join(DATA_DIR, "daily_habits.json")

# ---- 默认值 ----
DEFAULT_MAIN_TASK = {
    "title": "背英语单词",
    "count": 10,
    "unit": "个",
    "estimated_minutes": 15,
    "status": "pending",  # pending | done
    "actual_minutes": None,
}

DEFAULT_TODOS = []  # 今日待办，最多 3 个

MAX_TODOS_DISPLAY = 3

# 捕获池分类
POOL_TODO = "todo"       # 待办
POOL_INSPIRATION = "inspiration"  # 灵感
POOL_ERRAND = "errand"   # 琐事

POOL_CATEGORIES = {
    POOL_TODO: "[TODO] 待办",
    POOL_INSPIRATION: "[IDEA] 灵感",
    POOL_ERRAND: "[LIFE] 琐事",
}

# ---- 起床助手步骤 ----
MORNING_STEPS = [
    "喝一杯水",
    "洗漱",
    "坐到桌前",
]

MORNING_ENCOURAGEMENTS = [
    "不需要完美，只需要开始。",
    "每一个伟大的日子，都从一个微小的动作开始。",
    "你不需要看到整个楼梯，只需迈出第一步。",
    "今天不必是完美的一天，只要是在路上就好。",
    "好的开始是成功的一半。",
    "慢慢来，不急。你已经在做了。",
]

# ---- 环境检查 ----
ENV_CHECKS = [
    "手机不在手边",
    "桌上只有当前要做的东西",
    "手边有一杯水",
]

# ---- 专注计时器 ----
DEFAULT_FOCUS_MINUTES = 15
FOCUS_MIN = 5
FOCUS_MAX = 60

# ---- 每周回顾问题 ----
REVIEW_QUESTIONS = [
    "昨天完成了什么？（一两句话即可）",
    "今天最想做的一件事：",
]

# ---- 启动检查 ----
# 命令行参数
if "--no-morning" in sys.argv:
    SKIP_MORNING = True
else:
    SKIP_MORNING = False
