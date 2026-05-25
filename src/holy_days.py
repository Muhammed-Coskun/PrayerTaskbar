"""
holy_days.py — Islamic holy days data and visual styles.

Contains holy day dates for 2026-2035 (from Diyanet) and gradient
styles for the holy day cards in the flyout menu.
"""

from datetime import date
from typing import Optional


# Holy day dates from Diyanet (2026-2035)
# Each entry: (date, translation_key, [optional day_number for multi-day holidays])
# Translation keys map to i18n.get_holy_day_name()
HOLY_DAYS = [
    # ═══ 2026 ═══
    (date(2026, 1, 15), "mirac"),
    (date(2026, 2, 2), "berat"),
    (date(2026, 2, 19), "ramadan_start"),
    (date(2026, 3, 16), "qadr"),
    (date(2026, 3, 20), "eid_fitr", 1), (date(2026, 3, 21), "eid_fitr", 2), (date(2026, 3, 22), "eid_fitr", 3),
    (date(2026, 5, 27), "eid_adha", 1), (date(2026, 5, 28), "eid_adha", 2),
    (date(2026, 5, 29), "eid_adha", 3), (date(2026, 5, 30), "eid_adha", 4),
    (date(2026, 6, 16), "hijri_ny"),
    (date(2026, 6, 25), "ashura"),
    (date(2026, 8, 24), "mawlid"),
    (date(2026, 12, 10), "three_months"), (date(2026, 12, 10), "raghaib"),

    # ═══ 2027 ═══
    (date(2027, 1, 4), "mirac"),
    (date(2027, 1, 22), "berat"),
    (date(2027, 2, 8), "ramadan_start"),
    (date(2027, 3, 5), "qadr"),
    (date(2027, 3, 9), "eid_fitr", 1), (date(2027, 3, 10), "eid_fitr", 2), (date(2027, 3, 11), "eid_fitr", 3),
    (date(2027, 5, 16), "eid_adha", 1), (date(2027, 5, 17), "eid_adha", 2),
    (date(2027, 5, 18), "eid_adha", 3), (date(2027, 5, 19), "eid_adha", 4),
    (date(2027, 6, 6), "hijri_ny"),
    (date(2027, 6, 15), "ashura"),
    (date(2027, 8, 13), "mawlid"),
    (date(2027, 11, 29), "three_months"), (date(2027, 12, 2), "raghaib"),
    (date(2027, 12, 24), "mirac"),

    # ═══ 2028 ═══
    (date(2028, 1, 11), "berat"),
    (date(2028, 1, 28), "ramadan_start"),
    (date(2028, 2, 22), "qadr"),
    (date(2028, 2, 26), "eid_fitr", 1), (date(2028, 2, 27), "eid_fitr", 2), (date(2028, 2, 28), "eid_fitr", 3),
    (date(2028, 5, 5), "eid_adha", 1), (date(2028, 5, 6), "eid_adha", 2),
    (date(2028, 5, 7), "eid_adha", 3), (date(2028, 5, 8), "eid_adha", 4),
    (date(2028, 5, 25), "hijri_ny"),
    (date(2028, 6, 3), "ashura"),
    (date(2028, 8, 2), "mawlid"),
    (date(2028, 11, 18), "three_months"), (date(2028, 11, 23), "raghaib"),
    (date(2028, 12, 13), "mirac"),
    (date(2028, 12, 30), "berat"),

    # ═══ 2029 ═══
    (date(2029, 1, 16), "ramadan_start"),
    (date(2029, 2, 10), "qadr"),
    (date(2029, 2, 14), "eid_fitr", 1), (date(2029, 2, 15), "eid_fitr", 2), (date(2029, 2, 16), "eid_fitr", 3),
    (date(2029, 4, 24), "eid_adha", 1), (date(2029, 4, 25), "eid_adha", 2),
    (date(2029, 4, 26), "eid_adha", 3), (date(2029, 4, 27), "eid_adha", 4),
    (date(2029, 5, 14), "hijri_ny"),
    (date(2029, 5, 23), "ashura"),
    (date(2029, 7, 23), "mawlid"),
    (date(2029, 11, 7), "three_months"), (date(2029, 11, 8), "raghaib"),
    (date(2029, 12, 2), "mirac"),
    (date(2029, 12, 20), "berat"),

    # ═══ 2030 ═══
    (date(2030, 1, 5), "ramadan_start"),
    (date(2030, 1, 30), "qadr"),
    (date(2030, 2, 4), "eid_fitr", 1), (date(2030, 2, 5), "eid_fitr", 2), (date(2030, 2, 6), "eid_fitr", 3),
    (date(2030, 4, 13), "eid_adha", 1), (date(2030, 4, 14), "eid_adha", 2),
    (date(2030, 4, 15), "eid_adha", 3), (date(2030, 4, 16), "eid_adha", 4),
    (date(2030, 5, 3), "hijri_ny"),
    (date(2030, 5, 12), "ashura"),
    (date(2030, 7, 12), "mawlid"),
    (date(2030, 10, 28), "three_months"), (date(2030, 10, 31), "raghaib"),
    (date(2030, 11, 22), "mirac"),
    (date(2030, 12, 9), "berat"),
    (date(2030, 12, 26), "ramadan_start"),

    # ═══ 2031 ═══
    (date(2031, 1, 20), "qadr"),
    (date(2031, 1, 24), "eid_fitr", 1), (date(2031, 1, 25), "eid_fitr", 2), (date(2031, 1, 26), "eid_fitr", 3),
    (date(2031, 4, 2), "eid_adha", 1), (date(2031, 4, 3), "eid_adha", 2),
    (date(2031, 4, 4), "eid_adha", 3), (date(2031, 4, 5), "eid_adha", 4),

    # ═══ 2032 ═══
    (date(2032, 1, 9), "qadr"),
    (date(2032, 1, 14), "eid_fitr", 1), (date(2032, 1, 15), "eid_fitr", 2), (date(2032, 1, 16), "eid_fitr", 3),
    (date(2032, 3, 22), "eid_adha", 1), (date(2032, 3, 23), "eid_adha", 2),
    (date(2032, 3, 24), "eid_adha", 3), (date(2032, 3, 25), "eid_adha", 4),

    # ═══ 2033 ═══
    (date(2033, 1, 2), "eid_fitr", 1), (date(2033, 1, 3), "eid_fitr", 2), (date(2033, 1, 4), "eid_fitr", 3),
    (date(2033, 3, 11), "eid_adha", 1), (date(2033, 3, 12), "eid_adha", 2),
    (date(2033, 3, 13), "eid_adha", 3), (date(2033, 3, 14), "eid_adha", 4),
    (date(2033, 4, 1), "hijri_ny"),
    (date(2033, 4, 10), "ashura"),
    (date(2033, 6, 9), "mawlid"),
    (date(2033, 9, 25), "three_months"), (date(2033, 9, 29), "raghaib"),
    (date(2033, 10, 20), "mirac"),
    (date(2033, 11, 6), "berat"),
    (date(2033, 11, 23), "ramadan_start"),
    (date(2033, 12, 18), "qadr"),
    (date(2033, 12, 23), "eid_fitr", 1), (date(2033, 12, 24), "eid_fitr", 2), (date(2033, 12, 25), "eid_fitr", 3),

    # ═══ 2034 ═══
    (date(2034, 3, 1), "eid_adha", 1), (date(2034, 3, 2), "eid_adha", 2),
    (date(2034, 3, 3), "eid_adha", 3), (date(2034, 3, 4), "eid_adha", 4),
    (date(2034, 3, 21), "hijri_ny"),
    (date(2034, 3, 30), "ashura"),
    (date(2034, 5, 29), "mawlid"),
    (date(2034, 9, 14), "three_months"), (date(2034, 9, 14), "raghaib"),
    (date(2034, 10, 9), "mirac"),
    (date(2034, 10, 26), "berat"),
    (date(2034, 11, 12), "ramadan_start"),
    (date(2034, 12, 7), "qadr"),
    (date(2034, 12, 12), "eid_fitr", 1), (date(2034, 12, 13), "eid_fitr", 2), (date(2034, 12, 14), "eid_fitr", 3),

    # ═══ 2035 ═══
    (date(2035, 2, 18), "eid_adha", 1), (date(2035, 2, 19), "eid_adha", 2),
    (date(2035, 2, 20), "eid_adha", 3), (date(2035, 2, 21), "eid_adha", 4),
    (date(2035, 3, 11), "hijri_ny"),
    (date(2035, 3, 20), "ashura"),
    (date(2035, 5, 19), "mawlid"),
    (date(2035, 9, 3), "three_months"), (date(2035, 9, 6), "raghaib"),
    (date(2035, 9, 28), "mirac"),
    (date(2035, 10, 16), "berat"),
    (date(2035, 11, 1), "ramadan_start"),
    (date(2035, 11, 26), "qadr"),
    (date(2035, 12, 1), "eid_fitr", 1), (date(2035, 12, 2), "eid_fitr", 2), (date(2035, 12, 3), "eid_fitr", 3),
]


