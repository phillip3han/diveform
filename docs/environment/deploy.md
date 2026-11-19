# 배포

## GitHub
- 저장소: `phillip3han/diveform` (**public**, 2026-11-19 전환)
- 브랜치: `main`

## GitHub Pages
`.github/workflows/pages.yml`이 main 푸시마다 저장소 루트를 그대로 배포.
설정 완료 (Source = GitHub Actions, 2026-11-19). 배포 확인: 내장 엔진 로드까지 정상.
- **운영 주소: https://phillip3han.github.io/diveform/**
- 관절 추적: `https://<계정>.github.io/diveform/`
- 형태 분석: `https://<계정>.github.io/diveform/shape.html`
private 저장소의 Pages는 유료 플랜에서만 가능 (무료면 public으로 하거나 다른 호스팅).

## 대안
Netlify / Vercel / Cloudflare Pages에 폴더 그대로 업로드 (빌드 명령 없음, 출력 폴더 = 루트).
`vendor/`가 41MB라 Git LFS는 필요 없음 (파일당 100MB 미만).

## 예전 주소
Genspark 샌드박스 주소(`*.sandbox.westus2-prod.sspark.ai`)는 임시였음. 사용하지 말 것.
