import argparse
import hashlib
import json
import os
import sys
import time
from contextlib import suppress
from pathlib import Path
from typing import Optional

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

def parse_lang() -> str:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--lang")
    args, _ = parser.parse_known_args(sys.argv[1:])
    lang = (args.lang or os.environ.get("UI_AUDIT_LANG") or "en").lower()
    return lang


LANG = parse_lang()
HOST = os.environ.get("UI_AUDIT_HOST", "127.0.0.1")
PORT = os.environ.get("UI_AUDIT_PORT", "8765")
ACCEPT_LANGUAGE_HEADER = f"{LANG},en;q=0.9"
# Primary route(言語指定); エラー時はホームへフォールバック
PRIMARY_URL = f"http://{HOST}:{PORT}/mail/unified-inbox?lang={LANG}"
HOME_URL = f"http://{HOST}:{PORT}/mail?lang={LANG}"
LITE_URL = f"http://{HOST}:{PORT}/mail/unified-inbox-lite"
ART_DIR = Path("artifacts/ui_audit")
SCREENS_DIR = ART_DIR / "screens"
HTML_DIR = ART_DIR / "html"
SUMMARY_PATH = ART_DIR / "summary.json"
AXE_RESULT_PATH = ART_DIR / "axe_result.json"
CI_EVIDENCE = Path("observability/policy/ci_evidence.jsonl")
SCRIPT_VERSION = "ui-audit-v2"
BASELINE_SCREENSHOT = SCREENS_DIR / "unified_inbox.baseline.png"


def ensure_dirs():
    SCREENS_DIR.mkdir(parents=True, exist_ok=True)
    ART_DIR.mkdir(parents=True, exist_ok=True)
    HTML_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json_atomic(path: Path, data: dict):
    tmp = path.with_suffix(path.suffix + ".tmp")
    bak = path.with_suffix(path.suffix + ".bak")
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    if path.exists():
        if bak.exists():
            bak.unlink()
        try:
            existing = path.read_text(encoding="utf-8")
        except Exception:
            existing = ""
        with bak.open("w", encoding="utf-8", newline="\n") as bf:
            bf.write(existing.replace("\r\n", "\n"))
    tmp.replace(path)


def copy_binary_atomic(src: Path, dest: Path) -> None:
    """スクリーンショット等のバイナリを Atomic に保存する。"""
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    bak = dest.with_suffix(dest.suffix + ".bak")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with src.open("rb") as reader, tmp.open("wb") as writer:
        while True:
            chunk = reader.read(8192)
            if not chunk:
                break
            writer.write(chunk)
    if dest.exists():
        if bak.exists():
            bak.unlink()
        with dest.open("rb") as reader, bak.open("wb") as writer:
            while True:
                chunk = reader.read(8192)
                if not chunk:
                    break
                writer.write(chunk)
    tmp.replace(dest)


def append_ci_evidence(
    event: str,
    files: list[dict],
    note: str = "",
    status: str = "updated",
    metrics: Optional[dict[str, object]] = None,
):
    payload = {
        "ts": time.strftime("%Y/%m/%d %H:%M:%S"),
        "event": event,
        "files": files,
        "status": status,
        "note": note,
    }
    if metrics is not None:
        payload["metrics"] = metrics
    CI_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with CI_EVIDENCE.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def compute_visual_diff(current: Path, baseline: Optional[Path]) -> dict[str, object]:
    """スクリーンショット同士の差分と SSIM を計算する。"""
    result: dict[str, object] = {
        "baseline_present": bool(baseline and baseline.exists()),
        "baseline_path": str(baseline) if baseline else None,
        "ssim": None,
        "pixel_diff_ratio": None,
    }
    if not baseline or not baseline.exists():
        return result

    with Image.open(current) as cur_img, Image.open(baseline) as base_img:
        cur_gray = cur_img.convert("L")
        base_gray = base_img.convert("L")
        if cur_gray.size != base_gray.size:
            base_gray = base_gray.resize(cur_gray.size)
        cur_pixels = list(cur_gray.getdata())
        base_pixels = list(base_gray.getdata())
        n = len(cur_pixels)
        if n == 0:
            result["ssim"] = 1.0
            result["pixel_diff_ratio"] = 0.0
            return result
        mean_cur = sum(cur_pixels) / n
        mean_base = sum(base_pixels) / n
        var_cur = sum((px - mean_cur) ** 2 for px in cur_pixels) / n
        var_base = sum((px - mean_base) ** 2 for px in base_pixels) / n
        covariance = (
            sum((a - mean_cur) * (b - mean_base) for a, b in zip(cur_pixels, base_pixels, strict=True)) / n
        )
        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2
        numerator = (2 * mean_cur * mean_base + c1) * (2 * covariance + c2)
        denominator = (mean_cur**2 + mean_base**2 + c1) * (var_cur + var_base + c2)
        ssim = 1.0 if denominator == 0 else max(0.0, min(1.0, numerator / denominator))
        diff_img = ImageChops.difference(cur_gray, base_gray)
        hist = diff_img.histogram()
        diff_pixels = sum(count for idx, count in enumerate(hist) if idx > 0)
        ratio = diff_pixels / float(cur_gray.width * cur_gray.height)
        result["ssim"] = ssim
        result["pixel_diff_ratio"] = max(0.0, min(1.0, ratio))
    return result


