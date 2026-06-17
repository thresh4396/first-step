"""
「第一步」- 极简生活启动器
帮助你迈出每天的第一步
"""

import sys
import os
import time
import random
from datetime import date, datetime, timedelta

# 确保能找到模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    DEFAULT_MAIN_TASK, MAX_TODOS_DISPLAY,
    MORNING_STEPS, MORNING_ENCOURAGEMENTS, ENV_CHECKS,
    DEFAULT_FOCUS_MINUTES, POOL_TODO, POOL_INSPIRATION, POOL_ERRAND,
    POOL_CATEGORIES, SKIP_MORNING, REVIEW_QUESTIONS, FOCUS_MIN, FOCUS_MAX,
)
from display import (
    clear, header, footer, section, section_end, box_line,
    info, success, warn, emph, menu_item, progress_bar, input_safe, SEP,
)
from data_manager import (
    today_key, now_iso,
    get_streak, update_streak,
    get_today_task, save_today_task, update_main_task, update_todos,
    get_capture_pool, save_capture_pool, add_to_pool, remove_from_pool, move_pool_item,
    get_daily_log, save_daily_entry,
    get_reviews, add_review, get_last_review_date,
    get_calendar_data, get_date_events, add_date_event,
    remove_date_event, toggle_date_event, get_today_reminders,
    get_week_completion,
)
from lunar import lunar_date_string, lunar_day_short, solar_days_in_month


# ======================== 起床助手 ========================

def morning_kick():
    """每天第一次打开时触发的起床仪式"""
    clear()
    header("第一步 · 早安")

    now = datetime.now()
    greeting = "早上好" if now.hour < 12 else ("下午好" if now.hour < 18 else "晚上好")
    info(f"{greeting}，现在是 {now.strftime('%Y年%m月%d日 %H:%M')}")
    print()

    section("起床三步")
    for i, step in enumerate(MORNING_STEPS, 1):
        info(f"  [{i}] {step}")
        input_safe("完成这一步后按回车...")
    section_end()

    print()
    emph(random.choice(MORNING_ENCOURAGEMENTS))

    # 可选：环境检查
    print()
    resp = input_safe("要做环境检查吗？(y/n，直接回车跳过) ").lower()
    if resp == "y":
        print()
        section("环境就绪")
        for check in ENV_CHECKS:
            ans = input_safe(f"  {check} 好了吗？(回车=好了) ")
        section_end()
    print()

    input_safe("准备好开始今天了，按回车进入主界面...")


# ======================== 每日回顾 ========================

def daily_review_check():
    """检查是否需要补填回顾"""
    log = get_daily_log()
    td = today_key()

    # 检查昨天是否有日志但没回顾
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    reviews = get_reviews()

    # 如果今天已经有回顾，跳过
    if reviews and reviews[-1].get("date") == td:
        return

    # 如果昨天有活动记录但没有回顾
    need_review = False
    if yesterday in log and log[yesterday].get("main_done"):
        need_review = True
    # 或者上次回顾不是今天也不是昨天
    if not need_review:
        last = get_last_review_date()
        if last and last != td and last != yesterday:
            # 检查是否有未回顾的日子
            pass  # 先跳过这个复杂逻辑

    if need_review:
        clear()
        header("第一步 · 昨日回顾")
        info(f"昨天（{yesterday}）你完成了主线任务！")
        print()

        for q in REVIEW_QUESTIONS:
            ans = input_safe(f"  {q}\n  > ")
            if ans:
                add_review(f"{q}: {ans}")

        print()
        success("回顾已保存。新的一天，继续加油！")
        print()
        input_safe("按回车进入主界面...")


# ======================== 今日提醒 ========================

def show_today_reminders():
    """显示今日日历提醒"""
    reminders = get_today_reminders()
    if not reminders:
        return

    active_reminders = [r for r in reminders if not r.get("done", False)]
    if not active_reminders:
        return

    print()
    info("[CAL] 今日提醒：")
    for r in active_reminders[:5]:  # 最多显示 5 条
        time_str = f"[{r['time']}] " if r.get("time") else ""
        print(f"    [!] {time_str}{r['text']}")
    print(f"  {SEP}")


