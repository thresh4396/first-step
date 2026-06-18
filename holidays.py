"""
「第一步」节日模块
中国节日（农历 + 公历）+ 澳洲节日（公历 + 复活节变动）
"""

from datetime import date, timedelta
from lunar import solar_to_lunar, lunar_months_in_year


# ═══════════════════════════════════════════
# 农历节日：(农历月, 农历日) → 节日名
# ═══════════════════════════════════════════
LUNAR_HOLIDAYS = {
    (1, 1):   "春节",
    (1, 15):  "元宵",
    (5, 5):   "端午",
    (7, 7):   "七夕",
    (7, 15):  "中元",
    (8, 15):  "中秋",
    (9, 9):   "重阳",
    (12, 8):  "腊八",
}

# ═══════════════════════════════════════════
# 中国公历节日：(月, 日) → 节日名
# ═══════════════════════════════════════════
CHINESE_SOLAR_HOLIDAYS = {
    (1, 1):  "元旦",
    (3, 8):  "妇女节",
    (5, 1):  "劳动节",
    (6, 1):  "儿童节",
    (7, 1):  "建党节",
    (8, 1):  "建军节",
    (10, 1): "国庆",
}

# ═══════════════════════════════════════════
# 澳洲公历节日（固定日期）
# ═══════════════════════════════════════════
AU_FIXED_HOLIDAYS = {
    (1, 1):  "元旦",       # New Year's Day — 与元旦重叠，displayName 用中文
    (1, 26): "澳国庆",     # Australia Day
    (4, 25): "澳新军团日",  # ANZAC Day
    (12, 25): "圣诞",      # Christmas
    (12, 26): "节礼日",     # Boxing Day
}


# ═══════════════════════════════════════════
# 复活节计算（Meeus–Jones–Butcher）
# ═══════════════════════════════════════════
def easter_sunday(year: int) -> date:
    """返回指定年份的复活节星期日"""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


# ═══════════════════════════════════════════
# 澳洲变动节日
# ═══════════════════════════════════════════
def _kings_birthday(year: int) -> date:
    """6 月第 2 个周一（大多数州）"""
    jun1 = date(year, 6, 1)
    first_mon = jun1 + timedelta(days=(7 - jun1.weekday()) % 7)
    return first_mon + timedelta(days=7)


def _labour_day_nsw(year: int) -> date:
    """10 月第 1 个周一（NSW/ACT/SA）"""
    oct1 = date(year, 10, 1)
    return oct1 + timedelta(days=(7 - oct1.weekday()) % 7)


# ═══════════════════════════════════════════
# 清明近似（公历 4/4 或 4/5）
# ═══════════════════════════════════════════
def _qingming_date(year: int) -> date:
    """清明近似：闰年多为 4/4，平年多为 4/5，误差 ±1 天"""
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        return date(year, 4, 4)
    return date(year, 4, 5)


# ═══════════════════════════════════════════
# 主查询函数
# ═══════════════════════════════════════════
def get_holidays(year: int, month: int, day: int) -> list[str]:
    """
    返回指定公历日期对应的节日名列表。
    优先级：农历 > 清明 > 中国公历 > 澳洲
    同日多节日时只取第一个（日历格子空间有限）。
    """
    result = []
    d = date(year, month, day)

    # 1. 农历节日
    _, luna_m, luna_d, is_leap, _, _ = solar_to_lunar(year, month, day)
    if not is_leap:
        name = LUNAR_HOLIDAYS.get((luna_m, luna_d))
        if name:
            result.append(name)

    # 2. 除夕 — 腊月最后一天
    if not is_leap and luna_m == 12 and not result:
        luna_yr = solar_to_lunar(year, month, day)[0]
        months = lunar_months_in_year(luna_yr)
        for m_num, m_days, m_leap in reversed(months):
            if m_num == 12 and not m_leap:
                if luna_d == m_days:
                    result.append("除夕")
                break

    # 3. 清明
    if d == _qingming_date(year):
        result.append("清明")

    # 4. 中国公历节日
    name = CHINESE_SOLAR_HOLIDAYS.get((month, day))
    if name and name not in result:
        result.append(name)

    # 5. 澳洲固定节日
    name = AU_FIXED_HOLIDAYS.get((month, day))
    if name and name not in result:
        result.append(name)

    # 6. 澳洲变动节日
    if not result:
        easter = easter_sunday(year)
        if d == easter - timedelta(days=2):
            result.append("受难日")        # Good Friday
        elif d == easter + timedelta(days=1):
            result.append("复活节周一")     # Easter Monday
        elif d == _kings_birthday(year):
            result.append("国王生日")       # King's Birthday
        elif d == _labour_day_nsw(year):
            result.append("劳动日")         # Labour Day

    return result
