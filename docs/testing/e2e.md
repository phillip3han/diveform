# 엔드투엔드 검증

`tools/e2e.py`가 헤드리스 Chrome으로 `index.html`을 띄우고 실제 영상을 `#file`에 넣어
엔진 로드 → 관절 추적 → 리포트까지 돌린 뒤 추적률·방향·국면·점수·오류 로그를 출력한다.

```bash
pip install playwright        # 브라우저는 시스템 Chrome 사용 (CHROME 환경변수로 경로 변경)
ffmpeg -i in.MP4 -c:v libx264 -crf 20 -pix_fmt yuv420p -an v1.h264.mp4   # HEVC면 변환
python3 tools/e2e.py v1.h264.mp4 --shot /tmp/e2e --timeout 3000000
```
- 소프트웨어 GL 환경에서는 영상 1개에 10–15분. 실제 PC 브라우저는 훨씬 빠름
- 통과 기준: 추적률 ≥ 60%, 점수 카드 표시, `[pageerror]` 없음

## 테스트 영상 (저장소 미포함, 사용자 Mac `~/Downloads/`)
| 이름 | 원본 파일 | 해상도·코덱 | 특성 |
|---|---|---|---|
| v1 | `_talkv_dJMcau9YCCk_…MP4` | 1280×720 HEVC 30fps 6.3s | 측면에 가까움 |
| v2 | `_talkv_dJMcbaRDNsR_…MP4` | 1920×1080 HEVC 30fps 9.6s | 사선 뷰 |
| v3 | `_talkv_dJMcbfk6Xjw_…MP4` | 1920×1080 HEVC 29.97fps 8.5s | 원경 + 주변 인물 |
| v4 | `_talkv_wz5yEbKPyE_…MP4` | 1280×720 HEVC 29fps 11.7s | 인물 매우 작음 |