def show_upcoming_events():
    """显示待办日历事项摘要"""
    from data_manager import get_upcoming_events
    upcoming = get_upcoming_events(days=3)
    active = []
    for d, events in upcoming:
        for e in events:
            if not e.get("done", False):
                active.append((d, e))
                if len(active) >= 3:
                    break
        if len(active) >= 3:
            break

    if active:
        print()
        info("[CAL] 近期事项：")
        for d, e in active:
            ds = d[5:]  # 去掉年份
            print(f"    · {ds} {e['text']}")


# ======================== 专注计时器 ========================

def focus_timer(task_name, default_minutes=15):
    """专注计时器 - 不锁屏，只在终端里倒计时"""
    clear()
    header(f"专注时间 · {task_name}")

    # 设置时长
    try:
        mins_input = input_safe(f"专注时长（分钟，默认 {default_minutes}，{FOCUS_MIN}-{FOCUS_MAX}）：")
        minutes = int(mins_input) if mins_input else default_minutes
        minutes = max(FOCUS_MIN, min(FOCUS_MAX, minutes))
    except ValueError:
        minutes = default_minutes

    total_seconds = minutes * 60
    start_time = time.time()

    print()
    box_line(f"任务：{task_name}")
    box_line(f"时长：{minutes} 分钟")
    box_line("")
    box_line("计时器在终端里运行，不会锁屏。")
    box_line("你可以随时切到别的窗口做事。")
    box_line("按 [q] 提前结束  [p] 暂停")
    print(f"  {'─' * 45}")

    paused = False
    pause_start = 0
    total_pause = 0

    while True:
        if paused:
            # 检查输入（轮询方式）
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch().decode("utf-8", errors="ignore").lower()
                if key == "p":
                    pause_duration = time.time() - pause_start
                    total_pause += pause_duration
                    paused = False
                    print(f"\n  [>] 继续计时")
                elif key == "q":
                    print(f"\n  [STOP] 专注提前结束")
                    break
            time.sleep(0.1)
            continue

        elapsed = int(time.time() - start_time - total_pause)
        remaining = max(0, total_seconds - elapsed)

        if remaining <= 0:
            break

        # 显示倒计时
        mins = remaining // 60
        secs = remaining % 60
        pct = elapsed / total_seconds

        bar = progress_bar(elapsed, total_seconds, 25)
        time_str = f"{mins:02d}:{secs:02d}"
        print(f"\r  [{bar}] {time_str}  ", end="", flush=True)

        # 检查按键（仅 Windows）
        try:
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch().decode("utf-8", errors="ignore").lower()
                if key == "q":
                    print(f"\n\n  [STOP] 专注时间提前结束")
                    break
                elif key == "p":
                    paused = True
                    pause_start = time.time()
                    print(f"\n\n  [PAUSE] 已暂停，按 [p] 继续 [q] 结束")
        except ImportError:
            pass
        except Exception:
            pass

        time.sleep(0.1)

    # 计时结束
    actual_minutes = round(elapsed / 60, 1)
    print(f"\n\n  [DING] 时间到！实际专注了 {actual_minutes} 分钟。")

    # 记录
    note = input_safe("完成了什么？（一句话，回车跳过）> ")
    print()

    return actual_minutes, note if note else None


# ======================== 捕获池管理 ========================

