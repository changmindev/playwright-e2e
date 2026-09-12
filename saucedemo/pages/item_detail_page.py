"""상품 상세 화면."""

from __future__ import annotations

from decimal import Decimal

from playwright.sync_api import Page

from saucedemo.pages.base_page import BASE_URL, BasePage, to_money


class ItemDetailPage(BasePage):
    URL = f"{BASE_URL}/inventory-item.html"
    #: 목록 화면에는 없는 요소. 화면이 실제로 교체됐는지 가르는 기준.
    READY_TEST_ID = "back-to-products"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.name = page.get_by_test_id("inventory-item-name")
        self.description = page.get_by_test_id("inventory-item-desc")
        self.price = page.get_by_test_id("inventory-item-price")
        self.back_button = page.get_by_test_id("back-to-products")

    def name_text(self) -> str:
        self.ensure_ready()
        return (self.name.text_content() or "").strip()

    def price_value(self) -> Decimal:
        self.ensure_ready()
        return to_money(self.price.text_content())

    def item_id(self) -> str:
        """URL 의 ?id= 값. 어떤 상품으로 이동했는지 판정하는 근거로 쓴다."""
        self.ensure_ready()
        return self.page.url.partition("?id=")[2]
