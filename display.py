"""
终端显示工具函数
统一的输出格式（纯文本，兼容 Windows 中文终端）
"""

import os
import sys

# 设置控制台为 UTF-8（Windows 兼容）
if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# 清屏
def clear():
    os.system("cls" if os.name == "nt" else "clear")


# 分割线
SEP = "-" * 45
SEP_FULL = "=" * 45


def header(title="第一步"):
    """打印顶部标题栏"""
    print()
    print(f"  {SEP_FULL}")
    print(f"  >>  {title}")
    print(f"  {SEP_FULL}")


def footer():
    """打印底部分割线"""
    print(f"  {SEP_FULL}")
    print()


def section(title):
    """打印段落标题"""
    print(f"\n  +-- {title}")


def section_end():
    """打印段落结尾"""
    print(f"  +" + "-" * 43)


def box_line(text):
    """在框内打印一行"""
    print(f"  | {text}")


def info(text):
    """普通信息"""
    print(f"  {text}")


def success(text):
    """成功信息"""
    print(f"  [OK] {text}")


def warn(text):
    """警告信息"""
    print(f"  [!] {text}")


def emph(text):
    """强调信息"""
    print(f"  [i] {text}")


def menu_item(key, label, extra=""):
    """打印菜单项"""
    line = f"  [{key}] {label}"
    if extra:
        line += f"  {extra}"
    print(line)


def progress_bar(current, total, width=20):
    """返回进度条字符串"""
    filled = int(width * current / total) if total > 0 else 0
    return "#" * filled + "-" * (width - filled)


def input_safe(prompt="> "):
    """安全的输入函数"""
    try:
        return input(f"  {prompt}").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n")
        return "q"