def capture_pool_screen():
    """捕获池完整管理界面"""
    while True:
        clear()
        header("第一步 · 捕获池")

        pool = get_capture_pool()

        for cat_key in [POOL_TODO, POOL_INSPIRATION, POOL_ERRAND]:
            cat_label = POOL_CATEGORIES[cat_key]
            items = pool.get(cat_key, [])
            print(f"\n  {cat_label}  ({len(items)}项)")
            print(f"  {SEP}")
            if items:
                for i, item in enumerate(items, 1):
                    print(f"    {i}. {item['text']}")
            else:
                print(f"    （空）")

        print(f"\n  {'=' * 44}")
        print(f"  [A] 添加  [D] 删除  [M] 移动到其它分类")
        print(f"  [T] 拖到今日待办  [B] 返回主页")
        print(f"  {'=' * 45}")

        cmd = input_safe().lower()

        if cmd == "b":
            break
        elif cmd == "a":
            print(f"\n  选择分类：")
            for k, v in POOL_CATEGORIES.items():
                print(f"    [{k[0]}] {v}")
            cat = input_safe("选哪个？(t/i/e) > ").lower()
            cat_map = {"t": POOL_TODO, "i": POOL_INSPIRATION, "e": POOL_ERRAND}
            category = cat_map.get(cat, POOL_TODO)
            text = input_safe("输入内容：> ")
            if text:
                add_to_pool(category, text)
                success("已添加！")
                time.sleep(0.5)
        elif cmd == "d":
            cat_key = _choose_category()
            if not cat_key:
                continue
            items = pool.get(cat_key, [])
            if not items:
                warn("这个分类是空的")
                time.sleep(1)
                continue
            try:
                idx = int(input_safe(f"删除第几个？(1-{len(items)}) > ")) - 1
                if remove_from_pool(cat_key, idx):
                    success("已删除")
                    time.sleep(0.5)
            except (ValueError, IndexError):
                warn("无效的选择")
                time.sleep(1)
        elif cmd == "m":
            from_cat = _choose_category()
            if not from_cat:
                continue
            items = pool.get(from_cat, [])
            if not items:
                warn("这个分类是空的")
                time.sleep(1)
                continue
            try:
                idx = int(input_safe(f"移动第几个？(1-{len(items)}) > ")) - 1
                print()
                to_cat = _choose_category("移动到哪个分类？")
                if to_cat and from_cat != to_cat:
                    move_pool_item(from_cat, to_cat, idx)
                    success("已移动")
                    time.sleep(0.5)
            except (ValueError, IndexError):
                warn("无效的选择")
                time.sleep(1)
        elif cmd == "t":
            # 从待办池拖到今日待办
            items = pool.get(POOL_TODO, [])
            if not items:
                warn("待办池是空的")
                time.sleep(1)
                continue
            try:
                idx = int(input_safe(f"拖到今日待办第几个？(1-{len(items)}) > ")) - 1
                if 0 <= idx < len(items):
                    todo_text = items[idx]["text"]
                    td = get_today_task()
                    if len(td["todos"]) >= MAX_TODOS_DISPLAY:
                        warn(f"今日待办最多 {MAX_TODOS_DISPLAY} 个，请先完成或删除一些")
                        time.sleep(1.5)
                        continue
                    td["todos"].append({"text": todo_text, "done": False, "minutes": 15})
                    save_today_task(td)
                    remove_from_pool(POOL_TODO, idx)
                    success(f"「{todo_text}」已添加到今日待办")
                    time.sleep(1)
            except (ValueError, IndexError):
                warn("无效的选择")
                time.sleep(1)


def _choose_category(prompt_text="选择分类："):
    """辅助：选择捕获池分类"""
    print(f"\n  {prompt_text}")
    print(f"    [T] {POOL_CATEGORIES[POOL_TODO]}")
    print(f"    [I] {POOL_CATEGORIES[POOL_INSPIRATION]}")
    print(f"    [E] {POOL_CATEGORIES[POOL_ERRAND]}")
    cat = input_safe("> ").lower()
    cat_map = {"t": POOL_TODO, "i": POOL_INSPIRATION, "e": POOL_ERRAND}
    return cat_map.get(cat)


