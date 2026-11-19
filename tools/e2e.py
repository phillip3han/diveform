#!/usr/bin/env python3
"""DiveForm 엔드투엔드 검증: 헤드리스 Chrome에서 index.html에 실제 영상을 올려
엔진 로드 → 관절 추적 → 리포트까지 돌리고 결과를 출력한다.

사용법:
  python3 tools/e2e.py VIDEO [VIDEO ...] [--shot out.png]
"""
import argparse, functools, http.server, os, socketserver, sys, threading, time
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    h.log_message = lambda *a, **k: None
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def run(page, base, video, shot, timeout):
    logs = []
    page.on("console", lambda m: logs.append(f"[{m.type}] {m.text}"))
    page.on("pageerror", lambda e: logs.append(f"[pageerror] {e}"))
    page.goto(base + "/index.html")
    page.wait_for_function(
        "() => /준비|실패/.test(document.getElementById('engine').textContent)", timeout=120000)
    engine = page.inner_text("#engine")
    t0 = time.time()
    page.set_input_files("#file", video)
    done_js = """() => !document.getElementById('cardScore').classList.contains('hide')
               || /실패/.test(document.getElementById('steps').textContent)"""
    while not page.evaluate(done_js) and time.time() - t0 < timeout / 1000:
        print(f"   … {time.time()-t0:5.0f}s  progress={page.evaluate('document.getElementById(\"prog\").style.width')}", flush=True)
        time.sleep(30)
    page.wait_for_function(
        """() => !document.getElementById('cardScore').classList.contains('hide')
               || /실패/.test(document.getElementById('steps').textContent)
               || /엔진 없음/.test(document.getElementById('engine').textContent)""",
        timeout=timeout)
    took = time.time() - t0
    out = {
        "video": os.path.basename(video), "engine": engine, "sec": round(took, 1),
        "track": page.inner_text("#mTrack"), "dir": page.inner_text("#mDir"),
        "phase": page.inner_text("#mPhase"),
        "score": page.inner_text("#score") if page.is_visible("#score") else "—",
        "steps": page.inner_text("#steps").replace("\n", " | "),
    }
    if shot:
        page.screenshot(path=shot, full_page=True)
        dump = page.evaluate("""() => { const S = window.__DF; if (!S || !S.frames) return null;
            return { track: S.track || null, w: S.src && S.src.w, h: S.src && S.src.h, flip: !!(S.src && S.src.flip),
                     phases: S.res && S.res.phases, metrics: S.res && S.res.metrics,
                     frames: S.frames.map(f => ({ t: f.t, full: f.full || null, interp: !!f.interp })) }; }""")
        if dump:
            import json
            json.dump(dump, open(shot.replace(".png", ".json"), "w"))
    errs = [l for l in logs if l.startswith(("[error]", "[pageerror]", "[warning]"))]
    return out, errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--shot", help="스크린샷 경로 접두사")
    ap.add_argument("--timeout", type=int, default=600000)
    a = ap.parse_args()
    srv = serve()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=[
            "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
        for v in a.videos:
            page = b.new_page(viewport={"width": 1600, "height": 1000})
            shot = f"{a.shot}-{os.path.basename(v)}.png" if a.shot else None
            try:
                out, errs = run(page, base, os.path.abspath(v), shot, a.timeout)
            except Exception as e:
                out, errs = {"video": os.path.basename(v), "error": str(e)[:300]}, []
            print(out)
            for l in errs[:8]:
                print("   ", l[:300])
            sys.stdout.flush()
            page.close()
        b.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
