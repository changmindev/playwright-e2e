"""검증 대상 지역과 값의 허용 범위.

기대값을 화면에서 만들지 않는다는 원칙은 여기서도 같다.
'화면에 뜬 숫자가 화면에 뜬 다른 숫자와 맞는가'가 아니라,
**바깥에 정의한 기준**과 대조한다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    """검색어 하나가 곧 하나의 검증 대상이다."""

    key: str          # 리포트·테스트 id 에 쓰는 짧은 이름
    query: str        # 네이버 검색어
    expected_title: str   # 검색 결과 카드가 내놓아야 하는 행정구역명


# 강원도는 2023년 '강원특별자치도'로 바뀌었다.
# 검색어는 옛 이름 그대로 쓰되 화면에 나와야 하는 이름은 새 이름으로 둔다.
# 이 둘을 같다고 적으면, 제품이 옛 이름을 그대로 노출해도 테스트가 통과한다.
REGIONS: list[Region] = [
    Region("seoul", "서울 날씨", "서울특별시"),
    Region("gangwon", "강원도 날씨", "강원특별자치도"),
    Region("gyeonggi", "경기도 날씨", "경기도"),
]

REGION_BY_KEY = {r.key: r for r in REGIONS}

# ── 값의 허용 범위 ────────────────────────────────────────────
# 근거: 기상청 국내 극값 기록에 여유를 둔 값이다.
# 관측 최고 41.0°(2018 홍천) · 최저 -32.6°(1981 양평) 을 넘는 값이 나오면
# 그건 날씨가 아니라 파싱이 틀린 것이다.
TEMP_MIN_C = -35.0
TEMP_MAX_C = 45.0

HUMIDITY_RANGE = (0, 100)
PRECIP_PROB_RANGE = (0, 100)

# 시간당 강수량 상한. 국내 1시간 최다 강수량 기록(약 145mm)에 여유를 둔다.
PRECIP_MM_MAX = 200.0

WIND_MS_MAX = 75.0  # 태풍 최대순간풍속 기록(약 60m/s) 위로 여유

# 시간별 표에서 최소 이만큼은 나와야 '예보를 받았다'고 본다.
MIN_HOURLY_ROWS = 6
