# Tester Handover

## Test Scope
콘솔 줌인(터미널 리사이즈) 시 `rich.Live` 레이아웃 깨짐 현상 분석 및 수정 방향 검토.
대상 파일: `ensure_wifi_expected_ssids_watched.py`

## Test Cases
| Case | Input | Expected | Result |
|------|-------|----------|--------|
| TC-01 | 콘솔 줌인 (터미널 폭 축소) | 레이아웃 유지 | FAIL |
| TC-02 | 콘솔 줌아웃 (터미널 폭 확대) | 레이아웃 유지 | FAIL |
| TC-03 | 리사이즈 없이 정상 실행 | 주기적 갱신 정상 | PASS |

## Coverage
- `ensure_wifi_expected_ssids_watched()` 함수 내 `Live` 생성/업데이트 로직 검토
- `get_rich_console()` 호출 시점 분석 (Live 시작 시 1회만 생성 → 이후 폭 고정)
- `shutil.get_terminal_size()` 재감지 미적용 확인

## Root Cause
`Live` 생성 시 `Console` 1회 고정 → 이후 터미널 폭 변경 미감지.  
`screen=False` 모드에서 rich가 resize 이벤트 자동 처리 안 함.

## Fix Proposal
터미널 크기 변경 감지 시 `Live` 컨텍스트 재시작.  
구체적 방법: 루프 내 `shutil.get_terminal_size()` 비교 → 크기 변경 시 `Live` 종료 후 재진입.

## Pass / Fail
- Total: 3
- Pass: 1
- Fail: 2

## Next Role
upserter (fix needed)

## Notes
- 수정 대상: `ensure_wifi_expected_ssids_watched.py` 내 `ensure_wifi_expected_ssids_watched()` 함수
- `Live` 재시작 패턴 적용 권장 (방법 1)
- `screen=True` 방법은 UI 스타일 변경 부작용 있어 비권장
