"""
第一步 - 桌面版 (1080p)
PySide6 原生 GUI，暗色暖金主题，大字体
"""

import sys, os, random
from datetime import date, timedelta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QLineEdit, QTextEdit, QDialog,
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QPoint, Property, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QRadialGradient, QConicalGradient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_manager import (
    today_key, get_streak, update_streak, get_week_completion,
    get_today_task, save_today_task,
    get_capture_pool, save_capture_pool, add_to_pool,
    remove_from_pool,
    get_calendar_data, get_date_events, add_date_event,
    get_today_reminders,
    get_reviews, add_review, get_daily_log, save_daily_entry,
    get_daily_habits, save_daily_habits, add_daily_habit, remove_daily_habit,
    auto_populate_daily_habits,
)
from lunar import lunar_date_string, solar_days_in_month

# ======== DESIGN TOKENS (1080p) ========
class T:
    BG = "#1a1a1a"
    CARD = "#252525"
    ELEVATED = "#2e2e2e"
    GOLD = "#d4a853"
    GOLD_DIM = "#b8923a"
    CORAL = "#c97d60"
    TEXT = "#e8e0d5"
    TEXT_DIM = "#8a8078"
    TEXT_MUTED = "#5c5650"
    SAGE = "#7b9b6a"
    DIVIDER = "#33302b"
    FONT_DISPLAY = "Noto Serif SC"
    FONT_BODY = "Noto Sans SC"
    RADIUS = 16
    RADIUS_LG = 24

    # Sizing (1080p)
    BASE_FONT = 17
    H1 = 38
    H2 = 28
    H3 = 18
    BODY = 17
    CAPTION = 14
    SMALL = 13
    BTN_FONT = 20
    BTN_FONT_SMALL = 16
    CARD_PAD = 28
    PAGE_MARGIN = 32
    PAGE_SPACING = 20


# Theme presets
THEMES = {
    "暖金": {"BG":"#1a1a1a","CARD":"#252525","ELEVATED":"#2e2e2e","GOLD":"#d4a853","GOLD_DIM":"#b8923a","CORAL":"#c97d60","TEXT":"#e8e0d5","TEXT_DIM":"#8a8078","TEXT_MUTED":"#5c5650","SAGE":"#7b9b6a","DIVIDER":"#33302b"},
    "日初": {"BG":"#f5f0e8","CARD":"#ffffff","ELEVATED":"#f0ebe0","GOLD":"#b8860b","GOLD_DIM":"#8b6508","CORAL":"#c06040","TEXT":"#2a2218","TEXT_DIM":"#6b5c48","TEXT_MUTED":"#9b8c78","SAGE":"#5b8040","DIVIDER":"#e0d8c8"},
}
_current_theme = "暖金"

def apply_theme(name):
    global _current_theme
    if name not in THEMES: return
    _current_theme = name
    for k,v in THEMES[name].items(): setattr(T, k, v)


def qss():
    return f"""
    QMainWindow {{ background: {T.BG}; }}
    QLabel {{ color: {T.TEXT}; }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{ width: 0; }}
    QLineEdit, QTextEdit {{
        background: {T.BG}; border: 1px solid {T.DIVIDER};
        border-radius: 12px; padding: 14px 18px;
        font-size: {T.BODY}px; color: {T.TEXT};
    }}
    QLineEdit:focus, QTextEdit:focus {{ border-color: {T.GOLD}; }}
    """


# ======== CUSTOM WIDGETS ========

class _FadeWidget(QWidget):
    """A solid overlay that can fade out using its own paintEvent.
    No QGraphicsEffect needed - 100% reliable."""
    def __init__(self, parent, color):
        super().__init__(parent)
        self._color = QColor(color)
        self._alpha = 255

    def setAlpha(self, a):
        self._alpha = max(0, min(255, a))
        self.update()

    alpha = Property(int, lambda s: s._alpha, setAlpha)

    def fade_out(self):
        self._anim = QPropertyAnimation(self, b"alpha")
        self._anim.setDuration(150)
        self._anim.setStartValue(220)
        self._anim.setEndValue(0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()

    def paintEvent(self, e):
        p = QPainter(self)
        c = QColor(self._color)
        c.setAlpha(self._alpha)
        p.fillRect(self.rect(), c)


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            background: {T.CARD}; border: 1px solid {T.DIVIDER};
            border-radius: {T.RADIUS_LG}px; padding: {T.CARD_PAD}px;
        """)


class GoldBtn(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {T.GOLD}; color: {T.BG}; border: none;
                border-radius: 50px; padding: 16px 36px;
                font-size: {T.BTN_FONT}px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {T.GOLD_DIM}; }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)


class GhostBtn(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        tc = QColor(T.TEXT); tc.setAlpha(13)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {T.TEXT_DIM}; border: none;
                border-radius: 50px; padding: 14px 28px;
                font-size: {T.BTN_FONT_SMALL}px;
            }}
            QPushButton:hover {{ color: {T.TEXT}; background: rgba({tc.red()},{tc.green()},{tc.blue()},0.05); }}
            QPushButton:pressed {{ color: {T.GOLD}; }}
        """)


