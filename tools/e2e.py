#!/usr/bin/env python3
"""DiveForm 엔드투엔드 검증: 헤드리스 Chrome에서 index.html에 실제 영상을 올려
엔진 로드 → 관절 추적 → 리포트까지 돌리고 결과를 출력한다.

사용법:
  python3 tools/e2e.py VIDEO [VIDEO ...] [--shot out]       # 전체 분석 (+스크린샷·결과 JSON)
  python3 tools/e2e.py --replay out-VIDEO.json [...]         # 저장된 추적 결과로 분석만 다시 (수 초)
  python3 tools/e2e.py VIDEO --shot out --pick-at 1.0 --pick-xy 0.22,0.49
        # 분석 후 '다이버 지정' → 1.0초 장면에서 영상 좌표(0~1) 위치를 실제로 클릭해 재추적
"""
import argparse, functools, http.server, json, os, socketserver, sys, threading, time
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
DONE_JS = """() => (!document.getElementById('cardScore').classList.contains('hide') && !window.__DF.busy)
               || /실패/.test(document.getElementById('steps').textContent)"""


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    h.log_message = lambda *a, **k: None
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def wait_done(page, t0, timeout):
    while not page.evaluate(DONE_JS) and time.time() - t0 < timeout / 1000:
        print(f"   … {time.time()-t0:5.0f}s  progress={page.evaluate('document.getElementById(\"prog\").style.width')}", flush=True)
        time.sleep(30)


def summary(page, video, took):
    return {
        "video": os.path.basename(video), "engine": page.inner_text("#engine"), "sec": round(took, 1),
        "track": page.inner_text("#mTrack"), "scale": page.inner_text("#mScale"),
        "score": page.inner_text("#score") if page.is_visible("#score") else "—",
        "took": page.inner_text("#infoNote") if page.query_selector("#infoNote") else "",
        "quality": page.inner_text("#quality") if page.query_selector("#quality") else "",
        "steps": page.inner_text("#steps").replace("\n", " | ")[-300:],
        "history": page.evaluate("() => window.__DF_hist ? window.__DF_hist().Hist.all().then(a => a.map(m => m.name + ':' + m.score)) : null"),
        "session": page.evaluate("() => window.__DF.sessionId"),
    }


def dump(page, path):
    d = page.evaluate("""() => { const S = window.__DF; if (!S || !S.frames) return null;
        const m = S.res && S.res.metrics;
        return { track: S.track || null, w: S.src && S.src.w, h: S.src && S.src.h, dur: S.src && S.src.dur,
                 flip: !!(S.src && S.src.flip), pxPerM: S.cal && S.cal.pxPerM, scaleSrc: S.cal && S.cal.scaleSrc,
                 phases: S.res && S.res.phases, metrics: m, score: S.res && S.res.score, analysisSec: S.analysisSec,
                 frames: S.frames.map(f => ({ t: f.t, full: f.full || null, interp: !!f.interp, cam: f.cam || null })),
                 raw: S.framesRaw }; }""")
    if d:
        json.dump(d, open(path, "w"))
    return d


