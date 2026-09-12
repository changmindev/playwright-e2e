"""체크아웃 화면 — 정보 입력(step one) / 요약(step two) / 완료."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from playwright.sync_api import Page

from saucedemo.data.products import TAX_RATE
from saucedemo.pages.base_page import BASE_URL, BasePage, to_money


class CheckoutInfoPage(BasePage):
    URL = f"{BASE_URL}/checkout-step-one.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.first_name = page.get_by_test_id("firstName")
        self.last_name = page.get_by_test_id("lastName")
        self.postal_code = page.get_by_test_id("postalCode")
        self.continue_button = page.get_by_test_id("continue")
        self.cancel_button = page.get_by_test_id("cancel")
        self.error = page.get_by_test_id("error")

    def open(self) -> "CheckoutInfoPage":
        self.page.goto(self.URL)
        return self

    def fill_form(self, first: str, last: str, postal: str) -> None:
        self.first_name.fill(first)
        self.last_name.fill(last)
        self.postal_code.fill(postal)

    def submit(self, first: str, last: str, postal: str) -> None:
        self.fill_form(first, last, postal)
        self.continue_button.click()

    def entered_values(self) -> tuple[str, str, str]:
        """입력칸에 실제로 남은 값. '넣었다'와 '들어갔다'는 다른 사실이라 따로 읽는다."""
        return (
            self.first_name.input_value(),
            self.last_name.input_value(),
            self.postal_code.input_value(),
        )


class CheckoutSummaryPage(BasePage):
    URL = f"{BASE_URL}/checkout-step-two.html"
    #: 정보 입력 화면에는 없는 요소. 주소가 먼저 바뀌므로 이걸로 교체를 확인한다.
    READY_TEST_ID = "checkout-summary-container"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.item_prices = page.get_by_test_id("inventory-item-price")
        self.subtotal_label = page.get_by_test_id("subtotal-label")
        self.tax_label = page.get_by_test_id("tax-label")
        self.total_label = page.get_by_test_id("total-label")
        self.finish_button = page.get_by_test_id("finish")

    def names(self) -> list[str]:
        self.ensure_ready()
        return [t.strip() for t in self.item_names.all_text_contents()]

    def prices(self) -> list[Decimal]:
        self.ensure_ready()
        return [to_money(t) for t in self.item_prices.all_text_contents()]

    def subtotal(self) -> Decimal:
        self.ensure_ready()
        return to_money(self.subtotal_label.text_content())

    def tax(self) -> Decimal:
        self.ensure_ready()
        return to_money(self.tax_label.text_content())

    def total(self) -> Decimal:
        self.ensure_ready()
        return to_money(self.total_label.text_content())

    def finish(self) -> None:
        self.finish_button.click()

    @staticmethod
    def expected_tax(subtotal: Decimal) -> Decimal:
        """세액을 화면에서 읽지 않고 직접 계산한다.

        화면값끼리 비교하면 서버가 둘 다 틀리게 줘도 통과한다.
        기준값은 테스트가 계산해서 들고 있어야 한다."""
        return (subtotal * TAX_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CheckoutCompletePage(BasePage):
    URL = f"{BASE_URL}/checkout-complete.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.header = page.get_by_test_id("complete-header")
        self.text = page.get_by_test_id("complete-text")
        self.back_home_button = page.get_by_test_id("back-to-products")
