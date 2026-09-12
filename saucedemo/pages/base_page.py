"""Page Object 공통 기반.

원칙 두 가지만 지킨다.
  1. 셀렉터는 이 계층 밖으로 새지 않는다. 테스트 본문에 CSS 문자열이 보이면 안 된다.
  2. 명시적 sleep 을 쓰지 않는다. 대기는 expect()/wait_for_url 의 자동 대기에 맡긴다.
"""

from __future__ import annotations

from decimal import Decimal

from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"


def to_money(text: str) -> Decimal:
    """'$29.99', 'Item total: $39.98' 같은 표시값에서 금액만 뽑는다.

    금액은 float 이 아니라 Decimal 로 다룬다. 0.1 + 0.2 != 0.3 문제가
    합계 검증에서 그대로 오탐이 되기 때문이다.
    """
    return Decimal(text.split("$")[-1].strip())


class BasePage:
    #: 이 페이지 객체가 서 있어야 할 주소. 하위 클래스가 채운다.
    URL: str | None = None

    #: 이 화면에만 있는 요소의 test id. 주소는 화면보다 먼저 바뀌므로 같이 본다.
    READY_TEST_ID: str | None = None

    def __init__(self, page: Page) -> None:
        self.page = page

    def ensure_ready(self) -> None:
        """자기 화면이 실제로 그려질 때까지 기다린다.

        saucedemo 의 상품명 링크는 `<a href="#">` 라 클릭이 이동을 **시작만 하고
        곧바로 반환된다.** 그 직후에 값을 읽으면 아직 이전 화면이다.

        성가신 건 에러가 나서가 아니다. 즉시 읽기(`text_content` ·
        `all_text_contents` · `count`)는 **자동 대기를 하지 않는다.** 그래서 잘못된
        화면에서도 빈 리스트나 남의 상품 이름을 **조용히 돌려준다.**
        운이 좋으면 strict mode 위반으로 터지고, 운이 나쁘면 그냥 통과한다.
        후자가 훨씬 위험하다 — 통과한 테스트는 아무도 다시 안 본다.

        🔴 **주소만으로는 부족하다.** 이 사이트는 URL 을 먼저 바꾸고 화면을
        나중에 그린다. 실제로 측정해 보면 이렇다.

            t+  0ms  url=checkout-step-two.html  상품명 0개  firstName 1개  ← 아직 이전 화면
            t+300ms  url=checkout-step-two.html  상품명 1개  firstName 0개  ← 이제 교체됨

        `wait_for_url` 은 t+0 에 곧바로 통과한다. 그래서 **그 화면에만 있는
        요소**까지 붙었는지 같이 본다. 요소가 '보이는지'가 아니라 '붙었는지'를
        보는 이유는, 목록에도 '상품명' 요소가 있어서 잘못된 화면에서도
        눈에는 멀쩡히 보이기 때문이다 — 화면을 가르는 건 그 화면에만 있는 요소다.

        이동을 일으키는 쪽(`click`)이 아니라 **도착한 쪽이 확인한다.**
        같은 버튼이 성공하면 다음 화면으로, 실패하면 제자리에 머무는 경우가
        있기 때문이다(체크아웃 정보 입력이 그렇다). 누르는 쪽에서 이동을
        단정하면 오류 경로 테스트가 죽는다.
        """
        if self.URL:
            self.page.wait_for_url(f"{self.URL}*")
        if self.READY_TEST_ID:
            expect(self.page.get_by_test_id(self.READY_TEST_ID)).to_be_attached()

    # ── 공통 헤더 ────────────────────────────────────────────────
    @property
    def title_text(self):
        return self.page.get_by_test_id("title")

    @property
    def cart_badge(self):
        """장바구니 수량 뱃지. 0개일 때는 DOM 에 아예 없다(존재 여부로 판정)."""
        return self.page.get_by_test_id("shopping-cart-badge")

    def open_cart(self) -> None:
        self.page.get_by_test_id("shopping-cart-link").click()

    def open_menu(self) -> None:
        """햄버거 메뉴.

        data-test="open-menu" 는 <img> 라서 그대로 클릭하면
        상위의 <button id="react-burger-menu-btn"> 이 포인터 이벤트를 가로챈다.
        실제로 클릭을 받는 요소를 눌러야 한다. (DECISIONS.md 참고)
        """
        self.page.locator("#react-burger-menu-btn").click()