def inspiration_quick_view():
    """灵感和琐事快速查看"""
    pool = get_capture_pool()

    clear()
    header("第一步 · 灵感 & 琐事")

    for cat_key in [POOL_INSPIRATION, POOL_ERRAND]:
        cat_label = POOL_CATEGORIES[cat_key]
        items = pool.get(cat_key, [])
        print(f"\n  {cat_label}  ({len(items)}项)")
        print(f"  {SEP}")
        if items:
            for i, item in enumerate(items, 1):
                print(f"    {i}. {item['text']}")
        else:
            print(f"    （空）")

    print(f"\n  ═{'═' * 44}")
    print(f"  [A] 添加  [D] 删除  [M] 移到待办")
    print(f"  [T] 拖到今日待办  [B] 返回")
    print(f"  ═{'═' * 44}")

    cmd = input_safe().lower()
    if cmd == "b":
        return
    elif cmd == "a":
        print(f"\n  [I] 灵感  [E] 琐事")
        cat = input_safe("> ").lower()
        category = POOL_INSPIRATION if cat == "i" else POOL_ERRAND
        text = input_safe("输入内容：> ")
        if text:
            add_to_pool(category, text)
            success("已添加！")
            time.sleep(0.5)
            inspiration_quick_view()
    elif cmd == "d":
        cat_key = POOL_INSPIRATION
        # 先看看灵感有没有东西，没有再选琐事
        if not pool.get(POOL_INSPIRATION):
            cat_key = POOL_ERRAND
        items = pool.get(cat_key, [])
        if items:
            try:
                idx = int(input_safe(f"删除第几个？(1-{len(items)}) > ")) - 1
                remove_from_pool(cat_key, idx)
                success("已删除")
                time.sleep(0.5)
                inspiration_quick_view()
            except (ValueError, IndexError):
                pass
    elif cmd == "t":
        # 从灵感/琐事移动到待办池
        cat_key = POOL_INSPIRATION if pool.get(POOL_INSPIRATION) else POOL_ERRAND
        items = pool.get(cat_key, [])
        if items:
            try:
                idx = int(input_safe(f"移到待办池第几个？(1-{len(items)}) > ")) - 1
                move_pool_item(cat_key, POOL_TODO, idx)
                success("已移到待办！")
                time.sleep(0.5)
                inspiration_quick_view()
            except (ValueError, IndexError):
                pass


# ======================== 日历视图 ========================

def calendar_screen():
    """日历界面 - 月视图 + 农历"""
    today = date.today()
    view_year = today.year
    view_month = today.month

    while True:
        clear()
        header(f"第一步 · 日历")

        # 月份标题
        gan_zhi, sx = lunar_date_string(view_year, view_month, 1).split("年")[0], ""
        # 简化计算：获取月中某天的农历信息做标题
        mid_day = min(15, solar_days_in_month(view_year, view_month))
        lunar_str = lunar_date_string(view_year, view_month, mid_day)
        lunar_year_info = lunar_str.split("年")[0] + "年"

        print(f"\n     {view_year}年{view_month}月    农历{lunar_year_info}")
        print(f"  {'─' * 42}")

        # 星期标题
        print(f"  一    二    三    四    五    六    日")
        print(f"  {'─' * 42}")

        # 计算本月第一天是星期几
        first_day = date(view_year, view_month, 1)
        first_weekday = first_day.weekday()  # 0=周一

        # 本月天数
        days_in_month = solar_days_in_month(view_year, view_month)

        # 日历数据
        cal_data = get_calendar_data()

        # 逐行打印
        day_num = 1
        for week in range(6):
            if day_num > days_in_month:
                break

            line = ""
            for wd in range(7):
                if week == 0 and wd < first_weekday:
                    line += "      "
                    continue
                if day_num > days_in_month:
                    line += "      "
                    continue

                d = day_num
                ds = f"{view_year}-{view_month:02d}-{d:02d}"
                has_event = ds in cal_data and any(
                    not e.get("done", False) for e in cal_data[ds]
                )

                # 如果是今天，高亮显示
                if d == today.day and view_month == today.month and view_year == today.year:
                    marker = "●" if has_event else "○"
                    line += f" {marker}{d:02d}  "
                elif has_event:
                    line += f" *{d:02d}  "
                else:
                    # 获取简短农历日
                    try:
                        lunar_day = lunar_day_short(view_year, view_month, d)
                        # 如果是初一，显示月份
                        if "初一" in lunar_day:
                            short = lunar_day[:2] if len(lunar_day) > 2 else lunar_day[0]
                        else:
                            parts = lunar_day.replace("廿", "廿").replace("初", "初")
                            short = ".."
                    except:
                        short = ""
                    line += f" {d:02d}  "

                day_num += 1

            print(f"  {line}")

        print(f"  {'─' * 42}")
        print(f"  ● 今天  * 有事项")
        print(f"  农历：{lunar_date_string(today.year, today.month, today.day)}")
        print(f"\n  {'=' * 44}")
        print(f"  [←] 上月  [→] 下月  [T] 回到今天")
        print(f"  [数字] 查看/编辑日期事项  [S] 给今天添加事项")
        print(f"  [B] 返回主页")
        print(f"  {'=' * 45}")

        cmd = input_safe().lower()

        if cmd == "b":
            break
        elif cmd == "t":
            view_year = today.year
            view_month = today.month
        elif cmd in ("left", "←", "a", "h"):
            view_month -= 1
            if view_month < 1:
                view_month = 12
                view_year -= 1
        elif cmd in ("right", "→", "d", "l"):
            view_month += 1
            if view_month > 12:
                view_month = 1
                view_year += 1
        elif cmd == "s":
            # 给今天添加事项
            ds = today_key()
            text = input_safe("事项内容：> ")
            if text:
                tm = input_safe("时间（可选，如 15:00，回车跳过）：> ")
                add_date_event(ds, text, tm)
                success("已添加")
                time.sleep(0.5)
        elif cmd.isdigit():
            # 查看/编辑某天的事项
            d = int(cmd)
            if 1 <= d <= days_in_month:
                ds = f"{view_year}-{view_month:02d}-{d:02d}"
                date_detail_screen(ds, view_year, view_month, d)


