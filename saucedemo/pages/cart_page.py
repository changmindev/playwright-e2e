"""장바구니 화면."""

from __future__ import annotations

from decimal import Decimal

from playwright.sync_api import Page

from saucedemo.pages.base_page import BASE_URL, BasePage, to_money


class CartPage(BasePage):
    URL = f"{BASE_URL}/cart.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.items = page.get_by_test_id("inventory-item")
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.item_prices = page.get_by_test_id("inventory-item-price")
        self.checkout_button = page.get_by_test_id("checkout")
        self.continue_shopping_button = page.get_by_test_id("continue-shopping")

    def open(self) -> "CartPage":
        self.page.goto(self.URL)
        return self

    def names(self) -> list[str]:
        return [t.strip() for t in self.item_names.all_text_contents()]

    def prices(self) -> list[Decimal]:
        return [to_money(t) for t in self.item_prices.all_text_contents()]

    def remove(self, slug: str) -> None:
        self.page.get_by_test_id(f"remove-{slug}").click()

    def checkout(self) -> None:
        self.checkout_button.click()
