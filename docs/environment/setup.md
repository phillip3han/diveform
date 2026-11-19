# 실행 환경

## 요구
- 최신 Chrome / Edge / Safari (WebAssembly, ES 모듈). WebGL 있으면 GPU, 없으면 CPU
- 로컬 웹서버 (`file://` 불가)

## 로컬 실행
```bash
git clone https://github.com/<계정>/diveform.git && cd diveform
python3 -m http.server 8080
# http://localhost:8080/index.html  (관절 추적)
# http://localhost:8080/shape.html  (형태 분석)
```

## 의존성 (빌드 없음)
| 파일 | 출처 |
|---|---|
| vendor/vision_bundle.mjs, vendor/wasm/* | @mediapipe/tasks-vision 0.10.14 (Apache-2.0) |
| vendor/pose_landmarker_full.task (+lite) | MediaPipe Pose Landmarker float16 |
| vendor/hand_landmarker.task | MediaPipe Hand Landmarker float16 |
로딩 순서: 내장 → CDN(`cdn.jsdelivr.net`, `storage.googleapis.com`).

## 영상 코덱
아이폰 기본 촬영은 HEVC(H.265). Safari·macOS Chrome(하드웨어 지원 시)은 재생되지만, 일부 환경(리눅스 Chrome 등)은 못 읽어 "영상 메타데이터를 읽을 수 없습니다"가 뜬다. 이때는 아이폰 설정 > 카메라 > 포맷 > "높은 호환성"으로 찍거나 H.264로 변환.

## 개발 도구 (검증용)
Python 3 + playwright, Google Chrome, ffmpeg → testing/e2e.md
