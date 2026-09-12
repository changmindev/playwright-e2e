"""테스트 공통 설정과 픽스처.

pytest-playwright 가 주는 page 픽스처를 그대로 쓰되,
(1) 셀렉터 기준을 data-test 로 바꾸고
(2) 로그인된 상태를 만들어 주는 픽스처를 얹는다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Playwright, expect

from saucedemo.data.users import PROBLEM, STANDARD, User
from saucedemo.pages.inventory_page import InventoryPage
from saucedemo.pages.login_page import LoginPage

# 기대 대기 상한. 기본 5초는 performance_glitch_user(실측 약 5.3초) 에서 걸린다.
# sleep 을 넣는 대신 상한만 올린다 — 빠르면 그만큼 빨리 끝난다.
EXPECT_TIMEOUT_MS = 15_000

# 조작·이동 상한. 대상이 우리 통제 밖의 공개 사이트라 응답이 느려지는 날이 있다.
# 실제로 8회 실행 중 1회, 평소 32초짜리 실행이 63초로 늘면서 픽스처 단계에서
# 시간이 초과된 적이 있다(테스트 실패가 아니라 error 로 잡혔다).
# 재시도로 덮지 않고, 느린 응답을 정상 범위로 인정해 상한만 올린다.
ACTION_TIMEOUT_MS = 20_000
NAVIGATION_TIMEOUT_MS = 45_000


def pytest_configure(config: pytest.Config) -> None:
    expect.set_options(timeout=EXPECT_TIMEOUT_MS)


@pytest.fixture(autouse=True)
def apply_timeouts(page) -> None:
    page.set_default_timeout(ACTION_TIMEOUT_MS)
    page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)


@pytest.fixture(scope="session", autouse=True)
def use_data_test_attribute(playwright: Playwright) -> None:
    """get_by_test_id 가 볼 속성을 data-testid → data-test 로 바꾼다.

    이 한 줄 덕분에 테스트 어디에도 CSS 문자열이 나오지 않는다.

    ⚠️ **이 설정은 프로세스 전역이다.** autouse 는 이 디렉터리 아래에만 걸리지만,
    한 번 바뀐 속성은 세션이 끝날 때까지 되돌아오지 않는다.
    즉 saucedemo 가 먼저 돈 뒤 다른 스위트가 `get_by_test_id` 를 쓰면
    그쪽도 `data-test` 를 보게 된다.

    지금은 문제가 없다 — naver_weather 는 `get_by_test_id` 를 쓰지 않는다(확인함).
    **`data-testid` 를 쓰는 스위트를 새로 넣는다면 여기서 충돌한다.**
    그때는 이 fixture 를 function 스코프로 내리고 끝나면 되돌려 놓아야 한다.
    """
    playwright.selectors.set_test_id_attribute("data-test")


@pytest.fixture()
def login_page(page) -> LoginPage:
    return LoginPage(page).open()


@pytest.fixture()
def logged_in(page):
    """계정을 받아 로그인까지 마치고 상품 목록 Page Object 를 돌려준다.

    반환이 아니라 팩토리인 이유: 같은 시나리오를 계정만 바꿔 돌리는
    케이스(정상 계정 vs 결함 계정)가 있어서다.
    """

    def _login(user: User = STANDARD) -> InventoryPage:
        LoginPage(page).open().login_as(user)
        inventory = InventoryPage(page)
        expect(inventory.items.first).to_be_visible()
        return inventory

    return _login


@pytest.fixture()
def inventory(logged_in) -> InventoryPage:
    """정상 계정으로 로그인된 상품 목록."""
    return logged_in(STANDARD)


@pytest.fixture()
def problem_inventory(logged_in) -> InventoryPage:
    """결함 보유 계정으로 로그인된 상품 목록."""
    return logged_in(PROBLEM)
