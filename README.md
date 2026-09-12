# playwright-e2e

**외부 웹사이트를 대상으로 한 Playwright E2E 자동화 저장소.**

내가 통제할 수 없는 사이트를 대상으로 삼습니다. 화면이 언제든 바뀌고, 고쳐 달라고 할 수 없습니다.
그래서 여기서 다루는 건 "테스트를 통과시키는 법"이 아니라 **깨졌을 때 무엇이 깨졌는지 말할 수 있는 구조**입니다.

> 내가 만든 제품을 대상으로 한 E2E 는 별도 저장소에 있습니다 → [loyalhub-e2e](https://github.com/changmindev/loyalhub-e2e)
> 대상을 고칠 권한이 있느냐 없느냐에 따라 테스트 설계가 달라지기 때문에 저장소를 나눴습니다.

---

## 대상

| 스위트 | 대상 | 다루는 것 |
|---|---|---|
| `saucedemo/` | [saucedemo.com](https://www.saucedemo.com) | 로그인 · 장바구니 · 정렬 · 체크아웃, 그리고 **의도된 결함 탐지** |
| `naver-weather/` | 네이버 날씨 (서울 · 강원 · 경기) | 실시간 수집값의 **범위 · 계약 · 상호 일관성** 검증 |

---

## 상태

🚧 **구성 중.** 두 스위트를 이 저장소로 옮기는 작업이 진행 중이며, PR 단위로 들어옵니다.

- [ ] `naver-weather/` 이관 (pytest 53케이스)
- [ ] `saucedemo/` 이관 — 대상 사이트 개편으로 3건이 깨진 상태라 **수정 후** 반입
- [ ] GitHub Actions CI (`lint → test`)

---

## 실행

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
pytest
```

---

## 스택

```
Python · pytest · Playwright (sync API) · Page Object Model
```