def run(page, base, video, shot, timeout, pick_at, pick_xy=None):
    logs = []
    page.on("console", lambda m: logs.append(f"[{m.type}] {m.text}"))
    page.on("pageerror", lambda e: logs.append(f"[pageerror] {e}"))
    page.goto(base + "/index.html")
    page.wait_for_function("() => /준비|실패/.test(document.getElementById('engine').textContent)", timeout=120000)
    t0 = time.time()
    page.set_input_files("#file", video)
    wait_done(page, t0, timeout)
    out = summary(page, video, time.time() - t0)
    if shot:
        page.screenshot(path=shot + ".png", full_page=True)
        dump(page, shot + ".json")
    if pick_at is not None:
        # 해당 시각으로 이동 → 다이버 지정 → 가장 숙인 후보의 박스 중앙을 실제로 클릭
        page.evaluate(f"() => {{ window.__DF.t = {pick_at}; }}")
        page.click("#pickBtn")
        page.wait_for_function("() => !!window.__DF.pick", timeout=600000)
        info = page.evaluate("""() => { const P = window.__DF.pick; const im = P.img;
            const cv = document.getElementById('stage'), r = cv.getBoundingClientRect();
            const VW = cv.width, VH = cv.height, k = Math.min(VW/im.width, VH/im.height);
            const ox = (VW - im.width*k)/2, oy = (VH - im.height*k)/2;
            const XY = %s;
            let px, py;
            if (XY){ px = XY[0]*im.width; py = XY[1]*im.height; }
            else { let bi = -1, bt = -1; P.cands.forEach((c,i) => { if (c.tilt > bt){ bt = c.tilt; bi = i; } });
                   if (bi < 0) return { n: 0 }; px = P.cands[bi].c[0]; py = P.cands[bi].c[1]; }
            const x = (ox + px*k) / VW * r.width + r.left, y = (oy + py*k) / VH * r.height + r.top;
            return { n: P.cands.length, x, y, cands: P.cands.map(c => [Math.round(c.tilt), c.box.map(Math.round)]) }; }""" % (json.dumps(pick_xy) if pick_xy else "null"))
        print("   pick:", {k: v for k, v in info.items() if k not in ("x", "y")}, flush=True)
        if shot:
            page.screenshot(path=shot + "-pick.png")
        if info.get("n"):
            t1 = time.time()
            page.mouse.click(info["x"], info["y"])
            page.wait_for_function("() => window.__DF.busy", timeout=20000)
            while page.evaluate("() => window.__DF.busy") and time.time() - t1 < timeout/1000:
                print(f"   … retrack {time.time()-t1:5.0f}s", flush=True); time.sleep(30)
            out["after_pick"] = summary(page, video, time.time() - t1)
            if shot:
                page.screenshot(path=shot + "-picked.png", full_page=True)
                dump(page, shot + "-picked.json")
    errs = [l for l in logs if l.startswith(("[error]", "[pageerror]"))]
    return out, errs


def replay(page, base, path):
    page.goto(base + "/index.html")
    page.wait_for_function("() => !!window.__DF_api", timeout=60000)
    d = json.load(open(path))
    meta = {"w": d["w"], "h": d["h"], "dur": d["dur"], "track": d["track"], "kind": "video"}
    return page.evaluate("([raw, meta]) => window.__DF_api.analyzeOnly(raw, meta)", [d["raw"], meta])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--shot", help="결과 파일 접두사 (영상 이름이 붙음)")
    ap.add_argument("--timeout", type=int, default=3000000)
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--pick-at", type=float)
    ap.add_argument("--pick-xy", help="영상 정규 좌표 x,y (예: 0.22,0.49)")
    a = ap.parse_args()
    srv = serve()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=[
            "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
        for v in a.inputs:
            page = b.new_page(viewport={"width": 1600, "height": 1000})
            try:
                if a.replay:
                    r = replay(page, base, v)
                    m = r["metrics"]
                    print(os.path.basename(v), {k: (round(x, 2) if isinstance(x, float) else x) for k, x in
                                                {**{k: r[k] for k in ("flip", "pxPerM", "scaleSrc", "score")}, **m}.items()})
                else:
                    shot = f"{a.shot}-{os.path.basename(v)}" if a.shot else None
                    pxy = [float(q) for q in a.pick_xy.split(",")] if a.pick_xy else None
                    out, errs = run(page, base, os.path.abspath(v), shot, a.timeout, a.pick_at, pxy)
                    print(out)
                    for l in errs[:8]:
                        print("   ", l[:300])
            except Exception as e:
                print({"input": os.path.basename(v), "error": str(e)[:400]})
            sys.stdout.flush()
            page.close()
        b.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
