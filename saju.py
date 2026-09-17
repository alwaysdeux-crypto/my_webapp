from datetime import date, timedelta

STEMS = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계']
STEM_HANJA = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
BRANCHES = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해']
BRANCH_HANJA = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

STEM_ELEMENT = ['목', '목', '화', '화', '토', '토', '금', '금', '수', '수']
BRANCH_ELEMENT = ['수', '토', '목', '목', '토', '화', '화', '토', '금', '금', '토', '수']

# 오호둔(五虎遁): 연간 index -> 인월(寅月)의 월간 index
MONTH_STEM_START = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}

# 오서둔(五鼠遁): 일간 index -> 자시(子時)의 시간 index
HOUR_STEM_START = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}

# 절기 근사 기준일 (월, 일, 해당 월지 index) - 실제 절입 시각은 매년 하루 정도 오차가 있을 수 있음
SOLAR_TERM_BOUNDARIES = [
    (1, 6, 1),   # 소한 -> 축월
    (2, 4, 2),   # 입춘 -> 인월
    (3, 6, 3),   # 경칩 -> 묘월
    (4, 5, 4),   # 청명 -> 진월
    (5, 6, 5),   # 입하 -> 사월
    (6, 6, 6),   # 망종 -> 오월
    (7, 7, 7),   # 소서 -> 미월
    (8, 8, 8),   # 입추 -> 신월
    (9, 8, 9),   # 백로 -> 유월
    (10, 8, 10),  # 한로 -> 술월
    (11, 7, 11),  # 입동 -> 해월
    (12, 7, 0),  # 대설 -> 자월
]

IIPCHUN = (2, 4)  # 입춘 근사일 (연주 기준일)


def _gregorian_to_jdn(y, m, d):
    a = (14 - m) // 12
    y2 = y + 4800 - a
    m2 = m + 12 * a - 3
    return d + (153 * m2 + 2) // 5 + 365 * y2 + y2 // 4 - y2 // 100 + y2 // 400 - 32045


def _day_ganzhi_index(y, m, d):
    jdn = _gregorian_to_jdn(y, m, d)
    return (jdn + 49) % 60


def _month_branch_for_date(m, d):
    branch = 0  # 1/1~1/5는 전년도 대설 이후 자월(子月)에 속함
    for bm, bd, b in SOLAR_TERM_BOUNDARIES:
        if (m, d) >= (bm, bd):
            branch = b
        else:
            break
    return branch


def _hour_branch_index(hour):
    if hour == 23 or hour == 0:
        return 0
    return (hour + 1) // 2


def _pillar(stem_idx, branch_idx):
    return {
        'stem': STEMS[stem_idx],
        'stem_hanja': STEM_HANJA[stem_idx],
        'branch': BRANCHES[branch_idx],
        'branch_hanja': BRANCH_HANJA[branch_idx],
        'ganzhi': f'{STEMS[stem_idx]}{BRANCHES[branch_idx]}',
        'ganzhi_hanja': f'{STEM_HANJA[stem_idx]}{BRANCH_HANJA[branch_idx]}',
        'stem_element': STEM_ELEMENT[stem_idx],
        'branch_element': BRANCH_ELEMENT[branch_idx],
    }


def calculate_saju(birth_date_str, birth_time_str=None):
    """생년월일(양력, YYYY-MM-DD)과 시간(HH:MM, 선택)으로 사주팔자를 계산한다.
    절기 및 간지일은 고정 근사값을 사용하므로 실제 절입 시각과 하루 정도 오차가 있을 수 있다."""
    y, m, d = (int(x) for x in birth_date_str.split('-'))

    eff_year = y - 1 if (m, d) < IIPCHUN else y
    year_stem_idx = (eff_year - 4) % 10
    year_branch_idx = (eff_year - 4) % 12

    month_branch_idx = _month_branch_for_date(m, d)
    month_offset = (month_branch_idx - 2) % 12
    month_stem_idx = (MONTH_STEM_START[year_stem_idx] + month_offset) % 10

    day_y, day_m, day_d = y, m, d
    hour = None
    if birth_time_str:
        hour = int(birth_time_str.split(':')[0])
        if hour == 23:
            next_day = date(y, m, d) + timedelta(days=1)
            day_y, day_m, day_d = next_day.year, next_day.month, next_day.day

    gz_idx = _day_ganzhi_index(day_y, day_m, day_d)
    day_stem_idx = gz_idx % 10
    day_branch_idx = gz_idx % 12

    pillars = {
        'year': _pillar(year_stem_idx, year_branch_idx),
        'month': _pillar(month_stem_idx, month_branch_idx),
        'day': _pillar(day_stem_idx, day_branch_idx),
        'hour': None,
    }

    element_idx_pairs = [
        (year_stem_idx, 'stem'), (year_branch_idx, 'branch'),
        (month_stem_idx, 'stem'), (month_branch_idx, 'branch'),
        (day_stem_idx, 'stem'), (day_branch_idx, 'branch'),
    ]

    if hour is not None:
        hour_branch_idx = _hour_branch_index(hour)
        hour_stem_idx = (HOUR_STEM_START[day_stem_idx] + hour_branch_idx) % 10
        pillars['hour'] = _pillar(hour_stem_idx, hour_branch_idx)
        element_idx_pairs += [(hour_stem_idx, 'stem'), (hour_branch_idx, 'branch')]

    element_count = {'목': 0, '화': 0, '토': 0, '금': 0, '수': 0}
    for idx, kind in element_idx_pairs:
        el = STEM_ELEMENT[idx] if kind == 'stem' else BRANCH_ELEMENT[idx]
        element_count[el] += 1

    return pillars, element_count
