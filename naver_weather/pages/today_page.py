"""weather.naver.com/today/{지역코드} — 시간별 예보 표.

강수량(mm)은 이 화면에만 있다. 검색 카드는 강수'확률'까지만 준다.
둘은 다른 값이므로 한 화면에서 다 읽은 척하지 않는다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from playwright.sync_api import Page, expect

from naver_weather.pages.base_page import BasePage, ParseError, to_number_or_none

TODAY_URL = "https://weather.naver.com/today/{code}"

# 표의 행 라벨. 화면에는 '강수량 (mm)' 처럼 단위가 붙어 있어 앞부분으로 찾는다.
ROW_TEMP = "기온"
ROW_PRECIP_PROB = "강수확률"
ROW_PRECIP_MM = "강수량"
ROW_HUMIDITY = "습도"


# 자정 칸은 시각 대신 날짜 라벨이 붙는다. '0시' 가 아니라 '내일' · '모레' 로 온다.
# 이걸 모르고 '…시' 만 골라내면 **하루에 한 칸씩 조용히 빠진다.**
# 실제로 첫 실행에서 `23시 → 1시` 로 시간이 끊겨 잡혔다.
DAY_MARKERS = {"내일": 1, "모레": 2}


@dataclass
class HourlyPoint:
    hour_label: str        # '12시'
    day_offset: int        # 0=오늘 · 1=내일 · 2=모레
    condition: str         # '흐림'
    temperature_c: float | None
    precip_prob_pct: float | None
    precip_mm: float | None
    humidity_pct: float | None

    def as_dict(self) -> dict:
        return asdict(self)


class TodayPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # 시간별 표는 '강수량' 행을 가진 표 하나로 특정한다.
        # nth(0) 으로 잡지 않는 이유 — 페이지에 표가 10개 있고 순서는 보장되지 않는다.
        self.table = page.locator("table").filter(has_text=ROW_PRECIP_MM).first

    def open(self, region_code: str) -> "TodayPage":
        self.page.goto(TODAY_URL.format(code=region_code), wait_until="domcontentloaded")
        expect(self.table).to_be_visible()
        return self

    def location_name(self) -> str:
        """상세 화면이 말하는 지점명. 검색 카드와 같은 곳인지 대조하는 데 쓴다."""
        return self.page.locator(".location_name, .btn_select").first.inner_text().strip()

    def hourly(self) -> list[HourlyPoint]:
        """표를 시간 단위 레코드로 뒤집어 돌려준다.

        화면은 '행 = 항목 / 열 = 시간' 인데, 검증은 시간 단위로 하는 게 자연스럽다.
        표 모양 그대로 들고 다니면 테스트마다 인덱스 계산을 다시 하게 된다.
        """
        grid = self.page.evaluate(
            """(labels) => {
                 const t = [...document.querySelectorAll('table')]
                   .find(t => /강수량/.test(t.textContent));
                 if (!t) return null;
                 const clean = s => s.replace(/\\s+/g, ' ').trim();
                 const rows = [...t.rows].map(r => ({
                   head: clean(r.cells[0] ? r.cells[0].textContent : ''),
                   cells: [...r.cells].slice(1).map(c => clean(c.textContent)),
                 }));
                 return rows;
               }""",
            None,
        )
        if not grid:
            raise ParseError("시간별 표를 찾지 못함")

        header = grid[0]["cells"]          # '12시 흐림' · '18:46 일몰' 이 섞여 있다
        rows = {r["head"].split(" ")[0]: r["cells"] for r in grid[1:] if r["head"]}

        def col(label: str, i: int) -> str | None:
            values = rows.get(label)
            return values[i] if values and i < len(values) else None

        points: list[HourlyPoint] = []
        day = 0
        for i, head in enumerate(header):
            first, _, rest = head.partition(" ")
            if first.endswith("시") and first.removesuffix("시").isdigit():
                hour = first
            elif first in DAY_MARKERS:
                day = DAY_MARKERS[first]
                hour = "0시"
            else:
                # 일출·일몰 칸은 시간별 예보가 아니다. 값이 비는 게 정상이라 건너뛴다.
                continue
            points.append(
                HourlyPoint(
                    hour_label=hour,
                    day_offset=day,
                    condition=rest.strip(),
                    temperature_c=to_number_or_none(col(ROW_TEMP, i)),
                    precip_prob_pct=to_number_or_none(col(ROW_PRECIP_PROB, i)),
                    precip_mm=to_number_or_none(col(ROW_PRECIP_MM, i)),
                    humidity_pct=to_number_or_none(col(ROW_HUMIDITY, i)),
                )
            )
        if not points:
            raise ParseError("표는 찾았으나 시간 칸이 하나도 없음")
        return points