# Gradient styles for each holy day type
HOLY_DAY_STYLES = {
    'mirac':          {'grad_start': '#1a0a2e', 'grad_mid': '#2d1b4e', 'grad_end': '#5c2d91', 'accent': '#b388ff'},
    'berat':          {'grad_start': '#0d1525', 'grad_mid': '#1a2744', 'grad_end': '#2e3f6e', 'accent': '#90caf9'},
    'qadr':           {'grad_start': '#1a1400', 'grad_mid': '#2e2200', 'grad_end': '#5c4a00', 'accent': '#ffd700'},
    'ramadan_start':  {'grad_start': '#1a1500', 'grad_mid': '#2e2800', 'grad_end': '#4d4000', 'accent': '#ffb300'},
    'eid_fitr':       {'grad_start': '#0a1a0a', 'grad_mid': '#142e14', 'grad_end': '#1e5c1e', 'accent': '#66bb6a'},
    'eid_adha':       {'grad_start': '#0a1a18', 'grad_mid': '#142e2a', 'grad_end': '#1a5c52', 'accent': '#26a69a'},
    'hijri_ny':       {'grad_start': '#0a1525', 'grad_mid': '#142844', 'grad_end': '#1e4a7a', 'accent': '#42a5f5'},
    'ashura':         {'grad_start': '#1a120a', 'grad_mid': '#2e1f12', 'grad_end': '#5c3a1a', 'accent': '#e6a44a'},
    'mawlid':         {'grad_start': '#1a0a12', 'grad_mid': '#2e1420', 'grad_end': '#5c2840', 'accent': '#f48fb1'},
    'raghaib':        {'grad_start': '#0a1a1e', 'grad_mid': '#142e35', 'grad_end': '#1a5c68', 'accent': '#4dd0e1'},
    'three_months':   {'grad_start': '#140a25', 'grad_mid': '#251444', 'grad_end': '#3d1e7a', 'accent': '#b39ddb'},
}


