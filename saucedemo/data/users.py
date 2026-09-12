"""테스트 계정.

계정을 코드에서 분리해 둔다. 시나리오는 "어떤 성격의 계정인가"만 알면 되고,
계정이 바뀌어도 테스트 본문은 손대지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass

PASSWORD = "secret_sauce"


@dataclass(frozen=True)
class User:
    username: str
    password: str
    label: str


STANDARD = User("standard_user", PASSWORD, "정상 계정")
LOCKED_OUT = User("locked_out_user", PASSWORD, "잠긴 계정")
PROBLEM = User("problem_user", PASSWORD, "결함 보유 계정")
PERFORMANCE_GLITCH = User("performance_glitch_user", PASSWORD, "응답 지연 계정")

# ── 로그인 시나리오 입력값 ──────────────────────────────────────────
# 동등 분할: 정상 / 잠김 / 미입력 / 자격증명 불일치 4개 클래스.
# 같은 "실패"라도 사용자에게 다른 메시지가 나가야 하므로 기대 메시지까지 고정한다.
LOGIN_CASES = [
    (
        "빈 아이디",
        "",
        PASSWORD,
        "Epic sadface: Username is required",
    ),
    (
        "빈 비밀번호",
        STANDARD.username,
        "",
        "Epic sadface: Password is required",
    ),
    (
        "비밀번호 불일치",
        STANDARD.username,
        "wrong_password",
        "Epic sadface: Username and password do not match any user in this service",
    ),
    (
        "잠긴 계정",
        LOCKED_OUT.username,
        PASSWORD,
        "Epic sadface: Sorry, this user has been locked out.",
    ),
]