class NavBtn(QPushButton):
    def __init__(self, icon, label, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setFixedSize(150, 90)
        self.setText(f"{icon}\n{label}")
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {T.TEXT_MUTED}; border: none;
                border-radius: 16px; font-size: {T.BODY}px; font-weight: 500;
            }}
            QPushButton:hover {{ color: {T.TEXT_DIM}; }}
            QPushButton:checked {{ color: {T.GOLD}; font-weight: 700; font-size: {T.BODY+1}px; }}
        """)


class TodoWidget(QFrame):
    toggled = Signal(int)

    def __init__(self, index, text, done=False, minutes=15, parent=None):
        super().__init__(parent)
        self.idx = index
        self._done = done
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(64)
        self.update_style()

    def update_style(self):
        self.setStyleSheet(f"""
            TodoWidget {{ background: {T.CARD}; border: 1px solid {T.DIVIDER}; border-radius: {T.RADIUS}px; }}
            TodoWidget:hover {{ border-color: {T.TEXT_MUTED}; }}
        """)

    def mousePressEvent(self, e):
        self._done = not self._done
        self.update_style()
        self.toggled.emit(self.idx)
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = 36, self.height() // 2
        r = 14
        if self._done:
            p.setBrush(QBrush(QColor(T.SAGE)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPoint(cx, cy), r, r)
            p.setPen(QPen(QColor(T.BG), 3))
            p.drawLine(cx-5, cy, cx-2, cy+3)
            p.drawLine(cx-2, cy+3, cx+5, cy-5)
        else:
            p.setPen(QPen(QColor(T.TEXT_MUTED), 2))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPoint(cx, cy), r, r)

        p.setPen(QColor(T.TEXT if not self._done else T.TEXT_MUTED))
        font = QFont(T.FONT_BODY, T.BODY)
        p.setFont(font)
        text_rect = QRectF(62, 0, self.width()-140, self.height())
        if self._done:
            f = p.font(); f.setStrikeOut(True); p.setFont(f)
        p.drawText(text_rect, Qt.AlignVCenter, self.property("todo_text") or "")

        mins = self.property("todo_minutes") or "15"
        p.setPen(QColor(T.TEXT_MUTED))
        font2 = QFont(T.FONT_BODY, T.SMALL)
        p.setFont(font2)
        p.drawText(QRectF(self.width()-80, 0, 70, self.height()), Qt.AlignVCenter, f"{mins}min")


class TimerRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(440, 440)
        self._progress = 0.0

    def setProgress(self, pct):
        self._progress = max(0.0, min(1.0, pct))
        self.update()

    progress = Property(float, lambda self: self._progress, setProgress)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width()/2, self.height()/2
        r = 160

        gcol = QColor(T.GOLD)
        glow = QRadialGradient(cx, cy, 220)
        glow.setColorAt(0, QColor(gcol.red(), gcol.green(), gcol.blue(), 35))
        glow.setColorAt(0.4, QColor(gcol.red(), gcol.green(), gcol.blue(), 10))
        glow.setColorAt(1, QColor(gcol.red(), gcol.green(), gcol.blue(), 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), 220, 220)

        p.setPen(QPen(QColor(T.ELEVATED), 6))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r, r)

        if self._progress > 0:
            gcol = QColor(T.GOLD); gmid = QColor(T.GOLD).lighter(120)
            grad = QConicalGradient(cx, cy, -90)
            grad.setColorAt(0, gcol)
            grad.setColorAt(0.5, gmid)
            grad.setColorAt(1, gcol)
            p.setPen(QPen(QBrush(grad), 6, Qt.SolidLine, Qt.RoundCap))
            span = int(self._progress * 360 * 16)
            p.drawArc(QRectF(cx-r, cy-r, r*2, r*2), 90*16, -span)


# ======== PAGES ========

class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        # 外层只放滚动区域
        page_lo = QVBoxLayout(self)
        page_lo.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(T.PAGE_MARGIN, 24, T.PAGE_MARGIN, 24)
        self.layout.setSpacing(T.PAGE_SPACING)

        scroll.setWidget(content)
        page_lo.addWidget(scroll)

        # 词芽词汇自动刷新定时器
        self._vocab_card = None
        self._vocab_data = {}
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_vocab)
        self._refresh_timer.start(3000)  # 每 3 秒刷新

        self.build()

    def build(self):
        _clear_layout(self.layout)

        # ── Header bar: date + streak + week track ──
        streak = get_streak(); week_done = get_week_completion()
        today = date.today()
        month_names = ["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"]
        day_names = ["周一","周二","周三","周四","周五","周六","周日"]

        header_card = QFrame()
        header_card.setStyleSheet(f"background:{T.CARD}; border:1px solid {T.DIVIDER}; border-radius:{T.RADIUS_LG}px;")
        hl = QHBoxLayout(header_card); hl.setContentsMargins(T.CARD_PAD, 20, T.CARD_PAD, 20); hl.setSpacing(24)

        # Left: date block
        date_block = QVBoxLayout(); date_block.setSpacing(0); date_block.setAlignment(Qt.AlignCenter)
        day_num = QLabel(str(today.day))
        day_num.setStyleSheet(f"font-family:'{T.FONT_DISPLAY}'; font-size:42px; font-weight:300; color:{T.TEXT};")
        day_num.setAlignment(Qt.AlignCenter)
        date_block.addWidget(day_num)
        month_label = QLabel(f"{month_names[today.month-1]} · {day_names[today.weekday()]}")
        month_label.setStyleSheet(f"font-size:{T.SMALL}px; color:{T.TEXT_DIM};")
        month_label.setAlignment(Qt.AlignCenter)
        date_block.addWidget(month_label)
        hl.addLayout(date_block)

        # Divider line
        div = QFrame(); div.setFrameShape(QFrame.VLine); div.setStyleSheet(f"color:{T.DIVIDER}; border:none; background:{T.DIVIDER};"); div.setFixedWidth(1)
        hl.addWidget(div)

        # Center: streak
        streak_block = QVBoxLayout(); streak_block.setSpacing(2)
        streak_num = QLabel(str(streak['current']))
        streak_num.setStyleSheet(f"font-family:'{T.FONT_DISPLAY}'; font-size:42px; font-weight:700; color:{T.GOLD};")
        streak_block.addWidget(streak_num)
        streak_label = QLabel("连续坚持")
        streak_label.setStyleSheet(f"font-size:{T.SMALL}px; color:{T.TEXT_DIM};")
        streak_block.addWidget(streak_label)
        hl.addLayout(streak_block)

        hl.addStretch()

        # Right: week progress track
        week_block = QVBoxLayout(); week_block.setSpacing(8)
        week_title = QLabel(f"本周 {week_done}/7")
        week_title.setStyleSheet(f"font-size:{T.SMALL}px; color:{T.TEXT_DIM};")
        week_title.setAlignment(Qt.AlignRight)
        week_block.addWidget(week_title)

        dots_layout = QHBoxLayout(); dots_layout.setSpacing(6)
        today_dow = today.weekday(); monday = today - timedelta(days=today_dow)
        log = get_daily_log()
        day_labels = ["一","二","三","四","五","六","日"]
        for i in range(7):
            d = (monday + timedelta(days=i)).isoformat()
            dot = QLabel(day_labels[i]); dot.setFixedSize(28,28); dot.setAlignment(Qt.AlignCenter)
            if i == today_dow:
                dot.setStyleSheet(f"background:{T.GOLD}; color:{T.BG}; border-radius:14px; font-size:11px; font-weight:700;")
            elif d in log and log[d].get("main_done"):
                dot.setStyleSheet(f"background:{T.SAGE}; color:{T.BG}; border-radius:14px; font-size:11px; font-weight:700;")
            else:
                dot.setStyleSheet(f"background:{T.ELEVATED}; color:{T.TEXT_MUTED}; border-radius:14px; font-size:11px;")
            dots_layout.addWidget(dot)
        week_block.addLayout(dots_layout)
        hl.addLayout(week_block)
        self.layout.addWidget(header_card)

        # ── Reminders ──
        reminders = get_today_reminders()
        active = [r for r in reminders if not r.get("done")]
        if active:
            rem_card = Card()
            coral_col = QColor(T.CORAL); coral_col.setAlpha(77)
            rem_card.setStyleSheet(rem_card.styleSheet().replace(T.DIVIDER, coral_col.name(QColor.HexArgb)))
            rl = QVBoxLayout(rem_card); rl.setContentsMargins(T.CARD_PAD, 16, T.CARD_PAD, 16); rl.setSpacing(6)
            title = QLabel("今日提醒")
            title.setStyleSheet(f"font-size:{T.CAPTION}px; color:{T.CORAL}; font-weight:700;")
            rl.addWidget(title)
            for r in active[:3]:
                t = r.get("time",""); txt = f"[{t}] {r['text']}" if t else r['text']
                item = QLabel(txt); item.setStyleSheet(f"font-size:{T.BODY}px; color:{T.TEXT_DIM};"); rl.addWidget(item)
            self.layout.addWidget(rem_card)

        # ── Main task card ──
        td = get_today_task(); task = td["task"]; is_done = task["status"] == "done"

        main_card = QFrame()
        border_color = "rgba(123,155,106,0.3)" if is_done else "rgba(212,168,83,0.25)"
        main_card.setObjectName("mainTaskCard")
        main_card.setStyleSheet(f"""
            QFrame#mainTaskCard {{ background:{T.CARD}; border:1px solid {border_color}; border-radius:{T.RADIUS_LG}px; }}
        """)
        ml = QVBoxLayout(main_card); ml.setContentsMargins(T.CARD_PAD, T.CARD_PAD, T.CARD_PAD, T.CARD_PAD); ml.setSpacing(10)

        badge = QLabel("已完成" if is_done else "今日主线")
        badge.setFixedWidth(140); badge.setAlignment(Qt.AlignCenter)
        g = QColor(T.GOLD)
        badge.setStyleSheet(f"font-size:{T.BODY}px; font-weight:700; color:{T.GOLD}; background:rgba({g.red()},{g.green()},{g.blue()},0.10); padding:10px 24px; border-radius:50px;")
        ml.addWidget(badge)

        title_l = QLabel(task["title"])
        title_l.setStyleSheet(f"font-family:'{T.FONT_DISPLAY}'; font-size:{T.H2}px; font-weight:500; margin-top:4px;")
        ml.addWidget(title_l)

        meta = QLabel(f"{task['count']} {task['unit']}  ·  预计 {task['estimated_minutes']} 分钟"
                      + (f"  ·  实际 {task['actual_minutes']} 分钟" if task.get("actual_minutes") else ""))
        meta.setStyleSheet(f"font-size:{T.BODY}px; color:{T.TEXT_DIM};")
        ml.addWidget(meta)

        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        if not is_done:
            sb = GoldBtn("开始专注"); sb.clicked.connect(lambda: self.window().show_timer())
            eb = GhostBtn("编辑"); eb.clicked.connect(lambda: self.edit_task())
            cb = GhostBtn("换一个"); cb.clicked.connect(lambda: self.change_task())
            btn_row.addWidget(sb); btn_row.addWidget(eb); btn_row.addWidget(cb)
        else:
            ab = GhostBtn("再做一次"); ab.clicked.connect(lambda: self.window().show_timer())
            rb = GhostBtn("重置"); rb.clicked.connect(lambda: self.reset_task())
            btn_row.addWidget(ab); btn_row.addWidget(rb)
        btn_row.addStretch(); ml.addLayout(btn_row)
        self.layout.addWidget(main_card)

        # ── 词芽词汇统计 ──
        self._build_vocab_section()

        # ── Daily Habits ──
        habits = get_daily_habits()
        habits_label = QLabel("每日习惯（每天自动加入待办）")
        habits_label.setStyleSheet(f"font-size:{T.SMALL}px; color:{T.TEXT_MUTED}; margin-top:8px;")
        self.layout.addWidget(habits_label)

        habits_row = QHBoxLayout(); habits_row.setSpacing(8)
        if habits:
            for i, h in enumerate(habits):
                h_w = QFrame()
                h_w.setStyleSheet(f"background:{T.ELEVATED}; border-radius:{T.RADIUS}px; padding:6px 12px;")
                h_lo = QHBoxLayout(h_w); h_lo.setContentsMargins(0,0,0,0); h_lo.setSpacing(6)
                h_lo.addWidget(QLabel(h["text"]))
                del_h = QPushButton("×"); del_h.setFixedSize(22,22); del_h.setCursor(Qt.PointingHandCursor)
                del_h.setStyleSheet(f"background:transparent; color:{T.TEXT_MUTED}; border:none; font-size:16px; border-radius:11px;")
                del_h.clicked.connect(lambda checked, idx=i: self.remove_habit(idx))
                h_lo.addWidget(del_h)
                habits_row.addWidget(h_w)
        else:
            no_habit = QLabel("还没有每日习惯"); no_habit.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:{T.SMALL}px;")
            habits_row.addWidget(no_habit)
        habits_row.addStretch()
        self.layout.addLayout(habits_row)

        add_habit_btn = GhostBtn("+ 添加每日习惯")
        add_habit_btn.clicked.connect(lambda: self.add_habit())
        self.layout.addWidget(add_habit_btn)

        # ── Todos ──
        todos_label = QLabel("今日待办")
        todos_label.setStyleSheet(f"font-size:{T.H3}px; color:{T.TEXT_DIM}; font-weight:500; margin-top:4px;")
        self.layout.addWidget(todos_label)

        todos = td.get("todos",[])
        if todos:
            for i, t in enumerate(todos):
                tw = TodoWidget(i, t["text"], t.get("done",False), t.get("minutes",15))
                tw.setProperty("todo_text", t["text"]); tw.setProperty("todo_minutes", str(t.get("minutes",15)))
                tw.toggled.connect(self.toggle_todo); self.layout.addWidget(tw)
        else:
            empty = QLabel("还没有待办，开始添加吧")
            empty.setStyleSheet(f"font-size:{T.BODY}px; color:{T.TEXT_MUTED}; padding:24px;"); empty.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(empty)

        add_btn = GhostBtn("+ 添加待办"); add_btn.clicked.connect(lambda: self.add_todo())
        self.layout.addWidget(add_btn)
        self.layout.addStretch()

    # ── Actions ──
    def add_habit(self):
        dlg = QDialog(self.window()); dlg.setWindowTitle("添加每日习惯"); dlg.setFixedSize(500, 240)
        dlg.setStyleSheet(f"background:{T.CARD}; border-radius:{T.RADIUS_LG}px;")
        lo = QVBoxLayout(dlg); lo.setSpacing(12)
        t1 = QLineEdit(); t1.setPlaceholderText("习惯内容（如：背10个单词）"); lo.addWidget(t1)
        t2 = QLineEdit(); t2.setPlaceholderText("预计分钟（默认15）"); lo.addWidget(t2)
        br = QHBoxLayout(); c2=GhostBtn("取消"); c2.clicked.connect(dlg.reject); o2=GoldBtn("添加"); o2.clicked.connect(dlg.accept)
        br.addStretch(); br.addWidget(c2); br.addWidget(o2); lo.addLayout(br)
        if dlg.exec() == QDialog.Accepted:
            text = t1.text().strip()
            if text:
                try: mins = int(t2.text()) if t2.text().strip() else 15
                except: mins = 15
                add_daily_habit(text, mins); self.rebuild()

    def remove_habit(self, idx):
        remove_daily_habit(idx); self.rebuild()

    def toggle_todo(self, idx):
        td = get_today_task(); td["todos"][idx]["done"] = not td["todos"][idx].get("done",False)
        save_today_task(td); self.rebuild()

    def add_todo(self):
        dlg = QDialog(self.window()); dlg.setWindowTitle("添加待办"); dlg.setFixedSize(560, 280)
        dlg.setStyleSheet(f"background:{T.CARD}; border-radius:{T.RADIUS_LG}px;")
        lo = QVBoxLayout(dlg); lo.setSpacing(12)
        t1 = QLineEdit(); t1.setPlaceholderText("待办内容..."); lo.addWidget(t1)
        t2 = QLineEdit(); t2.setPlaceholderText("预计分钟（默认15）"); lo.addWidget(t2)
        br = QHBoxLayout(); c2=GhostBtn("取消"); c2.clicked.connect(dlg.reject); o2=GoldBtn("添加"); o2.clicked.connect(dlg.accept)
        br.addStretch(); br.addWidget(c2); br.addWidget(o2); lo.addLayout(br)
        if dlg.exec() == QDialog.Accepted:
            text = t1.text().strip()
            if text:
                try: mins = int(t2.text()) if t2.text().strip() else 15
                except: mins = 15
                td = get_today_task()
                if len(td["todos"]) >= 3: return
                td["todos"].append({"text":text,"done":False,"minutes":mins}); save_today_task(td); self.rebuild()

    def edit_task(self):
        td = get_today_task(); t = td["task"]
        dlg = QDialog(self.window()); dlg.setWindowTitle("编辑主线任务"); dlg.setFixedSize(560, 380)
        dlg.setStyleSheet(f"background:{T.CARD}; border-radius:{T.RADIUS_LG}px;")
        lo = QVBoxLayout(dlg); lo.setSpacing(12)
        inputs = {}
        for key,label,val in [("title","任务名",t["title"]),("count","数量",str(t["count"])),("unit","单位",t["unit"]),("mins","预计分钟",str(t["estimated_minutes"]))]:
            inp = QLineEdit(); inp.setPlaceholderText(label); inp.setText(val); lo.addWidget(inp); inputs[key]=inp
        br = QHBoxLayout(); c2=GhostBtn("取消"); c2.clicked.connect(dlg.reject); o2=GoldBtn("保存"); o2.clicked.connect(dlg.accept)
        br.addStretch(); br.addWidget(c2); br.addWidget(o2); lo.addLayout(br)
        if dlg.exec() == QDialog.Accepted:
            nt=inputs["title"].text().strip();
            if nt: t["title"]=nt
            try: t["count"]=int(inputs["count"].text())
            except: pass
            nu=inputs["unit"].text().strip();
            if nu: t["unit"]=nu
            try: t["estimated_minutes"]=int(inputs["mins"].text())
            except: pass
            save_today_task(td); self.rebuild()

    def change_task(self):
        dlg = QDialog(self.window()); dlg.setWindowTitle("更换主线任务"); dlg.setFixedSize(560, 260)
        dlg.setStyleSheet(f"background:{T.CARD}; border-radius:{T.RADIUS_LG}px;")
        lo = QVBoxLayout(dlg); lo.setSpacing(12)
        inp = QLineEdit(); inp.setPlaceholderText("输入新任务名..."); lo.addWidget(inp)
        br = QHBoxLayout(); c2=GhostBtn("取消"); c2.clicked.connect(dlg.reject); o2=GoldBtn("更换"); o2.clicked.connect(dlg.accept)
        br.addStretch(); br.addWidget(c2); br.addWidget(o2); lo.addLayout(br)
        if dlg.exec() == QDialog.Accepted:
            text = inp.text().strip()
            if text:
                td = get_today_task(); td["task"]["title"]=text; td["task"]["status"]="pending"
                td["task"]["actual_minutes"]=None; td["task"]["estimated_minutes"]=15
                td["task"]["count"]=1; td["task"]["unit"]="次"; save_today_task(td); self.rebuild()

    def reset_task(self):
        td = get_today_task(); td["task"]["status"]="pending"; td["task"]["actual_minutes"]=None
        save_today_task(td); self.rebuild()

    def rebuild(self): self.build()

    # ── 词芽词汇同步 ──

    def _build_vocab_section(self):
        """在仪表盘上创建词芽词汇统计卡片"""
        self._vocab_card = QFrame()
        self._vocab_card.setObjectName("vocabCard")
        self._vocab_card.setStyleSheet(f"""
            QFrame#vocabCard {{
                background: {T.CARD};
                border: 1px solid {T.DIVIDER};
                border-radius: {T.RADIUS_LG}px;
            }}
        """)
        card_lo = QVBoxLayout(self._vocab_card)
        card_lo.setContentsMargins(T.CARD_PAD, 16, T.CARD_PAD, 16)
        card_lo.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("🌱 词芽 · 词汇积累")
        title.setStyleSheet(f"font-size:{T.BODY}px; font-weight:700; color:{T.GOLD};")
        header.addWidget(title)
        header.addStretch()
        self._vocab_refresh_lbl = QLabel("")
        self._vocab_refresh_lbl.setStyleSheet(f"font-size:{T.SMALL}px; color:{T.TEXT_MUTED};")
        header.addWidget(self._vocab_refresh_lbl)
        card_lo.addLayout(header)

        # 统计数字行
        stats_row = QHBoxLayout()
        stats_row.setSpacing(24)

        self._vocab_stat_total = self._make_stat_label("📚 累计", "0")
        self._vocab_stat_today = self._make_stat_label("➕ 今日新增", "0")
        self._vocab_stat_reviewed = self._make_stat_label("🔄 今日复习", "0")
        self._vocab_stat_dialogues = self._make_stat_label("💬 生成对话", "0")

        stats_row.addWidget(self._vocab_stat_total)
        stats_row.addWidget(self._vocab_stat_today)
        stats_row.addWidget(self._vocab_stat_reviewed)
        stats_row.addWidget(self._vocab_stat_dialogues)
        stats_row.addStretch()
        card_lo.addLayout(stats_row)

        self.layout.addWidget(self._vocab_card)
        self._refresh_vocab()

    def _make_stat_label(self, label_text, value_text):
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(2)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"font-size:{T.SMALL}px; color:{T.TEXT_MUTED};")
        lo.addWidget(lbl)
        val = QLabel(value_text)
        val.setStyleSheet(f"font-size:{T.H2}px; font-weight:700; color:{T.TEXT};")
        lo.addWidget(val)
        return w

    def _refresh_vocab(self):
        """从 daily_log 读取词芽数据并更新卡片"""
        if not self._vocab_card:
            return
        try:
            log = get_daily_log()
            td = log.get(today_key(), {})
            new_data = {
                "total": td.get("vocab_total", 0),
                "added": td.get("vocab_added", 0),
                "reviewed": td.get("vocab_reviewed", 0),
                "dialogues": td.get("vocab_dialogues", 0),
            }
            # 只在数据变化时更新 UI
            if new_data != self._vocab_data:
                self._vocab_data = new_data
                self._vocab_stat_total.findChildren(QLabel)[1].setText(str(new_data["total"]))
                self._vocab_stat_today.findChildren(QLabel)[1].setText(str(new_data["added"]))
                self._vocab_stat_reviewed.findChildren(QLabel)[1].setText(str(new_data["reviewed"]))
                self._vocab_stat_dialogues.findChildren(QLabel)[1].setText(str(new_data["dialogues"]))
                # 刷新时间戳
                from datetime import datetime
                ts = datetime.now().strftime("%H:%M:%S")
                self._vocab_refresh_lbl.setText(f"已同步 {ts}")
        except Exception:
            pass  # 静默失败，不影响主流程


def _clear_layout(lo):
    """Recursively clear all widgets from a layout"""
    while lo.count():
        item = lo.takeAt(0)
        w = item.widget()
        if w is not None:
            w.hide()
            w.deleteLater()
        elif item.layout() is not None:
            _clear_layout(item.layout())


class TimerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_seconds = 0; self.remaining = 0; self.running = False; self.paused = False
        self.task_name = ""
        self.tick_timer = QTimer(self); self.tick_timer.timeout.connect(self.tick)
        self.build()

    def build(self):
        # Clear old layout if exists
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w: w.deleteLater()
                elif item.layout():
                    while item.layout().count():
                        si = item.layout().takeAt(0)
                        sw = si.widget()
                        if sw: sw.deleteLater()
            del old
        lo = QVBoxLayout(self)
        lo.setContentsMargins(T.PAGE_MARGIN, 60, T.PAGE_MARGIN, 60); lo.setSpacing(0)

        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"font-size:{T.H3}px; color:{T.TEXT_DIM}; margin-bottom:32px;")
        lo.addWidget(self.title_label)

        self.ring = TimerRing()
        rc = QHBoxLayout(); rc.addStretch(); rc.addWidget(self.ring); rc.addStretch()
        lo.addLayout(rc)

        self.time_label = QLabel("15:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet(f"font-family:'{T.FONT_DISPLAY}'; font-size:72px; font-weight:200; color:{T.TEXT}; margin-top:-260px;")
        self.time_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        lo.addWidget(self.time_label)
        lo.addSpacing(60)

        self.btn_layout = QHBoxLayout(); self.btn_layout.setSpacing(16); self.btn_layout.addStretch()
        lo.addLayout(self.btn_layout)

        self.start_btn = GoldBtn("开始"); self.start_btn.clicked.connect(self.start); self.btn_layout.addWidget(self.start_btn)
        self.pause_btn = GhostBtn("暂停"); self.pause_btn.clicked.connect(self.pause); self.pause_btn.hide(); self.btn_layout.addWidget(self.pause_btn)
        self.resume_btn = GoldBtn("继续"); self.resume_btn.clicked.connect(self.resume); self.resume_btn.hide(); self.btn_layout.addWidget(self.resume_btn)
        self.stop_btn = GhostBtn("结束"); self.stop_btn.clicked.connect(self.stop); self.stop_btn.hide(); self.btn_layout.addWidget(self.stop_btn)
        self.btn_layout.addStretch()
        lo.addStretch()

        back_btn = GhostBtn("返回"); back_btn.clicked.connect(lambda: self.window().show_page(0))
        lo.addWidget(back_btn, alignment=Qt.AlignCenter)

    def setup(self, task_name, minutes=15):
        self.task_name = task_name; self.total_seconds = minutes*60; self.remaining = self.total_seconds
        self.running = False; self.paused = False
        self.title_label.setText(task_name); self.ring.setProgress(0); self.update_display()
        self.start_btn.show(); self.pause_btn.hide(); self.resume_btn.hide(); self.stop_btn.hide()

    def update_display(self):
        m = self.remaining//60; s = self.remaining%60
        self.time_label.setText(f"{m:02d}:{s:02d}")
        pct = (self.total_seconds-self.remaining)/self.total_seconds if self.total_seconds>0 else 0
        self.ring.setProgress(pct)

    def start(self):
        if self.total_seconds<=0: return
        self.running=True; self.paused=False; self.start_btn.hide(); self.pause_btn.show(); self.stop_btn.show()
        self.tick_timer.start(200)

    def tick(self):
        if self.paused: return
        self.remaining = max(0, self.remaining-0.2); self.update_display()
        if self.remaining<=0: self.complete()

    def pause(self):
        self.paused=True; self.pause_btn.hide(); self.resume_btn.show()

    def resume(self):
        self.paused=False; self.resume_btn.hide(); self.pause_btn.show()

    def stop(self):
        self.tick_timer.stop()
        actual = round((self.total_seconds-self.remaining)/60,1)
        td=get_today_task(); td["task"]["status"]="done"; td["task"]["actual_minutes"]=actual
        save_today_task(td); update_streak()
        self.window().on_nav(0); self.window().toast(f"专注完成！实际用时 {actual} 分钟")

    def complete(self):
        self.tick_timer.stop(); self.remaining=0; self.update_display()
        actual = round(self.total_seconds/60,1)
        td=get_today_task(); td["task"]["status"]="done"; td["task"]["actual_minutes"]=actual
        save_today_task(td); update_streak()
        QTimer.singleShot(600, lambda: self.window().on_nav(0))
        self.window().toast("时间到！任务完成")


class CapturePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tab = "todo"
        lo = QVBoxLayout(self); lo.setContentsMargins(T.PAGE_MARGIN,24,T.PAGE_MARGIN,24); lo.setSpacing(16)
        self._layout = lo; self.build()

    def build(self):
        _clear_layout(self._layout)

        title = QLabel("捕获池")
        title.setStyleSheet(f"font-family:'{T.FONT_DISPLAY}'; font-size:{T.H1}px; font-weight:600; margin-bottom:4px;")
        self._layout.addWidget(title)

        tabs = QHBoxLayout(); tabs.setSpacing(8)
        tab_defs = [("todo","待办"), ("inspiration","灵感"), ("errand","琐事")]
        for key,label in tab_defs:
            active = key==self.current_tab
            btn = QPushButton(label); btn.setCheckable(True); btn.setChecked(active); btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ background:{T.ELEVATED if active else T.CARD}; color:{T.TEXT if active else T.TEXT_DIM};
                    border:none; border-radius:50px; padding:14px 28px; font-size:{T.BTN_FONT_SMALL}px; font-weight:500; }}
                QPushButton:hover {{ background:{T.ELEVATED}; color:{T.TEXT}; }}
            """)
            btn.clicked.connect(lambda checked, k=key: self.switch_tab(k))
            tabs.addWidget(btn)
        self._layout.addLayout(tabs)

        self.input_field = QLineEdit(); self.input_field.setPlaceholderText("输入新内容，回车添加...")
        self.input_field.returnPressed.connect(self.add_item); self._layout.addWidget(self.input_field)

        self.items_container = QVBoxLayout(); self.items_container.setSpacing(6)
        self._layout.addLayout(self.items_container)

        pool = get_capture_pool(); items = pool.get(self.current_tab,[])
        if items:
            for i, item in enumerate(items): self.add_item_widget(item,i)
        else:
            empty = QLabel("空的，添加点什么吧"); empty.setStyleSheet(f"color:{T.TEXT_MUTED}; padding:32px; font-size:{T.BODY}px;"); empty.setAlignment(Qt.AlignCenter)
            self.items_container.addWidget(empty)
        self._layout.addStretch()

    def switch_tab(self, key): self.current_tab=key; self.build()

    def add_item_widget(self, item, idx):
        # Wrap each item in a proper QWidget to prevent visual overlap
        wrapper = QWidget()
        wrapper.setStyleSheet(f"background:{T.CARD}; border-radius:{T.RADIUS}px; padding:8px 0;")
        row = QHBoxLayout(wrapper); row.setContentsMargins(16,10,16,10); row.setSpacing(12)
        label = QLabel(item["text"]); label.setStyleSheet(f"font-size:{T.BODY}px; color:{T.TEXT};"); row.addWidget(label); row.addStretch()
        if self.current_tab=="todo":
            move_btn = GhostBtn("拖到今日"); move_btn.clicked.connect(lambda checked, i=idx: self.move_to_today(i))
            row.addWidget(move_btn)
        del_btn = QPushButton("×"); del_btn.setFixedSize(36,36); del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(f"background:transparent; color:{T.TEXT_MUTED}; border:none; border-radius:18px; font-size:22px;")
        del_btn.clicked.connect(lambda checked, i=idx: self.delete_item(i))
        row.addWidget(del_btn)
        self.items_container.addWidget(wrapper)

    def add_item(self):
        text = self.input_field.text().strip()
        if text: add_to_pool(self.current_tab,text); self.input_field.clear(); self.build()

    def delete_item(self, idx): remove_from_pool(self.current_tab,idx); self.build()

    def move_to_today(self, idx):
        pool = get_capture_pool(); item = pool[self.current_tab][idx]; pool[self.current_tab].pop(idx); save_capture_pool(pool)
        td = get_today_task()
        if len(td["todos"])>=3: self.build(); self.window().toast("今日待办最多3个"); return
        td["todos"].append({"text":item["text"],"done":False,"minutes":15}); save_today_task(td); self.build()
        self.window().toast("已拖到今日待办")


class CalendarPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view_year = date.today().year; self.view_month = date.today().month
        lo = QVBoxLayout(self); lo.setContentsMargins(T.PAGE_MARGIN,24,T.PAGE_MARGIN,24); lo.setSpacing(12)
        self._layout = lo; self.build()

    def build(self):
        _clear_layout(self._layout)

        header = QHBoxLayout()
        pb = QPushButton("←"); pb.setFixedSize(48,48); pb.setCursor(Qt.PointingHandCursor)
        pb.setStyleSheet(f"background:transparent; color:{T.TEXT_DIM}; border:none; font-size:28px; border-radius:24px;")
        pb.clicked.connect(lambda: self.change_month(-1))
        title = QLabel(f"{self.view_year}年{self.view_month}月"); title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-family:'{T.FONT_DISPLAY}'; font-size:{T.H2}px; font-weight:500;")
        nb = QPushButton("→"); nb.setFixedSize(48,48); nb.setCursor(Qt.PointingHandCursor)
        nb.setStyleSheet(f"background:transparent; color:{T.TEXT_DIM}; border:none; font-size:28px; border-radius:24px;")
        nb.clicked.connect(lambda: self.change_month(1))
        header.addWidget(pb); header.addWidget(title,1); header.addWidget(nb)
        self._layout.addLayout(header)

        today = date.today(); lunar_str = lunar_date_string(today.year,today.month,today.day)
        li = QLabel(lunar_str); li.setAlignment(Qt.AlignCenter)
        li.setStyleSheet(f"font-size:{T.CAPTION}px; color:{T.TEXT_DIM};")
        self._layout.addWidget(li)

        days_h = QHBoxLayout()
        for d in ["一","二","三","四","五","六","日"]:
            lbl = QLabel(d); lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"font-size:{T.CAPTION}px; color:{T.TEXT_MUTED};")
            days_h.addWidget(lbl)
        self._layout.addLayout(days_h)

        cal_data = get_calendar_data()
        first_day = date(self.view_year,self.view_month,1); first_weekday = first_day.weekday()
        days_in_month = solar_days_in_month(self.view_year,self.view_month)

        day_num = 1
        for week in range(6):
            if day_num>days_in_month: break
            row = QHBoxLayout(); row.setSpacing(4)
            for wd in range(7):
                if week==0 and wd<first_weekday:
                    ph = QLabel(""); ph.setFixedSize(64,64); row.addWidget(ph); continue
                if day_num>days_in_month:
                    ph = QLabel(""); ph.setFixedSize(64,64); row.addWidget(ph); continue
                d = day_num
                ds = f"{self.view_year}-{self.view_month:02d}-{d:02d}"
                has_event = ds in cal_data and any(not e.get("done",False) for e in cal_data[ds])
                is_today = (d==today.day and self.view_month==today.month and self.view_year==today.year)
                day_btn = QPushButton(str(d)); day_btn.setFixedSize(64,64); day_btn.setCursor(Qt.PointingHandCursor)
                if is_today:
                    day_btn.setStyleSheet(f"background:{T.GOLD}; color:{T.BG}; border:none; border-radius:32px; font-weight:700; font-size:{T.BODY}px;")
                elif has_event:
                    coral_col2 = QColor(T.CORAL); coral_col2.setAlpha(102)
                    day_btn.setStyleSheet(f"background:transparent; color:{T.CORAL}; border:2px solid {coral_col2.name(QColor.HexArgb)}; border-radius:32px; font-size:{T.BODY}px;")
                else:
                    day_btn.setStyleSheet(f"background:transparent; color:{T.TEXT}; border:none; border-radius:32px; font-size:{T.BODY}px;")
                day_btn.clicked.connect(lambda checked, ds=ds: self.open_date(ds))
                row.addWidget(day_btn); day_num+=1
            self._layout.addLayout(row)
        self._layout.addStretch()

    def change_month(self, delta):
        self.view_month+=delta
        if self.view_month>12: self.view_month=1; self.view_year+=1
        elif self.view_month<1: self.view_month=12; self.view_year-=1
        self.build()

    def open_date(self, ds):
        dlg = QDialog(self.window()); dlg.setWindowTitle(ds); dlg.setFixedSize(600, 480)
        dlg.setStyleSheet(f"background:{T.CARD}; border-radius:{T.RADIUS_LG}px;")
        lo = QVBoxLayout(dlg); lo.setSpacing(10); lo.setContentsMargins(24,20,24,20)

        parts = ds.split("-"); y,m,d = int(parts[0]),int(parts[1]),int(parts[2])
        lunar_str = lunar_date_string(y,m,d)
        header_lbl = QLabel(f"{ds}  ·  {lunar_str}")
        header_lbl.setStyleSheet(f"font-size:{T.H3}px; color:{T.TEXT_DIM};"); lo.addWidget(header_lbl)

        # Scrollable events area
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("border:none; background:transparent;")
        scroll_w = QWidget(); scroll_w.setStyleSheet("background:transparent;"); svl = QVBoxLayout(scroll_w); svl.setSpacing(6); svl.setContentsMargins(0,0,0,0)
        events = get_date_events(ds)
        if events:
            for i, e in enumerate(events):
                ew = QWidget(); ew.setStyleSheet("background:transparent;")
                row = QHBoxLayout(ew); row.setContentsMargins(0,4,0,4); row.setSpacing(10)
                mark = "[DONE]" if e.get("done") else "[  ]"
                t_str = f"  [{e['time']}]" if e.get("time") else ""
                row.addWidget(QLabel(f"{mark} {e['text']}{t_str}"))
                row.addStretch()
                svl.addWidget(ew)
        else:
            empty = QLabel("还没有事项"); empty.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:{T.BODY}px;"); svl.addWidget(empty)
        svl.addStretch()
        scroll.setWidget(scroll_w); lo.addWidget(scroll, 1)

        inp_row = QHBoxLayout(); inp_row.setSpacing(8)
        inp = QLineEdit(); inp.setPlaceholderText("新事项..."); inp_row.addWidget(inp, 2)
        inp_t = QLineEdit(); inp_t.setPlaceholderText("时间"); inp_t.setFixedWidth(100); inp_row.addWidget(inp_t)
        lo.addLayout(inp_row)

        br = QHBoxLayout(); br.setSpacing(12)
        c2=GhostBtn("关闭"); c2.clicked.connect(dlg.reject); o2=GoldBtn("添加"); o2.clicked.connect(dlg.accept)
        br.addStretch(); br.addWidget(c2); br.addWidget(o2); lo.addLayout(br)
        if dlg.exec()==QDialog.Accepted:
            text=inp.text().strip()
            if text: add_date_event(ds, text, inp_t.text().strip()); self.build()


class ReviewPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lo = QVBoxLayout(self); lo.setContentsMargins(T.PAGE_MARGIN,24,T.PAGE_MARGIN,24); lo.setSpacing(16)
        self._layout = lo; self.build()

    def build(self):
        _clear_layout(self._layout)

        title = QLabel("每日回顾")
        title.setStyleSheet(f"font-family:'{T.FONT_DISPLAY}'; font-size:{T.H1}px; font-weight:600;")
        self._layout.addWidget(title)

        card = Card(); cl = QVBoxLayout(card); cl.setSpacing(12)
        self.review_input = QTextEdit(); self.review_input.setPlaceholderText("写一条回顾...今天做了什么？感觉如何？")
        self.review_input.setFixedHeight(120)
        mood_input = QLineEdit(); mood_input.setPlaceholderText("今日心情（可选）"); mood_input.setObjectName("mood_input")
        save_btn = GoldBtn("保存"); save_btn.clicked.connect(lambda: self.save_review())
        cl.addWidget(self.review_input); cl.addWidget(mood_input); cl.addWidget(save_btn)
        self._layout.addWidget(card)

        reviews = get_reviews()
        for r in reversed(reviews[-20:]):
            rc = Card(); rl = QVBoxLayout(rc); rl.setSpacing(6)
            dl = QLabel(r["date"]); dl.setStyleSheet(f"font-size:{T.SMALL}px; color:{T.TEXT_MUTED};"); rl.addWidget(dl)
            tl = QLabel(r["text"]); tl.setStyleSheet(f"font-size:{T.BODY}px; color:{T.TEXT};"); tl.setWordWrap(True); rl.addWidget(tl)
            if r.get("mood"):
                ml = QLabel(f"心情：{r['mood']}"); ml.setStyleSheet(f"font-size:{T.SMALL}px; color:{T.GOLD};"); rl.addWidget(ml)
            self._layout.addWidget(rc)
        self._layout.addStretch()

    def save_review(self):
        text = self.review_input.toPlainText().strip()
        if not text: return
        mood = self.window().findChild(QLineEdit,"mood_input")
        add_review(text, mood.text().strip() if mood else ""); self.build()
        self.window().toast("已保存")


