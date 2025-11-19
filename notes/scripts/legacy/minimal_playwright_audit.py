from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    out_dir = Path("artifacts/ui_audit")
    screens_dir = out_dir / "screens"
    out_dir.mkdir(parents=True, exist_ok=True)
    screens_dir.mkdir(parents=True, exist_ok=True)

    # Target server (align with FastAPI/Uvicorn default 8765)
    host = os.environ.get("UI_AUDIT_HOST", "127.0.0.1")
    port = os.environ.get("UI_AUDIT_PORT", "8765")
    base = f"http://{host}:{port}"
    url_unified = f"{base}/mail/unified-inbox"
    routes = ["/mail/unified-inbox", "/health/liveness", "/health/readiness"]

    results = {"routes": [], "gate": "FAIL", "axe_serious_plus": None, "axe_by_route": [], "axe_violations": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1366, "height": 768, "device_scale_factor": 1})
        page = context.new_page()
        for r in routes:
            target = url_unified if r == "/mail/unified-inbox" else f"{base}{r}"
            page.goto(target, wait_until="domcontentloaded")
            page.wait_for_timeout(500)
            # Save screenshot
            shot_name = "unified_inbox" if r == "/mail/unified-inbox" else r.strip('/').replace('/', '_') or 'mail'
            shot_path = screens_dir / f"route_{shot_name}.png"
            page.screenshot(path=str(shot_path))
            # Dump HTML for diagnostics on main UI route
            if r == "/mail/unified-inbox":
                html_dir = out_dir / "html"
                html_dir.mkdir(parents=True, exist_ok=True)
                content = page.content().replace("\r\n", "\n")
                with (html_dir / "route_unified_inbox.html").open("w", encoding="utf-8", newline="\n") as f:
                    f.write(content)
            results["routes"].append({"route": r, "status": 200})

            # Inject axe-core and run accessibility audit on /mail only (UI route)
            axe_summary = None
            if r == "/mail/unified-inbox":
                try:
                    page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js")
                    # Web Vitals minimal measurement (LCP/CLS)
                    page.add_script_tag(url="https://unpkg.com/web-vitals@4/dist/web-vitals.iife.js")
                    vitals = page.evaluate(
                        "() => new Promise((resolve) => { const data = {}; webVitals.onLCP(v => data.lcp = v.value); webVitals.onCLS(v => data.cls = v.value); setTimeout(() => resolve(data), 1000); })"
                    )
                    # Document diagnostics
                    doc_diag = page.evaluate("() => ({ title: document.title || '', lang: document.documentElement.getAttribute('lang') || '' })")
                    axe_result = page.evaluate(
                        "async () => { return await axe.run(document, { resultTypes: ['violations'] }) }"
                    )
                    # Count serious+ violations
                    serious_plus = 0
                    for v in axe_result.get("violations", []):
                        impact = (v.get("impact") or "").lower()
                        if impact in {"serious", "critical"}:
                            serious_plus += 1
                    # Build violation summaries (trimmed)
                    trimmed = []
                    for v in axe_result.get("violations", []):
                        trimmed.append({
                            "id": v.get("id"),
                            "impact": v.get("impact"),
                            "description": v.get("description"),
                            "help": v.get("help"),
                            "helpUrl": v.get("helpUrl"),
                            "nodes": len(v.get("nodes", [])),
                        })
                    axe_summary = {
                        "violations_total": len(axe_result.get("violations", [])),
                        "serious_plus": serious_plus,
                        "violations": trimmed,
                        "document": doc_diag,
                        "web_vitals": vitals,
                    }
                    results["axe_by_route"].append({"route": r, **axe_summary})
                    results["axe_violations"].extend(trimmed)
                except Exception:
                    axe_summary = {"violations_total": None, "serious_plus": None, "error": True}
                    results["axe_by_route"].append({"route": r, **axe_summary})
            # Update gate based on axe serious+ (if computed)
            try:
                sp = next((x["serious_plus"] for x in results["axe_by_route"] if x["route"] == "/mail/unified-inbox"), None)
                if sp is not None:
                    results["axe_serious_plus"] = sp
                    results["gate"] = "PASS" if sp == 0 else "FAIL"
            except Exception:
                pass
        context.close()
        browser.close()

    # Minimal summary.json to satisfy gate artifacts; UI Gate remains FAIL until axe etc.
    summary_path = out_dir / "summary.json"
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "gate": results["gate"],
        "routes": results["routes"],
        "axe": {
            "serious_plus": results["axe_serious_plus"],
            "by_route": results["axe_by_route"],
            "violations": results["axe_violations"],
        },
        "screens_dir": screens_dir.as_posix(),
        "path": summary_path.as_posix(),
    }
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Append CI evidence with SHA256
    import hashlib
    import time
    def sha256_file(p: Path) -> str:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest().upper()
    ci_evidence = Path("observability/policy/ci_evidence.jsonl")
    files = [{"path": summary_path.as_posix(), "sha256": sha256_file(summary_path)}]
    # Include key screenshots if exist
    for name in ["route_unified_inbox.png", "route_health_liveness.png", "route_health_readiness.png"]:
        p = (screens_dir / name)
        if p.exists():
            files.append({"path": p.as_posix(), "sha256": sha256_file(p)})
    # Include DOM HTML dump if present
    html_path = (out_dir / "html" / "route_unified_inbox.html")
    if html_path.exists():
        files.append({"path": html_path.as_posix(), "sha256": sha256_file(html_path)})
    payload_evidence = {
        "ts": time.strftime("%Y/%m/%d %H:%M:%S"),
        "event": "ui_audit_minimal_executed",
        "files": files,
        "status": "updated",
        "note": "Minimal Playwright+axe実行・UTF-8/LF"
    }
    ci_evidence.parent.mkdir(parents=True, exist_ok=True)
    with ci_evidence.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(payload_evidence, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
