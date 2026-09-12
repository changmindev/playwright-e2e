"""두 화면·두 값이 서로 어긋나지 않는가.

범위 검사는 값 하나를 혼자 본다. 여기서는 **관계**를 본다 —
같은 지점을 말하는 두 화면, 강수량과 강수확률, 시간의 연속성.
관계가 깨지는 쪽이 사용자 눈에 먼저 띄는 종류의 결함이다.
"""

from __future__ import annotations

import pytest

from naver_weather.data.regions import REGIONS

pytestmark = pytest.mark.consistency

# 검색 카드는 실황, 시간별 표의 현재 시각 칸은 예보다. 값이 완전히 같을 수는 없다.
# 3°는 '같은 지점의 같은 시각'이라면 넘지 않아야 하는 선으로 잡았다.
CURRENT_VS_HOURLY_TOLERANCE_C = 3.0

# 체감온도와 기온의 괴리 상한. 습도·바람으로 벌어질 수 있는 폭을 넉넉히 잡되,
# 둘을 바꿔 읽는 종류의 파싱 오류는 걸리게 한다.
FEELS_LIKE_GAP_MAX_C = 25.0


def test_카드가_가리킨_지점과_상세_화면의_지점이_같다(snapshot):
    """링크를 따라갔더니 다른 동네가 나오면, 사용자는 남의 동네 날씨를 본다.

    앞선 데모(Swag Labs)에서 잡은 D-04 와 같은 종류의 결함이다 —
    목록에서 연 상세가 다른 상품이었다.
    """
    assert snapshot.detail_location in snapshot.current.observation_point, (
        f"카드 {snapshot.current.observation_point!r} → "
        f"상세 {snapshot.detail_location!r} 로 지점이 어긋남"
    )


def test_실황과_시간별_예보가_크게_벌어지지_않는다(snapshot):
    now = snapshot.current.temperature_c
    first = snapshot.hourly[0].temperature_c
    assert first is not None
    gap = abs(now - first)
    assert gap <= CURRENT_VS_HOURLY_TOLERANCE_C, (
        f"실황 {now}° vs {snapshot.hourly[0].hour_label} 예보 {first}° — {gap:.1f}° 차이"
    )


def test_체감온도가_기온과_같은_세계에_있다(snapshot):
    c = snapshot.current
    gap = abs(c.feels_like_c - c.temperature_c)
    assert gap <= FEELS_LIKE_GAP_MAX_C, (
        f"기온 {c.temperature_c}° / 체감 {c.feels_like_c}° — {gap:.1f}° 차이"
    )


def test_비가_오는데_강수확률이_0인_시간이_없다(snapshot):
    """논리 모순 검사.

    강수량이 잡혀 있는데 확률이 0%면 둘 중 하나는 틀렸다.
    오늘 비가 오지 않으면 이 검사는 빈 목록을 확인하고 지나간다 —
    **비 오는 날에만 의미가 생기는 검사를 미리 넣어 둔다.**
    """
    contradictions = [
        f"{p.hour_label} 강수량 {p.precip_mm}mm 인데 강수확률 {p.precip_prob_pct}%"
        for p in snapshot.hourly
        if (p.precip_mm or 0) > 0 and (p.precip_prob_pct or 0) == 0
    ]
    assert not contradictions, "강수량·강수확률 모순:\n  " + "\n  ".join(contradictions)


def test_시간이_한_칸씩_이어진다(snapshot):
    """00시로 넘어가는 지점까지 포함해 1시간 간격인지 본다."""
    hours = [int(p.hour_label.removesuffix("시")) for p in snapshot.hourly]
    breaks = [
        f"{hours[i]}시 → {hours[i + 1]}시"
        for i in range(len(hours) - 1)
        if (hours[i] + 1) % 24 != hours[i + 1] % 24
    ]
    assert not breaks, "시간이 건너뛴 지점: " + ", ".join(breaks)


def test_세_지역이_서로_다른_지점을_본다(snapshots):
    """지역별 파라미터가 아니라 **세 지역을 한 번에** 보는 검증이다.

    지역 코드가 겹치면 화면에는 서로 다른 지역명이 뜨는데 값은 같은 곳을
    보게 된다. 지역별로 하나씩 도는 테스트로는 절대 잡히지 않는다.
    """
    codes = {k: s.current.region_code for k, s in snapshots.items()}
    assert len(set(codes.values())) == len(REGIONS), f"지역 코드가 겹침 — {codes}"

    points = {k: s.current.observation_point for k, s in snapshots.items()}
    assert len(set(points.values())) == len(REGIONS), f"관측 지점이 겹침 — {points}"


def test_세_지역이_같은_형태의_데이터를_준다(snapshots):
    """한 지역만 필드가 빠지면 리포트가 그 칸만 비워 낸다.

    지역별 검증은 '각자 멀쩡한가'를 보고, 이 검증은 '셋이 같은 모양인가'를 본다.
    """
    shapes = {
        k: (
            len(s.hourly) > 0,
            s.current.condition != "",
            len(s.current.precip_prob_pct) > 0,
        )
        for k, s in snapshots.items()
    }
    assert len(set(shapes.values())) == 1, f"지역별 데이터 형태가 다름 — {shapes}"


@pytest.mark.parametrize("key", [r.key for r in REGIONS])
def test_수집_시각이_하나의_스냅샷으로_묶여_있다(snapshots, key):
    """세 지역을 다른 시각에 긁으면 비교 자체가 성립하지 않는다.

    같은 실행 안에서 수집됐는지를 날짜·시(hour) 단위로 확인한다.
    """
    stamps = {s.collected_at[:13] for s in snapshots.values()}
    assert len(stamps) == 1, f"수집 시각이 흩어져 있음 — {sorted(stamps)}"
