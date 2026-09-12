"""공통 설정과 픽스처.

수집은 **세션당 한 번만** 한다. 테스트마다 다시 긁으면
(1) 같은 대상을 수십 번 두드리게 되고
(2) 테스트 A 와 테스트 B 가 서로 다른 시각의 값을 보게 되어
    "A 는 통과인데 B 는 실패"가 제품 문제인지 시차 문제인지 구분이 안 된다.
"""

from __future__ import annotations

import pytest

from naver_weather.collector import RegionSnapshot, collect_region
from naver_weather.data.regions import REGIONS

# 대상이 우리 통제 밖의 외부 사이트다. 응답이 느려지는 날을 정상 범위로 인정한다.
ACTION_TIMEOUT_MS = 20_000
NAVIGATION_TIMEOUT_MS = 45_000
EXPECT_TIMEOUT_MS = 15_000

# 기본 헤드리스 UA 는 'HeadlessChrome' 이 그대로 박혀 있다.
# 우리가 확인하려는 것은 '봇 차단이 되는가'가 아니라 '날씨 값이 맞는가'라서
# 일반 브라우저와 같은 조건으로 맞춰 둔다.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)


def pytest_configure(config: pytest.Config) -> None:
    from playwright.sync_api import expect

    expect.set_options(timeout=EXPECT_TIMEOUT_MS)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "locale": "ko-KR",
        "timezone_id": "Asia/Seoul",
        "user_agent": USER_AGENT,
    }


@pytest.fixture(autouse=True)
def apply_timeouts(page) -> None:
    page.set_default_timeout(ACTION_TIMEOUT_MS)
    page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)


@pytest.fixture(scope="session")
def snapshots(browser) -> dict[str, RegionSnapshot]:
    """3개 지역을 한 번 수집해 세션 내내 공유한다."""
    context = browser.new_context(
        locale="ko-KR", timezone_id="Asia/Seoul", user_agent=USER_AGENT
    )
    page = context.new_page()
    page.set_default_timeout(ACTION_TIMEOUT_MS)
    page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
    try:
        result = {r.key: collect_region(page, r) for r in REGIONS}
    finally:
        context.close()
    return result


@pytest.fixture(params=[r.key for r in REGIONS], ids=[r.key for r in REGIONS])
def snapshot(request, snapshots) -> RegionSnapshot:
    """지역별로 같은 검증을 반복하기 위한 파라미터 픽스처.

    실패했을 때 어느 지역인지 id 로 바로 보이게 한다 —
    '3건 실패'보다 'gangwon 만 실패'가 훨씬 빠른 단서다.
    """
    return snapshots[request.param]