def date_detail_screen(date_str, year, month, day):
    """某天的事项详情"""
    while True:
        events = get_date_events(date_str)
        lunar_day_str = lunar_date_string(year, month, day)

        clear()
        header(f"第一步 · 日历")

        day_name = "星期" + ["一", "二", "三", "四", "五", "六", "日"][date(year, month, day).weekday()]
        print(f"\n  [CAL] {year}年{month}月{day}日 {day_name}")
        print(f"  农历：{lunar_day_str}")
        print(f"  {SEP}")

        if events:
            for i, e in enumerate(events, 1):
                done_mark = "[DONE]" if e.get("done") else "[ ]"
                time_str = f" [{e['time']}]" if e.get("time") else ""
                print(f"  {i}. {done_mark} {e['text']}{time_str}")
        else:
            print(f"  （没有事项）")

        print(f"\n  {'=' * 44}")
        print(f"  [A] 添加  [D] 删除  [空格] 切换完成状态")
        print(f"  [B] 返回日历")
        print(f"  {'=' * 45}")

        cmd = input_safe().lower()

        if cmd == "b":
            break
        elif cmd == "a":
            text = input_safe("事项内容：> ")
            if text:
                tm = input_safe("时间（可选）：> ")
                add_date_event(date_str, text, tm)
                success("已添加")
                time.sleep(0.3)
        elif cmd == "d":
            if events:
                try:
                    idx = int(input_safe(f"删除第几个？(1-{len(events)}) > ")) - 1
                    remove_date_event(date_str, idx)
                    success("已删除")
                    time.sleep(0.3)
                except (ValueError, IndexError):
                    pass
        elif cmd == " ":
            if events:
                try:
                    idx = int(input_safe(f"切换第几个？(1-{len(events)}) > ")) - 1
                    toggle_date_event(date_str, idx)
                    time.sleep(0.3)
                except (ValueError, IndexError):
                    pass


# ======================== 主界面 ========================