# ======== MAIN WINDOW ========

class FirstStepApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("第一步")
        self.resize(1600, 1000)
        self.setMinimumSize(1200, 800)
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width()-1600)//2, (screen.height()-1000)//2)
        # Kill white flash: set palette before any painting
        pal = self.palette(); pal.setColor(self.backgroundRole(), QColor(T.BG))
        self.setPalette(pal); self.setAutoFillBackground(True)
        self.setStyleSheet(qss())

        central = QWidget(); self.setCentralWidget(central)
        main_layout = QVBoxLayout(central); main_layout.setContentsMargins(0,0,0,0); main_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.pages = [DashboardPage(), TimerPage(), CapturePage(), CalendarPage(), ReviewPage()]
        for p in self.pages: self.stack.addWidget(p)
        main_layout.addWidget(self.stack, 1)

        nav = QWidget()
        nbg = QColor(T.BG); nbg.setAlpha(242)
        nav.setStyleSheet(f"background: rgba({nbg.red()},{nbg.green()},{nbg.blue()},0.95); border-top: 1px solid {T.DIVIDER};")
        nav_layout = QHBoxLayout(nav); nav_layout.setContentsMargins(12,6,12,6); nav_layout.setSpacing(0)
        nav_layout.addStretch()
        # Page mapping: nav button -> page index
        # Pages: [0:Dashboard, 1:Timer, 2:Capture, 3:Calendar, 4:Review]
        # Nav: 今日->0, 捕获池->2, 日历->3, 回顾->4
        self._nav_to_page = [0, 2, 3, 4]
        self.nav_btns = []
        for icon,label in [("○","今日"),("☰","捕获池"),("☽","日历"),("✎","回顾")]:
            btn = NavBtn(icon,label)
            page_idx = self._nav_to_page[len(self.nav_btns)]
            btn.clicked.connect(lambda checked, pi=page_idx: self.show_page(pi))
            nav_layout.addWidget(btn); self.nav_btns.append(btn)
        # Theme toggle button
        self._theme_btn = QPushButton("配色"); self._theme_btn.setFixedSize(70,70); self._theme_btn.setCursor(Qt.PointingHandCursor)
        self._theme_btn.setStyleSheet(f"background:transparent; color:{T.TEXT_MUTED}; border:1px solid {T.DIVIDER}; border-radius:35px; font-size:11px;")
        self._theme_btn.clicked.connect(self.cycle_theme)
        nav_layout.addWidget(self._theme_btn)
        nav_layout.addStretch(); main_layout.addWidget(nav)
        self._theme_dirty = set()
        self._nav = nav; self.nav_btns[0].setChecked(True)
        self.check_morning()
        # Show after everything is built to avoid white flash
        self.show()

    def check_morning(self):
        log = get_daily_log(); td = today_key()
        # Auto-populate daily habits
        auto_populate_daily_habits()
        if log.get(td,{}).get("morning_done"): return
        if get_today_task().get("date")!=td: self.show_morning()

    def show_morning(self):
        steps = [("01","喝一杯水","唤醒身体的第一步"),("02","洗漱","让自己清醒过来"),("03","坐到桌前","你已经准备好开始了")]
        overlay = QDialog(self); overlay.setWindowFlags(Qt.FramelessWindowHint|Qt.Dialog)
        overlay.setModal(True); overlay.setFixedSize(self.size()); overlay.setStyleSheet(f"background:{T.BG};"); overlay.move(self.pos())
        lo = QVBoxLayout(overlay); lo.setAlignment(Qt.AlignCenter); lo.setSpacing(40)

        self._morning_step = 0
        num_label = QLabel("01"); num_label.setAlignment(Qt.AlignCenter)
        num_label.setStyleSheet(f"font-family:'{T.FONT_DISPLAY}'; font-size:96px; font-weight:200; color:{T.GOLD_DIM};")
        lo.addWidget(num_label)
        text_label = QLabel("喝一杯水"); text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet(f"font-size:{T.H1}px; font-weight:500; color:{T.TEXT};")
        lo.addWidget(text_label)
        sub_label = QLabel("唤醒身体的第一步"); sub_label.setAlignment(Qt.AlignCenter)
        sub_label.setStyleSheet(f"font-size:{T.BODY}px; color:{T.TEXT_DIM};")
        lo.addWidget(sub_label)

        dots_l = QHBoxLayout(); dots_l.setAlignment(Qt.AlignCenter); dots_l.setSpacing(20)
        self._dots = []
        for i in range(3):
            dot = QLabel(""); dot.setFixedSize(14,14); dot.setStyleSheet(f"background:{T.ELEVATED}; border-radius:7px;")
            dots_l.addWidget(dot); self._dots.append(dot)
        lo.addLayout(dots_l)

        next_btn = GoldBtn("完成")
        next_btn.clicked.connect(lambda: self._advance_morning(overlay,num_label,text_label,sub_label,next_btn,steps))
        lo.addWidget(next_btn, alignment=Qt.AlignCenter)
        overlay.exec()

    def _advance_morning(self, overlay, nl, tl, sl, nbtn, steps):
        self._morning_step += 1
        if self._morning_step >= 3:
            save_daily_entry({"morning_done":True}); overlay.accept(); return
        s = steps[self._morning_step]; nl.setText(s[0]); tl.setText(s[1]); sl.setText(s[2])
        for i in range(3):
            self._dots[i].setStyleSheet(f"background:{T.GOLD if i<=self._morning_step else T.ELEVATED}; border-radius:7px;")
        if self._morning_step==2: nbtn.setText("准备好了")

    def show_page(self, idx):
        # Rebuild page if theme changed since last visit
        if idx in self._theme_dirty:
            page = self.stack.widget(idx)
            if page:
                try:
                    if hasattr(page, 'rebuild'): page.rebuild()
                    elif hasattr(page, 'build'): page.build()
                except: pass
                self._theme_dirty.discard(idx)

        if self.stack.currentIndex() != idx:
            # Safe overlay: uses paintEvent + animated alpha, no QGraphicsEffect
            overlay = _FadeWidget(self, QColor(T.BG))
            overlay.setGeometry(self.stack.geometry())
            overlay.show(); overlay.raise_()
            self.stack.setCurrentIndex(idx)
            overlay.fade_out()
        else:
            self.stack.setCurrentIndex(idx)

        for i, pi in enumerate(self._nav_to_page):
            self.nav_btns[i].setChecked(pi == idx)

    def show_timer(self):
        td = get_today_task(); task = td["task"]
        tp = self.pages[1]; tp.setup(task["title"], task.get("estimated_minutes",15))
        self.show_page(1); self._nav.hide()

    def on_nav(self, idx):
        self._nav.show()
        self.show_page(self._nav_to_page[idx])

    def cycle_theme(self):
        """Cycle to next theme - mark all pages dirty, rebuild current"""
        names = list(THEMES.keys())
        idx = names.index(_current_theme)
        next_name = names[(idx + 1) % len(names)]
        apply_theme(next_name)
        self.setStyleSheet(qss())

        # 刷新底部导航栏和配色按钮的颜色
        nbg = QColor(T.BG); nbg.setAlpha(242)
        self._nav.setStyleSheet(f"background: rgba({nbg.red()},{nbg.green()},{nbg.blue()},0.95); border-top: 1px solid {T.DIVIDER};")
        self._theme_btn.setStyleSheet(f"background:transparent; color:{T.TEXT_MUTED}; border:1px solid {T.DIVIDER}; border-radius:35px; font-size:11px;")
        for btn in self.nav_btns:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {T.TEXT_MUTED}; border: none;
                    border-radius: 16px; font-size: {T.BODY}px; font-weight: 500;
                }}
                QPushButton:hover {{ color: {T.TEXT_DIM}; }}
                QPushButton:checked {{ color: {T.GOLD}; font-weight: 700; font-size: {T.BODY+1}px; }}
            """)

        # Mark all pages as needing rebuild on next visit
        self._theme_dirty = set(range(len(self.pages)))
        # Rebuild current page immediately
        cur = self.stack.currentIndex()
        page = self.stack.widget(cur)
        if page:
            try:
                if hasattr(page, 'rebuild'): page.rebuild()
                elif hasattr(page, 'build'): page.build()
            except: pass
            self._theme_dirty.discard(cur)
        self.stack.setCurrentIndex(cur)
        for i, pi in enumerate(self._nav_to_page):
            self.nav_btns[i].setChecked(pi == cur)
        self.toast(f"配色：{next_name}")

    def toast(self, msg):
        tw = QLabel(msg, self); tw.setAlignment(Qt.AlignCenter)
        tw.setStyleSheet(f"background:{T.ELEVATED}; color:{T.TEXT}; border:1px solid {T.DIVIDER}; border-radius:50px; padding:14px 32px; font-size:{T.BODY}px;")
        tw.adjustSize(); tw.move((self.width()-tw.width())//2, 40); tw.show(); tw.raise_()
        QTimer.singleShot(2000, tw.deleteLater)


def main():
    app = QApplication(sys.argv); app.setApplicationName("第一步")
    app.setFont(QFont(T.FONT_BODY, T.BODY))
    w = FirstStepApp(); sys.exit(app.exec())

if __name__=="__main__": main()
