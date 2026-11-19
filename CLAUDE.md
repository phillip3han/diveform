# DiveForm — 작업 안내 (Claude용)

수영 스타트 다이빙 영상을 올리면 브라우저 안에서 관절을 추적해 세트 → 이륙 → 입수 동작을 재구성하고,
이상 각도(이륙 35°, 4.5 m/s, 입수 35°)와 비교해 보여주는 정적 웹앱. 서버 없음, 빌드 없음.

## 파일
- `index.html` — 관절 추적 앱 전체 (HTML+CSS+JS 단일 파일, ~2,300줄). MediaPipe Tasks Vision 사용
- `shape.html` — 관절 엔진 없이 박스 3점(이륙·정점·입수)으로 탄도 재구성하는 보조 도구
- `vendor/` — MediaPipe 번들·WASM·모델(.task) 내장본 41MB. 지우지 말 것 (CDN 차단 환경 대응)
- `tools/e2e.py` — 헤드리스 Chrome으로 실제 영상을 올려 끝까지 돌리는 검증 스크립트
- `docs/` — 기획·설계·환경·이력 문서. 큰 결정을 바꾸면 해당 문서도 갱신

## 실행
```bash
python3 -m http.server 8080   # http://localhost:8080/index.html
```
`file://`로 열면 ES 모듈·WASM이 막힘.

## 검증 규칙 (중요)
코드 수정 뒤에는 반드시 실제 영상으로 `tools/e2e.py`를 돌려 추적률·리포트가 나오는지 확인한다.
Genspark 시절 "수정했다"는 보고가 여러 번 실제 브라우저에서는 0%였다. 렌더 스크린샷만으로 완료 처리하지 말 것.

```bash
python3 tools/e2e.py /path/v1.h264.mp4 --shot /tmp/e2e --timeout 3000000
```
- 클라우드 작업 공간 Chrome은 HEVC(H.265)를 못 읽는다 → 테스트 전 `ffmpeg -c:v libx264`로 변환
- 소프트웨어 GL이라 영상 1개에 10~15분 걸림. 백그라운드로 돌리고 로그를 볼 것
- 테스트 영상은 저장소에 넣지 않는다(사용자 Mac `~/Downloads/_talkv_*.MP4`, docs/testing 참고)

## 코드 규칙
- 포즈 엔진은 `runningMode: "IMAGE"` + `poseLK.detect()`. 크롭마다 다른 이미지를 넣으므로 VIDEO 모드(타임스탬프·추적 상태) 쓰지 말 것
- 각도 정의가 셋 다 다르다: 세트 = 관절 내각, 이륙 = 무게중심 속도벡터 vs 수평, 입수 = 신체축 vs 수면
- 사용자 대면 문구는 한국어
- 커밋은 `main`. GitHub Pages 워크플로(`.github/workflows/pages.yml`)가 main 푸시 시 배포