def main_screen():
    """主界面"""
    while True:
        clear()
        header("第一步")

        # 连续天数
        streak = get_streak()
        week_done = get_week_completion()
        today = date.today()
        day_names = ["一", "二", "三", "四", "五", "六", "日"]
        day_str = f"{today.year}-{today.month:02d}-{today.day:02d} 星期{day_names[today.weekday()]}"

        print(f"  [H] 连续坚持：{streak['current']} 天    本周：{week_done}/7     {day_str}")

        # 今日提醒
        show_today_reminders()

        # 主线任务
        td = get_today_task()
        task = td["task"]
        print()
        print(f"  今日主线：")
        print(f"  +{'-' * 43}+")
        status_icons = {"pending": "[...] 未开始", "done": "[DONE] 已完成"}
        status = status_icons.get(task["status"], "[...] 未开始")
        print(f"  | [T] {task['title']:<38}|")
        print(f"  | [G] {task['count']} {task['unit']}  [C] 预计 {task['estimated_minutes']} 分钟       |")
        if task.get("actual_minutes"):
            print(f"  |  实际用时：{task['actual_minutes']} 分钟                       |")
        print(f"  |  状态：{status:<37}|")
        print(f"  +{'-' * 43}+")

        # 今日待办
        todos = td.get("todos", [])
        print()
        if todos:
            print(f"  今日待办：")
            for i, t in enumerate(todos, 1):
                done_mark = "[DONE]" if t.get("done") else "[ ]"
                mins = t.get("minutes", 15)
                print(f"    {i}. {done_mark} {t['text']:<25} [{mins}min]")
        else:
            print(f"  今日待办：（空，按 [A] 添加）")

        print(f"\n  {'=' * 44}")
        # 第一行操作
        menu_item("S", "开始主线（专注计时）")
        menu_item("E", "编辑主线任务")
        menu_item("N", "换一个主线")
        print()
        # 第二行操作
        if todos:
            print(f"  [1-{len(todos)}] 勾选/取消待办", end="    ")
        menu_item("A", "添加待办")
        print()
        # 第三行
        menu_item("C", "捕获池（全部）")
        menu_item("L", "灵感 & 琐事")
        menu_item("K", "日历")
        menu_item("R", "回顾历史")
        print(f"  [Q] 退出")
        print(f"  {'=' * 45}")

        cmd = input_safe().lower()

        # 分发命令
        if cmd == "q":
            print()
            emph("再见，今天辛苦了。")
            print()
            break
        elif cmd == "s":
            # 开始专注
            actual_min, note = focus_timer(task["title"], task.get("estimated_minutes", DEFAULT_FOCUS_MINUTES))
            # 标记完成
            task["status"] = "done"
            task["actual_minutes"] = actual_min
            update_main_task(task)
            # 更新连续天数
            new_streak = update_streak()
            # 保存日志
            save_daily_entry({
                "main_done": True,
                "main_minutes": actual_min,
            })
            if note:
                add_review(note, "focus")
            success(f"主线完成！连续坚持 {new_streak} 天")
            time.sleep(1.5)
        elif cmd == "e":
            edit_main_task()
        elif cmd == "n":
            change_main_task()
        elif cmd == "a":
            add_todo()
        elif cmd == "c":
            capture_pool_screen()
        elif cmd == "l":
            inspiration_quick_view()
        elif cmd == "k":
            calendar_screen()
        elif cmd == "r":
            review_history()
        elif cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(todos):
                todos[idx]["done"] = not todos[idx].get("done", False)
                update_todos(todos)
                success("已更新" if todos[idx]["done"] else "已取消完成")
                time.sleep(0.3)


# ======================== 主线任务编辑 ========================

def edit_main_task():
    """编辑主线任务的参数"""
    td = get_today_task()
    task = td["task"]

    print()
    info(f"当前主线：{task['title']}")
    print()

    # 标题
    new_title = input_safe(f"任务名（回车保留「{task['title']}」）：> ")
    if new_title:
        task["title"] = new_title

    # 数量
    new_count = input_safe(f"数量（回车保留 {task['count']}）：> ")
    if new_count:
        try:
            task["count"] = int(new_count)
        except ValueError:
            pass

    # 单位
    new_unit = input_safe(f"单位（回车保留「{task['unit']}」）：> ")
    if new_unit:
        task["unit"] = new_unit

    # 预计时间
    new_time = input_safe(f"预计时间/分钟（回车保留 {task['estimated_minutes']}）：> ")
    if new_time:
        try:
            task["estimated_minutes"] = int(new_time)
        except ValueError:
            pass

    update_main_task(task)
    success("主线任务已更新")
    time.sleep(0.8)


def change_main_task():
    """更换主线任务（从待办池选一个，或手动输入）"""
    pool = get_capture_pool()
    todo_items = pool.get(POOL_TODO, [])

    clear()
    header("第一步 · 换主线")

    if todo_items:
        info("从待办池中选一个：")
        print()
        for i, item in enumerate(todo_items, 1):
            print(f"  [{i}] {item['text']}")
        print(f"  [M] 手动输入新任务")
        print(f"  [B] 返回")

        cmd = input_safe().lower()
        if cmd == "b":
            return
        elif cmd == "m":
            text = input_safe("新任务：> ")
            if text:
                td = get_today_task()
                td["task"]["title"] = text
                td["task"]["status"] = "pending"
                td["task"]["actual_minutes"] = None
                td["task"]["estimated_minutes"] = 15
                td["task"]["count"] = 1
                td["task"]["unit"] = "次"
                save_today_task(td)
                success("已更换主线任务")
                time.sleep(0.5)
        elif cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(todo_items):
                text = todo_items[idx]["text"]
                td = get_today_task()
                td["task"]["title"] = text
                td["task"]["status"] = "pending"
                td["task"]["actual_minutes"] = None
                td["task"]["estimated_minutes"] = 15
                td["task"]["count"] = 1
                td["task"]["unit"] = "次"
                save_today_task(td)
                remove_from_pool(POOL_TODO, idx)
                success(f"主线已切换为：{text}")
                time.sleep(1)
    else:
        info("待办池是空的，手动输入吧")
        text = input_safe("新任务：> ")
        if text:
            td = get_today_task()
            td["task"]["title"] = text
            td["task"]["status"] = "pending"
            td["task"]["actual_minutes"] = None
            save_today_task(td)
            success("已更换")
            time.sleep(0.5)


