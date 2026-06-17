# Upserter Handover

## Change Summary
터미널 리사이즈 시 `rich.Live` 레이아웃 깨짐 수정.  
크기 변경 감지 시 `Live` 컨텍스트 재시작 패턴 적용.

## Files Changed
| File | Type | Description |
|------|------|-------------|
| ensure_wifi_expected_ssids_watched.py | update | `import shutil` 추가, outer while loop + 터미널 크기 감지 후 Live 재시작 |

## Diff Summary
- `import shutil` 추가 (line 4)
- `ensure_wifi_expected_ssids_watched()`: 기존 `with Live` 블록을 `while True` outer loop로 감쌈
- `console`, `current_terminal_size` outer loop 진입 시마다 재생성
- inner loop 끝에 `shutil.get_terminal_size() != current_terminal_size` 시 `break` → outer loop가 `Live` 재시작

## Next Role
tester

## Notes
- `screen=True` 방식 사용 안 함 (UI 스타일 변경 부작용)
- 최소 변경 원칙 준수 — 로직 변경 없음
