import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_text(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=target.name + '.', dir=str(target.parent))
    os.close(tmp_fd)
    tmp = Path(tmp_path)
    with tmp.open('w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    # optional backup
    if target.exists():
        bak = target.with_suffix(target.suffix + '.bak')
        try:
            if bak.exists():
                bak.unlink()
            target.replace(bak)
        except Exception:
            # best-effort backup
            pass
    tmp.replace(target)


def load_json(path: Path):
    if path.exists():
        try:
            with path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def ensure_summary_updated(summary_path: Path, line_rate: float, lines_covered: int, lines_valid: int, note: str):
    existing = load_json(summary_path)
    payload = None
    if isinstance(existing, dict):
        # update in-place style
        notes = existing.get('notes')
        if isinstance(notes, list):
            notes.append(note)
        else:
            existing['notes'] = [note]
        existing['line_rate'] = line_rate
        existing['lines_covered'] = lines_covered
        existing['lines_valid'] = lines_valid
        payload = existing
    elif isinstance(existing, list):
        existing.append({
            'line_rate': line_rate,
            'lines_covered': lines_covered,
            'lines_valid': lines_valid,
            'note': note,
            'ts': datetime.now(timezone.utc).isoformat(),
        })
        payload = existing
    else:
        payload = {
            'line_rate': line_rate,
            'lines_covered': lines_covered,
            'lines_valid': lines_valid,
            'notes': [note],
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }

    atomic_write_text(summary_path, json.dumps(payload, ensure_ascii=False, indent=2))


def append_ci_evidence(ci_path: Path, event: str, metrics: dict, sha_map: dict):
    ci_path.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        'event': event,
        'ts': datetime.now(timezone.utc).isoformat(),
        'metrics': metrics,
        'sha256': sha_map,
    }
    line = json.dumps(rec, ensure_ascii=False)
    # append with LF
    with ci_path.open('a', encoding='utf-8', newline='\n') as f:
        f.write(line + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--note', required=True)
    ap.add_argument('--pytest-output', required=True)
    ap.add_argument('--coverage-xml', default='coverage.xml')
    ap.add_argument('--summary-json', default='reports/test/coverage_summary.json')
    ap.add_argument('--ci-evidence', default='reports/test/ci_evidence.jsonl')
    args = ap.parse_args()

    cov_path = Path(args.coverage_xml)
    if not cov_path.exists():
        print(f"ERROR: coverage xml not found: {cov_path}", file=sys.stderr)
        return 2
    try:
        tree = ET.parse(str(cov_path))
        root = tree.getroot()
        line_rate = float(root.attrib.get('line-rate', '0'))
        lines_covered = int(root.attrib.get('lines-covered', '0'))
        lines_valid = int(root.attrib.get('lines-valid', '0'))
    except Exception as e:
        print(f"ERROR: parsing coverage xml failed: {e}", file=sys.stderr)
        return 2

    summary_path = Path(args.summary_json)
    ensure_summary_updated(summary_path, line_rate, lines_covered, lines_valid, args.note)

    pytest_out = Path(args.pytest_output)
    sha_map = {
        'coverage_xml': sha256_file(cov_path),
        'pytest_output': sha256_file(pytest_out) if pytest_out.exists() else None,
        'coverage_summary': sha256_file(summary_path),
    }
    metrics = {
        'line_rate': line_rate,
        'lines_covered': lines_covered,
        'lines_valid': lines_valid,
        'note': args.note,
    }
    ci_path = Path(args.ci_evidence)
    append_ci_evidence(ci_path, event='pytest_storage_process_details_executed', metrics=metrics, sha_map=sha_map)

    print(json.dumps({'ok': True, 'metrics': metrics}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
