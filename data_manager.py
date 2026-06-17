"""
数据持久化管理
所有 JSON 读写集中处理
"""

import json
import os
from datetime import date, datetime
from config import (
    STREAK_FILE, CAPTURE_FILE, DAILY_LOG_FILE, CALENDAR_FILE,
    TODAY_TASK_FILE, REVIEW_FILE, CONFIG_FILE, DATA_DIR,
    DEFAULT_MAIN_TASK, POOL_TODO, POOL_INSPIRATION, POOL_ERRAND,
    HABITS_FILE, MAX_TODOS_DISPLAY,
)


def _ensure_data_dir():
    """确保 data 目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)


def _read_json(filepath, default=None):
    """读取 JSON 文件，不存在则返回默认值"""
    _ensure_data_dir()
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def _write_json(filepath, data):
    """写入 JSON 文件"""
    _ensure_data_dir()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def today_key():
    """返回今天的日期字符串 'YYYY-MM-DD'"""
    return date.today().isoformat()


def now_iso():
    """返回当前 ISO 时间戳"""
    return datetime.now().isoformat()


# ========== 连续天数 ==========

def get_streak():
    """返回 {'current': int, 'last_date': str}"""
    data = _read_json(STREAK_FILE)
    if data is None:
        data = {"current": 0, "last_date": None}
    return data


def update_streak():
    """更新连续天数：今天完成主线任务后调用"""
    data = get_streak()
    td = today_key()
    last = data.get("last_date")

    if last == td:
        return data["current"]  # 今天已经记录过了

    # 检查昨天是否完成了
    yesterday = date.today()
    from datetime import timedelta
    yesterday = (yesterday - timedelta(days=1)).isoformat()

    if last == yesterday:
        data["current"] += 1
    elif last == td:
        pass  # 已记录
    else:
        data["current"] = 1  # 断了，重新计数

    data["last_date"] = td
    _write_json(STREAK_FILE, data)
    return data["current"]


def get_week_completion():
    """返回本周完成天数"""
    from datetime import timedelta
    today = date.today()
    # 本周一
    monday = today - timedelta(days=today.weekday())
    completions = 0
    daily_log = get_daily_log()

    for i in range(7):
        d = (monday + timedelta(days=i)).isoformat()
        if d in daily_log and daily_log[d].get("main_done"):
            completions += 1
    return completions


# ========== 今日任务 ==========

def get_today_task():
    """获取今日主线任务"""
    data = _read_json(TODAY_TASK_FILE)
    if data is None:
        data = {
            "date": today_key(),
            "task": dict(DEFAULT_MAIN_TASK),
            "todos": [],
        }
    # 如果日期变了，重置状态但保留任务定义
    if data.get("date") != today_key():
        task_def = data.get("task", dict(DEFAULT_MAIN_TASK))
        task_def["status"] = "pending"
        task_def["actual_minutes"] = None
        data = {
            "date": today_key(),
            "task": task_def,
            "todos": data.get("todos", []),  # 待办不清空
        }
    return data


def save_today_task(data):
    """保存今日任务"""
    data["date"] = today_key()
    _write_json(TODAY_TASK_FILE, data)


def update_main_task(task_dict):
    """更新主线任务定义"""
    td = get_today_task()
    td["task"] = task_dict
    save_today_task(td)


def update_todos(todos_list):
    """更新今日待办列表"""
    td = get_today_task()
    td["todos"] = todos_list
    save_today_task(td)


# ========== 捕获池 ==========

def get_capture_pool():
    """返回捕获池 {'todo': [], 'inspiration': [], 'errand': []}"""
    default = {POOL_TODO: [], POOL_INSPIRATION: [], POOL_ERRAND: []}
    data = _read_json(CAPTURE_FILE)
    if data is None:
        data = default
    # 确保所有分类存在
    for key in default:
        if key not in data:
            data[key] = []
    return data


def save_capture_pool(pool):
    """保存捕获池"""
    _write_json(CAPTURE_FILE, pool)


def add_to_pool(category, text):
    """向捕获池添加条目"""
    pool = get_capture_pool()
    if category not in pool:
        category = POOL_TODO
    pool[category].append({
        "text": text,
        "added": now_iso(),
        "id": len(pool[category]) + 1,
    })
    save_capture_pool(pool)


def remove_from_pool(category, index):
    """从捕获池删除条目"""
    pool = get_capture_pool()
    if category in pool and 0 <= index < len(pool[category]):
        pool[category].pop(index)
        save_capture_pool(pool)
        return True
    return False


def move_pool_item(from_cat, to_cat, index):
    """移动捕获池条目到另一个分类"""
    pool = get_capture_pool()
    if from_cat in pool and 0 <= index < len(pool[from_cat]):
        item = pool[from_cat].pop(index)
        if to_cat not in pool:
            to_cat = POOL_TODO
        pool[to_cat].append(item)
        save_capture_pool(pool)
        return True
    return False


# ========== 每日日志 ==========

def get_daily_log():
    """返回 { 'YYYY-MM-DD': { main_done, main_minutes, todos_done, note } }"""
    data = _read_json(DAILY_LOG_FILE)
    if data is None:
        data = {}
    return data


def save_daily_entry(entry):
    """
    保存今天的日志
    entry: { main_done: bool, main_minutes: int, todos_done: int, note: str }
    """
    log = get_daily_log()
    td = today_key()
    if td not in log:
        log[td] = {}
    log[td].update(entry)
    _write_json(DAILY_LOG_FILE, log)


# ========== 回顾 ==========

def get_reviews():
    """返回回顾列表"""
    return _read_json(REVIEW_FILE) or []


def add_review(text, mood=""):
    """添加一条回顾"""
    reviews = get_reviews()
    reviews.append({
        "date": today_key(),
        "timestamp": now_iso(),
        "text": text,
        "mood": mood,
    })
    _write_json(REVIEW_FILE, reviews)


def get_last_review_date():
    """获取最后回顾日期"""
    reviews = get_reviews()
    if reviews:
        return reviews[-1].get("date")
    return None


def needs_review():
    """
    判断是否需要弹出回顾
    - 上次打开程序时没有填回顾
    - 并且今天 > 上次回顾日期
    """
    last = get_last_review_date()
    if last is None:
        return False
    td = today_key()
    return last != td  # 如果上次回顾不是今天，可能需要补


# ========== 日历 ==========

def get_calendar_data():
    """返回 { 'YYYY-MM-DD': [ { text, time, done }, ... ] }"""
    return _read_json(CALENDAR_FILE) or {}


def save_calendar_data(data):
    """保存日历数据"""
    _write_json(CALENDAR_FILE, data)


def get_date_events(date_str):
    """获取指定日期的事项列表"""
    cal = get_calendar_data()
    return cal.get(date_str, [])


def add_date_event(date_str, text, event_time=""):
    """向指定日期添加事项"""
    cal = get_calendar_data()
    if date_str not in cal:
        cal[date_str] = []
    cal[date_str].append({
        "text": text,
        "time": event_time,
        "done": False,
        "added": now_iso(),
    })
    save_calendar_data(cal)


def remove_date_event(date_str, index):
    """删除指定日期的某项事项"""
    cal = get_calendar_data()
    if date_str in cal and 0 <= index < len(cal[date_str]):
        cal[date_str].pop(index)
        if not cal[date_str]:
            del cal[date_str]
        save_calendar_data(cal)
        return True
    return False


def toggle_date_event(date_str, index):
    """切换事项完成状态"""
    cal = get_calendar_data()
    if date_str in cal and 0 <= index < len(cal[date_str]):
        cal[date_str][index]["done"] = not cal[date_str][index].get("done", False)
        save_calendar_data(cal)
        return True
    return False


def get_today_reminders():
    """获取今日提醒"""
    return get_date_events(today_key())


def get_upcoming_events(days=7):
    """获取未来 N 天的事项"""
    from datetime import timedelta
    cal = get_calendar_data()
    today = date.today()
    upcoming = []
    for i in range(days):
        d = (today + timedelta(days=i)).isoformat()
        if d in cal and cal[d]:
            upcoming.append((d, cal[d]))
    return upcoming


# ========== 每日习惯 ==========

def get_daily_habits():
    """返回每日习惯列表 [{text, minutes}, ...]"""
    return _read_json(HABITS_FILE) or []


def save_daily_habits(habits):
    """保存每日习惯列表"""
    _write_json(HABITS_FILE, habits)


def add_daily_habit(text, minutes=15):
    """添加一个每日习惯"""
    habits = get_daily_habits()
    habits.append({"text": text, "minutes": minutes})
    save_daily_habits(habits)


def remove_daily_habit(index):
    """删除一个每日习惯"""
    habits = get_daily_habits()
    if 0 <= index < len(habits):
        habits.pop(index)
        save_daily_habits(habits)
        return True
    return False


def auto_populate_daily_habits():
    """
    每日首次打开时，将每日习惯自动填充到今日待办
    返回是否进行了填充
    """
    log = get_daily_log()
    td = today_key()
    if log.get(td, {}).get("habits_populated"):
        return False  # 今天已经填充过了

    habits = get_daily_habits()
    if not habits:
        return False

    td_data = get_today_task()
    existing_texts = {t["text"] for t in td_data.get("todos", [])}
    added = False

    for habit in habits:
        if habit["text"] not in existing_texts and len(td_data.get("todos", [])) < MAX_TODOS_DISPLAY:
            td_data.setdefault("todos", []).append({
                "text": habit["text"],
                "done": False,
                "minutes": habit.get("minutes", 15),
            })
            added = True

    if added:
        save_today_task(td_data)

    # 标记已填充
    save_daily_entry({"habits_populated": True})
    return added
