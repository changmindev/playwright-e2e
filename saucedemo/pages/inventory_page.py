"""상품 목록 화면."""

from __future__ import annotations

from decimal import Decimal

from playwright.sync_api import Page

from saucedemo.pages.base_page import BASE_URL, BasePage, to_money

# 정렬 드롭다운의 value → 사람이 읽는 이름
SORT_OPTIONS = {
    "az": "Name (A to Z)",
    "za": "Name (Z to A)",
    "lohi": "Price (low to high)",
    "hilo": "Price (high to low)",
}


class InventoryPage(BasePage):
    URL = f"{BASE_URL}/inventory.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.sort_dropdown = page.get_by_test_id("product-sort-container")
        self.items = page.get_by_test_id("inventory-item")
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.item_prices = page.get_by_test_id("inventory-item-price")

    def open(self) -> "InventoryPage":
        self.page.goto(self.URL)
        return self

    # ── 읽기 ────────────────────────────────────────────────────
    def names(self) -> list[str]:
        return [t.strip() for t in self.item_names.all_text_contents()]

    def prices(self) -> list[Decimal]:
        return [to_money(t) for t in self.item_prices.all_text_contents()]

    def image_sources(self) -> list[str]:
        """상품 이미지 경로 목록.

        이미지가 '보이는지'만 보면 안 된다. 깨진 이미지도 대체 이미지로
        채워져 있으면 화면에는 멀쩡히 뜬다. 실제 경로를 읽어야 판정된다."""
        return self.page.locator(".inventory_item_img img").evaluate_all(
            "els => els.map(e => e.getAttribute('src'))"
        )

    def image_src(self, slug: str) -> str:
        return self.page.get_by_test_id(f"inventory-item-{slug}-img").get_attribute("src")

    # ── 조작 ────────────────────────────────────────────────────
    def sort_by(self, value: str) -> None:
        self.sort_dropdown.select_option(value)

    def add_to_cart(self, slug: str) -> None:
        self.page.get_by_test_id(f"add-to-cart-{slug}").click()

    def remove_from_cart(self, slug: str) -> None:
        self.page.get_by_test_id(f"remove-{slug}").click()

    def remove_button(self, slug: str):
        return self.page.get_by_test_id(f"remove-{slug}")

    def add_button(self, slug: str):
        return self.page.get_by_test_id(f"add-to-cart-{slug}")

    def open_detail_by_index(self, index: int) -> None:
        """화면에 보이는 순서로 n번째 상품명을 누른다.

        data-test 의 item-N-title-link 에서 N 은 화면 순서가 아니라 상품 고유
        id 다. 순서로 접근할 때 그 숫자를 쓰면 엉뚱한 상품을 누르게 된다."""
        self.item_names.nth(index).click()

    def open_detail_by_name(self, name: str) -> None:
        """상품명으로 찾아 상세로 들어간다. 정렬이 바뀌어도 같은 상품을 연다."""
        self.item_names.filter(has_text=name).first.click()
