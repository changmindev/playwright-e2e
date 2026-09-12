"""로그인 화면."""

from __future__ import annotations

from playwright.sync_api import Page

from saucedemo.data.users import User
from saucedemo.pages.base_page import BASE_URL, BasePage


class LoginPage(BasePage):
    URL = f"{BASE_URL}/"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username = page.get_by_test_id("username")
        self.password = page.get_by_test_id("password")
        self.login_button = page.get_by_test_id("login-button")
        self.error = page.get_by_test_id("error")

    def open(self) -> "LoginPage":
        self.page.goto(self.URL)
        return self

    def submit(self, username: str, password: str) -> None:
        """빈 값 케이스도 그대로 흘려보낸다. fill('') 은 입력칸을 비우는 동작이라
        '미입력' 상태를 만드는 데 그대로 쓸 수 있다."""
        self.username.fill(username)
        self.password.fill(password)
        self.login_button.click()

    def login_as(self, user: User) -> None:
        self.submit(user.username, user.password)
