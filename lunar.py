"""
农历计算模块
实现公历转农历（1900–2100），基于查表法
"""

# 农历数据表：每个整数编码一年的农历信息
# 低 4 位：闰月月份（0=无闰月）
# 高 16 位（bit 4-15）：每个月的大小（1=30天，0=29天），从正月到十二月
# 如果有闰月，bit 16 开始存闰月信息
LUNAR_INFO = [
    0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,
    0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,
    0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,
    0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,
    0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,
    0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5b0, 0x14573, 0x052b0, 0x0a9a8, 0x0e950, 0x06aa0,
    0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,
    0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b6a0, 0x195a6,
    0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,
    0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,
    0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,
    0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,
    0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,
    0x05aa0, 0x076a3, 0x096d0, 0x04afb, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,
    0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,
    0x14b63, 0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6, 0x0ea50, 0x06aa0, 0x1a6c4, 0x0aae0,
    0x092e0, 0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0, 0x0a6d0, 0x055d4,
    0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50, 0x055a0, 0x0aba4, 0x0a5b0, 0x052b0,
    0x0b273, 0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x14b55, 0x04b60, 0x0a570, 0x054e4, 0x0d160,
    0x0e968, 0x0d520, 0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a4d0, 0x0d150, 0x0f252,
    0x0d520,
]

# 天干地支
TIAN_GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DI_ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SHENG_XIAO = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# 农历月份名
LUNAR_MONTH_NAMES = [
    "", "正月", "二月", "三月", "四月", "五月", "六月",
    "七月", "八月", "九月", "十月", "十一月", "十二月"
]

# 农历日期名
LUNAR_DAY_NAMES = [
    "", "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"
]

# 公历每月天数（非闰年）
SOLAR_MONTH_DAYS = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def is_leap_year(year):
    """判断公历闰年"""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def solar_days_in_month(year, month):
    """返回公历某年某月的天数"""
    if month == 2 and is_leap_year(year):
        return 29
    return SOLAR_MONTH_DAYS[month]


def _lunar_year_info(year):
    """获取农历年的编码信息"""
    return LUNAR_INFO[year - 1900]


def lunar_months_in_year(year):
    """
    返回农历年的月份列表
    每个元素为 (月份号, 天数, 是否为闰月)
    """
    info = _lunar_year_info(year)
    leap_month = info & 0xf  # 低 4 位：闰月
    months = []

    # 解析 12 个常规月
    for i in range(12):
        day_bit = 12 - i  # 从高位到低位
        days = 30 if (info >> (day_bit + 3)) & 1 else 29
        months.append((i + 1, days, False))
        # 如果这个月是闰月，插入闰月
        if leap_month and i + 1 == leap_month:
            leap_days = 30 if (info >> 16) & 1 else 29
            months.append((i + 1, leap_days, True))

    return months


def solar_to_lunar(year, month, day):
    """
    公历转农历
    返回 (农历年, 农历月, 农历日, 是否闰月, 农历年干支, 生肖)
    支持 1900-2100 年
    """
    # 1900年1月1日 = 农历1899年腊月初一（这里使用 1900-01-31 = 农历1900年正月初一）
    # 计算从 1900-01-31 到目标日期的天数偏移
    base_year, base_month, base_day = 1900, 1, 31

    # 计算偏移天数
    offset = 0
    for y in range(base_year, year):
        offset += 366 if is_leap_year(y) else 365
    for m in range(1, month):
        offset += solar_days_in_month(year, m)
    offset += day - base_day

    # 按农历年推进
    lunar_year = 1900
    lunar_months_list = lunar_months_in_year(lunar_year)
    total_days = sum(d for _, d, _ in lunar_months_list)

    while offset >= total_days:
        offset -= total_days
        lunar_year += 1
        lunar_months_list = lunar_months_in_year(lunar_year)
        total_days = sum(d for _, d, _ in lunar_months_list)

    # 定位到具体月份和日期
    lunar_month = 1
    is_leap = False
    for m_num, m_days, m_leap in lunar_months_list:
        if offset < m_days:
            lunar_month = m_num
            is_leap = m_leap
            lunar_day = offset + 1
            break
        offset -= m_days

    # 干支年
    gan_idx = (lunar_year - 4) % 10
    zhi_idx = (lunar_year - 4) % 12
    gan_zhi = TIAN_GAN[gan_idx] + DI_ZHI[zhi_idx]
    shengxiao = SHENG_XIAO[zhi_idx]

    return lunar_year, lunar_month, lunar_day, is_leap, gan_zhi, shengxiao


def lunar_date_string(year, month, day):
    """获取农历日期字符串，如 '五月二十'"""
    lunar_year, lunar_month, lunar_day, is_leap, gan_zhi, sx = solar_to_lunar(year, month, day)
    prefix = "闰" if is_leap else ""
    month_str = prefix + LUNAR_MONTH_NAMES[lunar_month]
    day_str = LUNAR_DAY_NAMES[lunar_day]
    return f"{gan_zhi}年 {month_str}{day_str}"


def lunar_day_short(year, month, day):
    """获取农历日期简短版，如 '五月二十'"""
    _, lunar_month, lunar_day, is_leap, _, _ = solar_to_lunar(year, month, day)
    prefix = "闰" if is_leap else ""
    month_str = prefix + LUNAR_MONTH_NAMES[lunar_month]
    day_str = LUNAR_DAY_NAMES[lunar_day]
    return f"{month_str}{day_str}"


def get_ganzhi_year(year, month, day):
    """获取农历年干支"""
    _, _, _, _, gan_zhi, sx = solar_to_lunar(year, month, day)
    return gan_zhi, sx
