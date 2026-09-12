"""지역 하나를 두 화면에 걸쳐 수집한다.

  검색 카드(현재 관측값) → 카드가 들고 있는 지역 코드 → 상세(시간별 강수량)

주소를 미리 적어 두지 않고 **카드가 실제로 가리키는 링크**를 따라간다.
그래야 링크가 엉뚱한 지역을 가리키는 날 그 사실이 잡힌다.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page

from naver_weather.data.regions import REGIONS, Region
from naver_weather.pages.search_weather_page import CurrentWeather, SearchWeatherPage
from naver_weather.pages.today_page import HourlyPoint, TodayPage


@dataclass
class RegionSnapshot:
    region: Region
    current: CurrentWeather
    hourly: list[HourlyPoint]
    detail_location: str
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    # ── 파생값 ──────────────────────────────────────────────
    @property
    def total_precip_mm(self) -> float:
        return round(sum(p.precip_mm or 0.0 for p in self.hourly), 1)

    @property
    def max_precip_prob(self) -> float:
        return max((p.precip_prob_pct or 0.0 for p in self.hourly), default=0.0)

    @property
    def rain_hours(self) -> list[HourlyPoint]:
        return [p for p in self.hourly if (p.precip_mm or 0.0) > 0]

    def as_dict(self) -> dict:
        return {
            "region": asdict(self.region),
            "collected_at": self.collected_at,
            "detail_location": self.detail_location,
            "current": self.current.as_dict(),
            "hourly": [h.as_dict() for h in self.hourly],
            "total_precip_mm": self.total_precip_mm,
            "max_precip_prob": self.max_precip_prob,
        }


def collect_region(page: Page, region: Region) -> RegionSnapshot:
    search = SearchWeatherPage(page).open(region.query)
    current = search.read(region.key, region.query)

    today = TodayPage(page).open(current.region_code)
    return RegionSnapshot(
        region=region,
        current=current,
        hourly=today.hourly(),
        detail_location=today.location_name(),
    )


def collect_all(page: Page) -> list[RegionSnapshot]:
    return [collect_region(page, r) for r in REGIONS]


def save_json(snapshots: list[RegionSnapshot], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([s.as_dict() for s in snapshots], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":  # 수동 실행용: python collector.py
    from playwright.sync_api import sync_playwright

    from naver_weather.conftest import USER_AGENT

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(locale="ko-KR", timezone_id="Asia/Seoul", user_agent=USER_AGENT)
        pg = ctx.new_page()
        pg.set_default_timeout(20_000)
        pg.set_default_navigation_timeout(45_000)
        snaps = collect_all(pg)
        out = save_json(snaps, Path("out/snapshot.json"))
        browser.close()

    for s in snaps:
        print(
            f"{s.current.title:10} {s.current.temperature_c:5.1f}°  {s.current.condition:6} "
            f"강수 {s.total_precip_mm:4.1f}mm  최대확률 {s.max_precip_prob:3.0f}%  "
            f"({s.current.observation_point})"
        )
    print(f"\n→ {out}")