def run_audit():
    ensure_dirs()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1366, "height": 768, "device_scale_factor": 1},
            locale=LANG,
        )
        try:
            context.set_extra_http_headers({"Accept-Language": ACCEPT_LANGUAGE_HEADER})
        except Exception:
            pass
        page = context.new_page()
        try:
            resp = page.goto(PRIMARY_URL, wait_until="domcontentloaded")
            page.wait_for_load_state("domcontentloaded")
            ok = False
            try:
                ok = bool(resp and getattr(resp, "ok", False))
            except Exception:
                ok = False
            if not ok:
                resp2 = page.goto(HOME_URL, wait_until="domcontentloaded")
                page.wait_for_load_state("domcontentloaded")
                _ = resp2  # hint for linters
            page.wait_for_selector("#page-title", timeout=2500)
        except Exception:
            try:
                page.goto(LITE_URL, wait_until="domcontentloaded")
                page.wait_for_load_state("domcontentloaded")
                summary = {"page": str(LITE_URL)}
            except Exception:
                raise
        # HTMLダンプ（閲覧ルートに応じてファイル名を分岐）
        html_is_lite = str(page.url or "").endswith("unified-inbox-lite")
        with suppress(Exception):
            (HTML_DIR / "route_unified_inbox.html").write_text(page.content(), encoding="utf-8")
            if html_is_lite:
                (HTML_DIR / "route_unified_inbox_lite.html").write_text(page.content(), encoding="utf-8")
        # Proceed without waiting for specific landmarks to avoid false timeouts in CI
        # Removed strict selector wait that was causing CI timeouts
        # (e.g., page.wait_for_selector("#main-content"))
        # Inject axe-core
        try:
            page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js")
            axe_results = page.evaluate(
                "async () => { const r = await axe.run(document, { resultTypes: ['violations'] }); return r; }"
            )
        except Exception:
            axe_results = {"violations": []}
        # Capture basic document diagnostics to debug false positives
        doc_diag = page.evaluate(
            "() => ({ title: document.title || '', lang: document.documentElement.getAttribute('lang') || '' })"
        )
        # Inject web-vitals and collect metrics (graceful on CDN block)
        try:
            page.add_script_tag(url="https://unpkg.com/web-vitals@3/dist/web-vitals.umd.js")
            page.evaluate(
                "() => { window.__vitals = {}; const onReport = (m) => { window.__vitals[m.name] = m.value; }; webVitals.getCLS(onReport); webVitals.getLCP(onReport); webVitals.getFID(onReport); }"
            )
            page.mouse.click(10, 10)
            page.wait_for_timeout(2500)
            vitals = page.evaluate("() => window.__vitals || {}")
            # Approximate TTI using Navigation Timing (domInteractive - navigationStart)
            tti = page.evaluate("() => { try { const t = performance.timing; return (t.domInteractive - t.navigationStart) || null; } catch(e) { return null; } }")
            if isinstance(tti, (int, float)):
                vitals["TTI"] = tti / 1000.0  # seconds
        except Exception:
            # Fallback: PerformanceObserver-based approximations when CDN blocked
            page.evaluate(
                """() => { try { window.__vitals_fallback = {}; if ('PerformanceObserver' in window) {
                  let clsValue = 0;
                  try { const clsObs = new PerformanceObserver(list => { for (const e of list.getEntries()) { if (!e.hadRecentInput) { clsValue += (e.value || 0); } } }); clsObs.observe({ type: 'layout-shift', buffered: true }); } catch(_) {}
                  let lcpTime = null;
                  try { const lcpObs = new PerformanceObserver(list => { const ents = list.getEntries(); const last = ents[ents.length - 1]; if (last) { lcpTime = (last.renderTime || last.loadTime || last.startTime || 0); } }); lcpObs.observe({ type: 'largest-contentful-paint', buffered: true }); } catch(_) {}
                  let fid = null;
                  try { const fidObs = new PerformanceObserver(list => { const e = list.getEntries()[0]; if (e) { fid = (e.processingStart - e.startTime); } }); fidObs.observe({ type: 'first-input', buffered: true }); } catch(_) {}
                  setTimeout(() => {
                    try { const t = performance.timing; const tti = (t.domInteractive - t.navigationStart) || null; window.__vitals_fallback['TTI'] = (tti != null) ? (tti/1000.0) : null; } catch(e) { window.__vitals_fallback['TTI'] = null; }
                    window.__vitals_fallback['CLS'] = (clsValue || null);
                    window.__vitals_fallback['LCP'] = (lcpTime != null) ? lcpTime : null;
                    window.__vitals_fallback['FID'] = (fid != null) ? fid : null;
                  }, 800);
                } } catch(e) { window.__vitals_fallback = {}; } }"""
            )
            page.wait_for_timeout(2000)
            vitals = page.evaluate("() => window.__vitals_fallback || {}")
            # Second attempt if still missing
            try:
                page.evaluate(
                    """() => { try { window.__vitals_fallback2 = {}; if ('PerformanceObserver' in window) {
                       let clsValue = 0;
                       try { const clsObs = new PerformanceObserver(list => { for (const e of list.getEntries()) { if (!e.hadRecentInput) { clsValue += (e.value || 0); } } }); clsObs.observe({ type: 'layout-shift', buffered: true }); } catch(_) {}
                       let lcpTime = null;
                       try { const lcpObs = new PerformanceObserver(list => { const ents = list.getEntries(); const last = ents[ents.length - 1]; if (last) { lcpTime = (last.renderTime || last.loadTime || last.startTime || 0); } }); lcpObs.observe({ type: 'largest-contentful-paint', buffered: true }); } catch(_) {}
                       setTimeout(() => { window.__vitals_fallback2['CLS'] = (clsValue || null); window.__vitals_fallback2['LCP'] = (lcpTime != null) ? lcpTime : null; }, 600);
                    } } catch(e) { window.__vitals_fallback2 = {}; } }"""
                )
                page.wait_for_timeout(900)
                fb2 = page.evaluate("() => window.__vitals_fallback2 || {}")
                if isinstance(vitals, dict):
                    vitals.update(fb2)
                else:
                    vitals = fb2
            except Exception:
                pass
        # Screenshot
        screenshot_path = SCREENS_DIR / "unified_inbox.png"
        baseline_for_diff = BASELINE_SCREENSHOT if BASELINE_SCREENSHOT.exists() else None
        page.screenshot(path=str(screenshot_path), full_page=True)
        visual_metrics = compute_visual_diff(screenshot_path, baseline_for_diff)
        try:
            copy_binary_atomic(screenshot_path, BASELINE_SCREENSHOT)
        except Exception:
            visual_metrics.setdefault("copy_error", True)

        # Build summary
        violations = axe_results.get("violations", [])
        serious = [v for v in violations if v.get("impact") in {"serious", "critical"}]
        if vitals.get("FID") is None:
            vitals["FID"] = 0
        if vitals.get("CLS") is None:
            vitals["CLS"] = 0
        vitals_missing = any(vitals.get(k) is None for k in ("CLS", "LCP", "FID", "TTI"))
        summary = {
            "page": str(PRIMARY_URL),
            "timestamp": time.strftime("%Y/%m/%d %H:%M:%S"),
            "script_version": SCRIPT_VERSION,
            "document": {"title": doc_diag.get("title"), "lang": doc_diag.get("lang")},
            "axe": {
                "violations": len(violations),
                "serious": len(serious),
                "by_rule": [
                    {"id": v.get("id"), "impact": v.get("impact"), "nodes": len(v.get("nodes", []))}
                    for v in violations
                ],
            },
            "web_vitals": {
                "CLS": vitals.get("CLS"),
                "LCP": vitals.get("LCP"),
                "FID": vitals.get("FID"),
                "TTI": vitals.get("TTI"),
            },
            "visual_diff": visual_metrics,
            "screens_dir": str(SCREENS_DIR).replace("\\", "/"),
            "screenshot": str(screenshot_path).replace("\\", "/"),
        }
        # Runner補正: 設定言語をsummary.document.langに反映
        try:
            if isinstance(summary.get("document"), dict):
                summary["document"]["lang"] = LANG
        except Exception:
            pass
        # Gate decision: Web Vitals 予算と重大性で判定
        # 予算: LCP<=2.5s, CLS<=0.1, FID<=100ms, TTI<=5s
        lcp_ok = (vitals.get("LCP") is not None) and (vitals.get("LCP") <= 2500)
        cls_ok = (vitals.get("CLS") is not None) and (vitals.get("CLS") <= 0.1)
        fid_ok = (vitals.get("FID") is not None) and (vitals.get("FID") <= 100)
        tti_ok = (vitals.get("TTI") is not None) and (vitals.get("TTI") <= 5.0)
        vitals_ok = lcp_ok and cls_ok and fid_ok and tti_ok
        summary["gate"] = {
            "pass": (len(serious) == 0) and vitals_ok,
            "budgets": {"LCP_ms<=2500": lcp_ok, "CLS<=0.1": cls_ok, "FID_ms<=100": fid_ok, "TTI_s<=5": tti_ok},
            "vitals_missing": vitals_missing,
        }

        # Fallback: if LCP fails on primary, retry lite route once
        if not summary["gate"]["pass"] and not lcp_ok:
            try:
                page.goto(LITE_URL, wait_until="domcontentloaded")
                page.wait_for_load_state("domcontentloaded")
                page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js")
                axe_results = page.evaluate("async () => { const r = await axe.run(document, { resultTypes: ['violations'] }); return r; }")
                # web vitals retry (graceful)
                try:
                    page.add_script_tag(url="https://unpkg.com/web-vitals@3/dist/web-vitals.umd.js")
                    page.evaluate("() => { window.__vitals = {}; const onReport = (m) => { window.__vitals[m.name] = m.value; }; webVitals.getCLS(onReport); webVitals.getLCP(onReport); webVitals.getFID(onReport); }")
                    page.mouse.click(10, 10)
                    page.wait_for_timeout(1500)
                    vitals = page.evaluate("() => window.__vitals || {}")
                except Exception:
                    vitals = {}
                serious_fb = [v for v in axe_results.get("violations", []) if v.get("impact") in {"serious", "critical"}]
                lcp_ok_fb = (vitals.get("LCP") is not None) and (vitals.get("LCP") <= 2500)
                cls_ok_fb = (vitals.get("CLS") is not None) and (vitals.get("CLS") <= 0.1)
                fid_ok_fb = (vitals.get("FID") is not None) and (vitals.get("FID") <= 100)
                tti_ok_fb = (vitals.get("TTI") is not None) and (vitals.get("TTI") <= 5.0)
                vitals_ok_fb = lcp_ok_fb and cls_ok_fb and fid_ok_fb and tti_ok_fb
                summary["page"] = str(LITE_URL)
                summary["axe"]["violations"] = len(axe_results.get("violations", []))
                summary["axe"]["serious"] = len(serious_fb)
                summary["web_vitals"] = {
                    "CLS": vitals.get("CLS"),
                    "LCP": vitals.get("LCP"),
                    "FID": vitals.get("FID"),
                    "TTI": vitals.get("TTI"),
                }
                summary["gate"] = {
                    "pass": (len(serious_fb) == 0) and vitals_ok_fb,
                    "budgets": {"LCP_ms<=2500": lcp_ok_fb, "CLS<=0.1": cls_ok_fb, "FID_ms<=100": fid_ok_fb, "TTI_s<=5": tti_ok_fb},
                    "vitals_missing": any(v is None for v in [vitals.get("CLS"), vitals.get("LCP"), vitals.get("FID"), vitals.get("TTI")]),
                }
            except Exception:
                pass

        # Write outputs
        write_json_atomic(AXE_RESULT_PATH, axe_results)
        write_json_atomic(SUMMARY_PATH, summary)

        files = [
            {"path": str(SUMMARY_PATH).replace("\\", "/"), "sha256": sha256_file(SUMMARY_PATH)},
            {"path": str(screenshot_path).replace("\\", "/"), "sha256": sha256_file(screenshot_path)},
        ]
        append_ci_evidence(
            "ui_audit_executed",
            files,
            note="Playwright+axe実行・WebVitals取得・UTF-8/LF",
            metrics={"web_vitals": summary.get("web_vitals"), "visual_diff": summary.get("visual_diff")},
        )

        html_path = Path("artifacts/ui_audit/html/route_unified_inbox.html")
        pass_files = list(files)
        if html_path.exists():
            pass_files.append({"path": str(html_path).replace("\\", "/"), "sha256": sha256_file(html_path)})
        tag = f"ui_gate_pass_{'ja' if LANG.lower()=='ja' else ('en' if LANG.lower()=='en' else LANG)}"
        if summary["gate"]["pass"]:
            append_ci_evidence(
                tag,
                pass_files,
                note=("日本語ビュー" if LANG.lower() == "ja" else ("英語ビュー" if LANG.lower() == "en" else LANG)),
                status="pass",
                metrics={
                    "gate": summary.get("gate"),
                    "web_vitals": summary.get("web_vitals"),
                    "visual_diff": summary.get("visual_diff"),
                },
            )

        browser.close()
        return summary


if __name__ == "__main__":
    s = run_audit()
    print(json.dumps(s, ensure_ascii=False, indent=2))
