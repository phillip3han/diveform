# 변경 기록

## 2026-11-19 — Claude 인수
- **수정: 실제 영상 추적률 0%** — `detectBest`가 프레임당 타임스탬프 하나를 최대 14번의 크롭 추론에 재사용 → MediaPipe 그래프가 "Packet timestamp mismatch"로 오류 상태가 되어 이후 전 프레임 실패. try/catch가 예외를 삼켜 "검출 실패"로만 보였음. Pose를 IMAGE 모드 + `detect()`로 변경 (크롭마다 독립 추론)
- **수정: 모션 재구성 화면 예외** — 정의되지 않은 `rbones()` 호출로 재구성 렌더가 중단되던 문제. 재구성 좌표계 스켈레톤 함수 추가
- 추가: `tools/e2e.py` 헤드리스 Chrome 엔드투엔드 검증, `CLAUDE.md`, `docs/`

## 2026-11-16 — Genspark 5f28983
- 관절 추적 앱 + 형태 분석 도구, 모델 내장, 스무딩, CSV 내보내기, Pages 워크플로
