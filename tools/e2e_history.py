#!/usr/bin/env python3
"""분석 기록 기능 엔드투엔드 시험 (헤드리스 Chrome, 한 브라우저 컨텍스트 = 같은 IndexedDB)
1) 실제 영상 분석 → 자동 저장  2) ☆ 눌러 고정  3) 새 기록 6개 추가(최근 5개 유지 규칙)
4) 고정 기록이 남는지  5) 목록에서 다른 기록 열기  6) 새로고침 후 유지  7) 이름 바꾸기  8) 삭제
사용법: python3 tools/e2e_history.py VIDEO --shot /tmp/hist"""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e import serve, CHROME, wait_done
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--shot", default="/tmp/hist")
a = ap.parse_args()
srv = serve(); base = f"http://127.0.0.1:{srv.server_address[1]}"
ok = lambda c, m: print(("  ✓ " if c else "  ✗ ") + m, flush=True) or c
LIST = "() => window.__DF_hist().Hist.all().then(a => a.map(m => ({id:m.id, name:m.name, pinned:m.pinned, t:m.createdAt, score:m.score, thumb:!!m.thumb})))"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    ctx = b.new_context(viewport={"width": 1440, "height": 1000})
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(base + "/index.html")
    pg.wait_for_function("() => /준비|실패/.test(document.getElementById('engine').textContent)", timeout=120000)
    t0 = time.time(); pg.set_input_files("#file", os.path.abspath(a.video)); wait_done(pg, t0, 3000000)
    print("analysis", round(time.time() - t0), "s", flush=True)
    L = pg.evaluate(LIST)
    ok(len(L) == 1 and L[0]["thumb"], f"분석 후 자동 저장 (기록 {len(L)}개, 썸네일 {L[0]['thumb'] if L else None})")
    real = L[0]["id"]
    ok(pg.evaluate("() => window.__DF.sessionId") == real, "현재 기록으로 강조")
    pg.wait_for_selector(f'.hitem[data-id="{real}"]')
    pg.click(f'.hitem[data-id="{real}"] [data-act="pin"]'); pg.wait_for_timeout(500)
    ok(pg.evaluate(LIST)[0]["pinned"], "☆ 눌러 고정")
    # 새 기록 6개 (실제 기록 복제, 이후 시각) — 저장 경로와 같은 put + prune
    pg.evaluate("""async (rid) => { const { Hist, renderHistory } = window.__DF_hist(); const r = await Hist.get(rid);
        for (let k = 1; k <= 6; k++){ const id = "fake" + k;
          await Hist.put(Object.assign({}, r.meta, { id, name: "시험 " + k, pinned: false, createdAt: Date.now() + k*1000, score: 40 + k }),
                         Object.assign({}, r.data, { id }));
          await Hist.prune(); }
        await renderHistory(); }""", real)
    L = pg.evaluate(LIST); names = sorted(m["name"] for m in L if not m["pinned"])
    ok(any(m["id"] == real and m["pinned"] for m in L), "고정 기록은 새 기록 6개가 들어와도 남음")
    ok(len([m for m in L if not m["pinned"]]) == 5 and "시험 1" not in names, f"최근 분석은 5개만 (가장 오래된 '시험 1' 삭제): {names}")
    ok(pg.locator(".hitem").count() == 6, f"목록 표시 {pg.locator('.hitem').count()}개 (고정 1 + 최근 5)")
    pg.screenshot(path=a.shot + "-list.png", full_page=True)
    # 다른 기록 열기
    pg.click('.hitem[data-id="fake6"] .nm'); pg.wait_for_function("() => window.__DF.sessionId === 'fake6' && !window.__DF.busy", timeout=60000)
    ok(pg.inner_text("#mFile") == "시험 6" and pg.is_visible("#cardScore"), "목록에서 다른 기록 열기 → 이름·리포트 전환")
    ok(pg.locator('.hitem.cur[data-id="fake6"]').count() == 1, "연 기록이 강조됨")
    pg.click(f'.hitem[data-id="{real}"] .nm'); pg.wait_for_function(f"() => window.__DF.sessionId === '{real}' && !window.__DF.busy", timeout=60000)
    ok(True, "고정 기록으로 다시 전환")
    pg.evaluate("() => { window.__DF.view = 'overlay'; }"); pg.click("#vOverlay"); pg.wait_for_timeout(800)
    pg.screenshot(path=a.shot + "-opened.png", full_page=True)
    # 새로고침 후 유지
    pg.reload(); pg.wait_for_selector(".hitem", timeout=60000)
    ok(pg.locator(".hitem").count() == 6, "새로고침 후에도 기록 유지")
    # 이름 바꾸기
    pg.click('.hitem[data-id="fake5"] [data-act="ren"]'); pg.fill(".hitem input.rn", "김수영 1차"); pg.keyboard.press("Enter"); pg.wait_for_timeout(500)
    ok(any(m["name"] == "김수영 1차" for m in pg.evaluate(LIST)), "이름 바꾸기")
    # 삭제 (두 번 눌러 확인)
    pg.click('.hitem[data-id="fake2"] [data-act="del"]'); pg.wait_for_timeout(200)
    ok(len(pg.evaluate(LIST)) == 6, "삭제 첫 클릭은 확인 단계 (아직 안 지움)")
    pg.click('.hitem[data-id="fake2"] [data-act="del"]'); pg.wait_for_timeout(500)
    ok(len(pg.evaluate(LIST)) == 5, "두 번째 클릭에 삭제")
    pg.screenshot(path=a.shot + "-final.png", full_page=True)
    ok(not errs, f"페이지 오류 없음 {errs[:3]}")
    b.close()
srv.shutdown()