def add_todo():
    """添加今日待办"""
    td = get_today_task()
    todos = td.get("todos", [])

    if len(todos) >= MAX_TODOS_DISPLAY:
        warn(f"今日待办最多 {MAX_TODOS_DISPLAY} 个。请先完成或删除一些。")
        time.sleep(1.5)
        return

    clear()
    header("第一步 · 添加待办")

    # 选项：从待办池选，还是手动输入
    pool = get_capture_pool()
    pool_todos = pool.get(POOL_TODO, [])

    if pool_todos:
        info("从待办池选择（输入数字）或手动输入（输入 M）：")
        print()
        for i, item in enumerate(pool_todos[:10], 1):  # 显示前 10 个
            print(f"  [{i}] {item['text']}")
        print(f"  [M] 手动输入")
        print(f"  [B] 返回")

        cmd = input_safe().lower()
        if cmd == "b":
            return
        elif cmd == "m":
            text = input_safe("待办内容：> ")
            if text:
                mins = input_safe("预计时间（分钟，默认15）：> ")
                try:
                    minutes = int(mins) if mins else 15
                except ValueError:
                    minutes = 15
                todos.append({"text": text, "done": False, "minutes": minutes})
                update_todos(todos)
                success("已添加")
                time.sleep(0.5)
        elif cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(pool_todos):
                text = pool_todos[idx]["text"]
                mins = input_safe("预计时间（分钟，默认15）：> ")
                try:
                    minutes = int(mins) if mins else 15
                except ValueError:
                    minutes = 15
                todos.append({"text": text, "done": False, "minutes": minutes})
                update_todos(todos)
                remove_from_pool(POOL_TODO, idx)
                success(f"「{text}」已添加到今日待办")
                time.sleep(0.8)
    else:
        text = input_safe("待办内容：> ")
        if text:
            mins = input_safe("预计时间（分钟，默认15）：> ")
            try:
                minutes = int(mins) if mins else 15
            except ValueError:
                minutes = 15
            todos.append({"text": text, "done": False, "minutes": minutes})
            update_todos(todos)
            success("已添加")
            time.sleep(0.5)


def review_history():
    """查看历史回顾"""
    clear()
    header("第一步 · 回顾历史")

    reviews = get_reviews()
    if reviews:
        # 显示最近 20 条
        for r in reviews[-20:]:
            print(f"  [CAL] {r['date']}")
            print(f"     {r['text']}")
            if r.get("mood"):
                print(f"     心情：{r['mood']}")
            print()
    else:
        info("还没有回顾记录。")
        info("当你完成主线任务后，可以在这里写一句话记录。")
        print()

    info("写一条新的回顾：")
    text = input_safe("> ")
    if text:
        mood = input_safe("今日心情（可选）：> ")
        add_review(text, mood)
        success("已保存")
        time.sleep(0.5)

    print()
    input_safe("按回车返回...")


# ======================== 启动 ========================

def main():
    """程序入口"""
    # 今天第一次打开 -> 起床助手
    td_data = get_today_task()
    is_first_open_today = td_data.get("date") != today_key()

    if is_first_open_today and not SKIP_MORNING:
        # 先做回顾检查
        daily_review_check()
        # 起床助手
        morning_kick()
    elif is_first_open_today:
        daily_review_check()

    # 进入主界面
    main_screen()


if __name__ == "__main__":
    main()