def get_next_holy_day() -> tuple[Optional[date], Optional[str], Optional[int]]:
    """Find the next upcoming holy day from today.
    
    Returns:
        Tuple of (date, translation_key, day_number_or_None).
        day_number is set for multi-day holidays (e.g. Eid day 1, 2, 3).
        Returns (None, None, None) if no future holy days found.
    """
    today = date.today()
    for entry in sorted(HOLY_DAYS, key=lambda x: x[0]):
        d = entry[0]
        key = entry[1]
        day_num = entry[2] if len(entry) > 2 else None
        if d >= today:
            return d, key, day_num
    return None, None, None


def get_holy_day_style(key: str) -> dict:
    """Get the gradient style for a holy day type.
    
    Args:
        key: Translation key (e.g. 'qadr', 'eid_fitr').
        
    Returns:
        Style dict with grad_start, grad_mid, grad_end, accent keys.
    """
    return HOLY_DAY_STYLES.get(key, HOLY_DAY_STYLES['qadr'])


def is_ramadan_today(hijri_dates: dict) -> bool:
    """Check if today is during Ramadan based on hijri date strings.
    
    Args:
        hijri_dates: Dict mapping date -> hijri date string.
        
    Returns:
        True if today's hijri date contains 'Ramazan' or 'Ramadan'.
    """
    today = date.today()
    hicri = hijri_dates.get(today, "")
    return "Ramazan" in hicri or "Ramadan" in hicri
