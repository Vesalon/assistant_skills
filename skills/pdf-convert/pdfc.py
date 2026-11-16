#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf>=4", "keyring>=24"]
# ///
"""Convert PDFs (and Word, PowerPoint, images) to markdown, HTML, JSON or LaTeX
through the Datalab convert API (marker), with spend guards.

    pdfc.py setup                         store a Datalab key (asks for it, hidden)
    pdfc.py doctor                        check key, tools, budget, cache
    pdfc.py convert paper.pdf             standard preset -> ./paper/paper.md + figures
    pdfc.py convert paper.pdf --preset text -o notes/      cheapest, text only
    pdfc.py convert paper.pdf --preset full --format md,latex
    pdfc.py convert paper.pdf --pages 0-3 --dry-run         plan and cost, no call
    pdfc.py fetch REQUEST_ID              collect a conversion that outlived the wait
    pdfc.py usage                         spend over the last 30 days
    pdfc.py config [KEY VALUE]            show or set budget_usd_30d, max_pages

Guards: a page limit per call, a rolling 30-day budget kept in a local ledger,
a cache by file hash (repeat conversions are free), and uploads that are never
retried after the server may have accepted them. The hard limit is the spend
cap set on the key itself in the Datalab dashboard.

API key: $DATALAB_API_KEY, else the store chosen at setup (OS keyring or a
mode-600 file in the config directory). Standard library only; pypdf (page
counts) and keyring (OS credential store) are optional and `uv run` adds both.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import gzip
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

API = "https://www.datalab.to/api/v1"
NAME = "pdf-convert"
ENV_KEY = "DATALAB_API_KEY"
KEYRING_SERVICE, KEYRING_USER = "pdf-convert", "datalab"
USER_AGENT = "pdf-convert-skill/1.0"
KEYS_URL = "https://www.datalab.to/app/keys"

EXIT_ERROR, EXIT_PENDING, EXIT_REFUSED = 1, 3, 4  # argparse uses 2


def _dirs() -> tuple[Path, Path, Path]:
    """Config, state and cache directories: XDG on Linux/macOS, AppData on Windows."""
    home = Path.home()
    if os.name == "nt":
        roaming = Path(os.environ.get("APPDATA") or home / "AppData" / "Roaming")
        local = Path(os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local")
        return roaming / NAME, local / NAME / "state", local / NAME / "cache"
    env = os.environ.get
    return (Path(env("XDG_CONFIG_HOME") or home / ".config") / NAME,
            Path(env("XDG_STATE_HOME") or home / ".local" / "state") / NAME,
            Path(env("XDG_CACHE_HOME") or home / ".cache") / NAME)


CONFIG_DIR, STATE_DIR, CACHE_DIR = _dirs()
CONFIG_FILE = CONFIG_DIR / "config.json"
KEY_FILE = CONFIG_DIR / "api_key"
LEDGER = STATE_DIR / "ledger.jsonl"

DEFAULTS: dict[str, Any] = {
    "budget_usd_30d": 5.0,
    "max_pages": 60,
    "key_store": None,  # "keyring" or "file", chosen by `setup`
    # USD per 1,000 pages at Datalab list prices, i.e. without the optional 25%
    # data-sharing discount (checked 2026-11-16). Used only for estimates; the
    # ledger records the cost the API reports.
    "price_per_1k_pages": {"lite": 0.50, "fast": 1.33, "balanced": 4.00, "accurate": 10.00},
    "extra_per_1k_pages": {"chart_understanding": 3.00, "infographic": 4.00,
                           "word_bboxes": 2.00, "track_changes": 6.00},
    "merge_cross_page_per_doc": 0.10,  # variable compute charge, "a few cents" per document
}
SETTABLE = {"budget_usd_30d": float, "max_pages": int}

PRESETS: dict[str, dict[str, Any]] = {
    # Born-digital text layer only, no images: skimming, searching, quoting.
    "text": {"mode": "lite", "images": False, "extras": [], "merge": False,
             "flags": {"token_efficient_markdown": "true"}},
    # Layout-aware reading with figures and tables.
    "standard": {"mode": "balanced", "images": True, "extras": [], "merge": False, "flags": {}},
    # Highest accuracy, chart reading, tables/paragraphs merged across pages.
    "full": {"mode": "accurate", "images": True, "extras": ["chart_understanding"],
             "merge": True, "flags": {}},
}
MODES = ("lite", "fast", "balanced", "accurate")
FORMATS = {"md": "markdown", "markdown": "markdown", "html": "html", "json": "json",
           "chunks": "chunks", "latex": "markdown", "tex": "markdown"}

PAGE_SEP = re.compile(r"^\{(\d+)\}-{6,}\s*$", re.M)


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #

def die(msg: str, code: int = EXIT_ERROR) -> None:
    sys.stdout.flush()
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def refuse(msg: str) -> None:
    sys.stdout.flush()
    print(f"refused: {msg}", file=sys.stderr)
    raise SystemExit(EXIT_REFUSED)


def now() -> datetime:
    return datetime.now(timezone.utc)


def load_config() -> dict[str, Any]:
    cfg = json.loads(json.dumps(DEFAULTS))
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text())
        except (OSError, json.JSONDecodeError) as e:
            die(f"cannot read {CONFIG_FILE}: {e}")
        for k, v in saved.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


def save_config(updates: dict[str, Any]) -> None:
    saved = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    saved.update(updates)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(saved, indent=2) + "\n")


def safe_name(s: str) -> str:
    s = re.sub(r"[^\w.-]+", "_", s, flags=re.ASCII).strip("._")
    return s or "document"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def money(x: float | None) -> str:
    return "?" if x is None else f"${x:.4f}" if x < 1 else f"${x:.2f}"


# --------------------------------------------------------------------------- #
# API key storage
# --------------------------------------------------------------------------- #

def _keyring():
    try:
        import keyring  # type: ignore
        return keyring
    except ImportError:
        return None


def keyring_usable() -> tuple[bool, str]:
    kr = _keyring()
    if kr is None:
        return False, "keyring package not installed (run through `uv run` to get it)"
    try:
        backend = kr.get_keyring()
    except Exception as e:  # noqa: BLE001 - any backend failure means unusable
        return False, f"keyring error: {e}"
    name = type(backend).__module__ + "." + type(backend).__name__
    if "fail" in name.lower() or "null" in name.lower() or getattr(backend, "priority", 1) <= 0:
        return False, f"no OS keyring backend available ({name})"
    return True, name


def load_key(cfg: dict[str, Any]) -> tuple[str | None, str]:
    """Return (key, where it came from). Never print the key itself."""
    v = os.environ.get(ENV_KEY, "").strip()
    if v:
        return v, f"${ENV_KEY}"
    if cfg.get("key_store") == "keyring":
        kr = _keyring()
        if kr is None:
            die("the key is stored in the OS keyring, but the keyring package is missing. "
                "Run this script with `uv run`, or set $DATALAB_API_KEY.")
        try:
            v = (kr.get_password(KEYRING_SERVICE, KEYRING_USER) or "").strip()
        except Exception as e:  # noqa: BLE001
            die(f"could not read the key from the OS keyring: {e}")
        return (v or None), "OS keyring"
    if KEY_FILE.exists():
        v = KEY_FILE.read_text().strip()
        return (v or None), str(KEY_FILE)
    return None, ""


def store_key(key: str, store: str) -> str:
    if store == "keyring":
        kr = _keyring()
        kr.set_password(KEYRING_SERVICE, KEYRING_USER, key)
        if kr.get_password(KEYRING_SERVICE, KEYRING_USER) != key:
            raise RuntimeError("keyring did not return the stored key")
        return "OS keyring"
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = KEY_FILE.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(key)
    os.replace(tmp, KEY_FILE)
    if os.name != "nt":
        os.chmod(KEY_FILE, 0o600)
    return str(KEY_FILE)


def remove_key() -> list[str]:
    removed = []
    kr = _keyring()
    if kr is not None:
        try:
            if kr.get_password(KEYRING_SERVICE, KEYRING_USER) is not None:
                kr.delete_password(KEYRING_SERVICE, KEYRING_USER)
                removed.append("OS keyring")
        except Exception:  # noqa: BLE001
            pass
    if KEY_FILE.exists():
        KEY_FILE.unlink()
        removed.append(str(KEY_FILE))
    return removed


def require_key(cfg: dict[str, Any]) -> str:
    key, _ = load_key(cfg)
    if not key:
        die(f"no Datalab API key. The user should run `{_self_cmd()} setup` in their own "
            f"terminal (it asks for the key without echoing it), or set ${ENV_KEY}.")
    return key


def _self_cmd() -> str:
    return f"uv run {Path(__file__).resolve()}"


# --------------------------------------------------------------------------- #
# HTTP (standard library)
# --------------------------------------------------------------------------- #

class ApiError(Exception):
    pass


def _http(method: str, url: str, key: str | None = None, body: bytes | None = None,
          headers: dict[str, str] | None = None, timeout: float = 60) -> tuple[int, bytes]:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if key:
        h["X-API-Key"] = key
    h.update(headers or {})
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _error_text(status: int, raw: bytes) -> str:
    try:
        data = json.loads(raw)
        detail = data.get("detail") or data.get("error") or data
        if not isinstance(detail, str):
            detail = json.dumps(detail)[:400]
    except (json.JSONDecodeError, AttributeError):
        detail = raw[:300].decode("utf-8", "replace")
    hints = {
        401: "the key was rejected; run setup again with a valid key",
        402: "the key reached its 30-day spend cap in Datalab. Stop and tell the user; "
             "only they can raise the cap in the Datalab billing settings",
        403: "permission or subscription problem with this key",
        413: "file is over the API size limit (200 MB)",
    }
    hint = hints.get(status)
    return f"HTTP {status}: {detail}" + (f" ({hint})" if hint else "")


def _multipart(fields: dict[str, str], path: Path) -> tuple[bytes, str]:
    b = "pdfc" + uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        out += (f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n').encode()
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    fname = safe_name(path.stem) + path.suffix.lower()
    out += (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{fname}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n").encode()
    out += path.read_bytes() + b"\r\n" + f"--{b}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={b}"


def submit(key: str, path: Path, fields: dict[str, str]) -> str:
    """POST the file once. Retries only 429, which the API rejects without processing."""
    body, ctype = _multipart(fields, path)
    for attempt in range(4):
        try:
            status, raw = _http("POST", f"{API}/convert", key, body,
                                {"Content-Type": ctype}, timeout=300)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            die(f"upload failed ({e}). The server may or may not have accepted the job, so it "
                "was not retried (a retry could bill twice). Check the requests list in the "
                "Datalab dashboard before converting this file again.")
        if status == 429 and attempt < 3:
            wait = 20 * (attempt + 1)
            print(f"rate limited; waiting {wait}s before resubmitting", file=sys.stderr)
            time.sleep(wait)
            continue
        if status != 200:
            raise ApiError(_error_text(status, raw))
        data = json.loads(raw)
        if not data.get("success", True) or not data.get("request_id"):
            raise ApiError(f"submit rejected: {data.get('error') or data}")
        return str(data["request_id"])
    raise ApiError("still rate limited after 3 retries; try again later")


class Pending(Exception):
    pass


def poll(key: str, request_id: str, wait_s: float) -> dict[str, Any]:
    url = f"{API}/convert/{request_id}"
    start, delay = time.time(), 2.0
    while True:
        try:
            status, raw = _http("GET", url, key, timeout=120)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            status, raw = None, b""
        if status == 200:
            data = json.loads(raw)
            st = str(data.get("status", "")).lower()
            if st == "complete":
                return _download_result(data)
            if st in ("failed", "error"):
                return data
        elif status not in (None, 429, 500, 502, 503, 504, 529):
            raise ApiError(_error_text(status, raw))
        if time.time() - start > wait_s:
            raise Pending(request_id)
        time.sleep(delay)
        delay = min(delay * 1.5, 15.0)


def _download_result(data: dict[str, Any]) -> dict[str, Any]:
    """Large results come as a signed result_url instead of inline fields."""
    inline = any(data.get(k) is not None for k in ("markdown", "html", "json", "chunks"))
    url = data.get("result_url")
    if inline or not url or not str(url).startswith("https://"):
        return data
    status, raw = _http("GET", str(url), None, timeout=300)  # signed URL: no key sent
    if status != 200:
        raise ApiError(f"could not download the result from result_url: HTTP {status}")
    full = json.loads(raw)
    return {**data, **full}


# --------------------------------------------------------------------------- #
# pages, cost, ledger, cache
# --------------------------------------------------------------------------- #

def count_pages(path: Path) -> int | None:
    suffix = path.suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg", ".webp"):
        return 1
    if suffix != ".pdf":
        return None
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        return None
    try:
        return len(PdfReader(str(path)).pages)
    except Exception:  # noqa: BLE001 - a PDF pypdf can't read may still convert
        return None


def parse_range(spec: str) -> list[int]:
    pages: set[int] = set()
    for part in spec.replace(" ", "").split(","):
        if not part:
            continue
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not m:
            die(f"bad --pages '{spec}': use 0-based pages like 0,4-9,20")
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        if b < a:
            die(f"bad --pages range '{part}'")
        pages.update(range(a, b + 1))
    if not pages:
        die("--pages is empty")
    return sorted(pages)


def human_pages(pages: list[int]) -> str:
    """0-based list -> '1-4, 7' in printed (1-based) numbering."""
    out, i = [], 0
    while i < len(pages):
        j = i
        while j + 1 < len(pages) and pages[j + 1] == pages[j] + 1:
            j += 1
        a, b = pages[i] + 1, pages[j] + 1
        out.append(f"{a}" if a == b else f"{a}-{b}")
        i = j + 1
    return ", ".join(out)


def cost_usd(result: dict[str, Any]) -> float | None:
    """The API reports cost in cents (total_cost, cost_breakdown.final_cost_cents)."""
    cents = (result.get("cost_breakdown") or {}).get("final_cost_cents", result.get("total_cost"))
    return float(cents) / 100 if isinstance(cents, (int, float)) else None


def estimate(cfg: dict[str, Any], mode: str, pages: int, extras: list[str], merge: bool) -> float:
    per_k = cfg["price_per_1k_pages"][mode]
    per_k += sum(cfg["extra_per_1k_pages"].get(e, 0.0) for e in extras)
    return pages * per_k / 1000 + (cfg["merge_cross_page_per_doc"] if merge else 0.0)


def ledger_read() -> list[dict[str, Any]]:
    if not LEDGER.exists():
        return []
    rows = []
    for line in LEDGER.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def ledger_append(row: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    row = {"ts": now().isoformat(timespec="seconds"), **row}
    with LEDGER.open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def requests_30d() -> dict[str, dict[str, Any]]:
    """request_id -> merged submit/final rows, for requests submitted in the last 30 days."""
    cutoff = now() - timedelta(days=30)
    merged: dict[str, dict[str, Any]] = {}
    for r in ledger_read():
        rid = r.get("request_id")
        if not rid:
            continue
        merged.setdefault(rid, {}).update(r if r.get("event") != "submit" else
                                          {**r, "submitted": r.get("ts")})
    out = {}
    for rid, r in merged.items():
        try:
            ts = datetime.fromisoformat(r.get("submitted") or r.get("ts"))
        except (TypeError, ValueError):
            continue
        if ts >= cutoff:
            out[rid] = r
    return out


def row_cost(r: dict[str, Any]) -> float:
    if r.get("cost") is not None:
        return float(r["cost"])
    if r.get("event") == "failed":
        return 0.0
    return float(r.get("cost_est") or 0.0)  # pending: count the estimate


def spent_30d() -> float:
    return sum(row_cost(r) for r in requests_30d().values())


def cache_key(digest: str, fields: dict[str, str]) -> str:
    canon = json.dumps({k: v for k, v in sorted(fields.items()) if k != "skip_cache"})
    return hashlib.sha256((digest + canon).encode()).hexdigest()


def cache_path(key: str) -> Path:
    return CACHE_DIR / key[:2] / f"{key}.json.gz"


def cache_get(key: str) -> dict[str, Any] | None:
    p = cache_path(key)
    if not p.exists():
        return None
    try:
        with gzip.open(p, "rt") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def cache_put(key: str, result: dict[str, Any]) -> None:
    p = cache_path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as fh:
        json.dump(result, fh)
    os.replace(tmp, p)


# --------------------------------------------------------------------------- #
# outputs
# --------------------------------------------------------------------------- #

def write_outputs(result: dict[str, Any], out_dir: Path, stem: str, outputs: list[str],
                  meta: dict[str, Any]) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def put(name: str, text: str) -> Path:
        p = out_dir / name
        p.write_text(text, encoding="utf-8")
        written.append(p)
        return p

    md_path = None
    if result.get("markdown") is not None and {"md", "markdown", "latex", "tex"} & set(outputs):
        md_path = put(f"{stem}.md", result["markdown"])
    if "html" in outputs and result.get("html") is not None:
        put(f"{stem}.html", result["html"])
    for fmt, suffix in (("json", "json"), ("chunks", "chunks.json")):
        if fmt in outputs and result.get(fmt) is not None:
            val = result[fmt]
            put(f"{stem}.{suffix}", val if isinstance(val, str) else json.dumps(val, indent=1))

    for name, b64 in (result.get("images") or {}).items():
        fname = Path(str(name)).name  # no directories from the server
        if not re.fullmatch(r"[\w.-]+", fname, flags=re.ASCII) or fname.startswith("."):
            fname = safe_name(fname)
        try:
            data = base64.b64decode(b64.split(",", 1)[-1] if b64.startswith("data:") else b64)
        except (ValueError, AttributeError):
            continue
        (out_dir / fname).write_bytes(data)
        written.append(out_dir / fname)

    if md_path and {"latex", "tex"} & set(outputs):
        tex = to_latex(md_path, out_dir / f"{stem}.tex")
        if tex:
            written.append(tex)

    meta_path = out_dir / f"{stem}.meta.json"
    meta["cost_usd"] = cost_usd(result)
    keep = ("page_count", "cost_breakdown", "runtime", "parse_quality_score",
            "versions", "metadata")
    meta_path.write_text(json.dumps({**meta, **{k: result.get(k) for k in keep}}, indent=1) + "\n")
    written.append(meta_path)
    return written


def to_latex(md_path: Path, tex_path: Path) -> Path | None:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        print("warning: pandoc not found, so no .tex was written (the markdown was). Install "
              "pandoc (https://pandoc.org/installing.html) and rerun: the cache makes it free.",
              file=sys.stderr)
        return None
    text = md_path.read_text(encoding="utf-8")
    text = PAGE_SEP.sub("", text)
    # marker writes chemistry/units super- and subscripts as HTML, which pandoc's
    # LaTeX writer would drop; turn them into pandoc's own ^sup^ / ~sub~.
    text = re.sub(r"<sup>([^<\n]*?)</sup>", lambda m: "^" + m.group(1).replace(" ", "\\ ") + "^", text)
    text = re.sub(r"<sub>([^<\n]*?)</sub>", lambda m: "~" + m.group(1).replace(" ", "\\ ") + "~", text)
    proc = subprocess.run(
        [pandoc, "-f", "markdown", "-t", "latex", "--standalone", "-o", tex_path.name],
        input=text, text=True, cwd=md_path.parent, capture_output=True)
    if proc.returncode != 0:
        print(f"warning: pandoc failed: {proc.stderr.strip()[:500]}", file=sys.stderr)
        return None
    return tex_path


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def plan_request(args: argparse.Namespace, cfg: dict[str, Any]) -> dict[str, Any]:
    preset = PRESETS[args.preset]
    mode = args.mode or preset["mode"]
    images = preset["images"] if args.images is None else args.images
    if mode == "lite":
        images = False  # lite never extracts images
    extras = list(preset["extras"])
    for e in (args.extras or "").split(","):
        if e.strip() and e.strip() not in extras:
            extras.append(e.strip())
    if not images:
        extras = [e for e in extras if e not in ("chart_understanding", "infographic")]
    merge = preset["merge"] if args.merge_cross_page is None else args.merge_cross_page

    outputs = []
    for f in (args.format or "md").split(","):
        f = f.strip().lower()
        if f not in FORMATS:
            die(f"unknown format '{f}' (use md, html, json, chunks, latex)")
        outputs.append(f)
    api_formats = sorted({FORMATS[f] for f in outputs})

    fields = {
        "mode": mode,
        "output_format": ",".join(api_formats),
        "paginate": "true",
        "disable_image_extraction": "false" if images else "true",
        "fence_synthetic_captions": "true",
        "skip_cache": "false",
        **preset["flags"],
    }
    if extras:
        fields["extras"] = ",".join(extras)
    if merge:
        fields["merge_cross_page"] = "true"
    return {"mode": mode, "images": images, "extras": extras, "merge": merge,
            "outputs": outputs, "fields": fields}


def cmd_convert(args: argparse.Namespace) -> None:
    cfg = load_config()
    src = Path(args.file).expanduser()
    if not src.is_file():
        die(f"no such file: {src}")
    plan = plan_request(args, cfg)
    fields = plan["fields"]
    limit = args.max_pages or int(cfg["max_pages"])

    total = count_pages(src)
    if args.pages:
        sel = parse_range(args.pages)
        if total is not None:
            beyond = [p for p in sel if p >= total]
            if beyond:
                die(f"--pages goes past the end: the document has {total} pages (0-{total - 1})")
        n_pages, pages_note = len(sel), f"pages {human_pages(sel)} (0-based {args.pages})"
        fields["page_range"] = args.pages.replace(" ", "")
    else:
        n_pages = total
        pages_note = f"all {total} pages" if total is not None else \
            f"page count unknown; capped at {limit} by max_pages"
        fields["max_pages"] = str(limit)
    if n_pages is not None and n_pages > limit:
        refuse(f"{n_pages} pages is over the per-call limit of {limit}. Convert part of it "
               f"with --pages, or, once the user has agreed to the cost, pass --max-pages "
               f"{n_pages}.")
    billable = n_pages if n_pages is not None else limit
    est = estimate(cfg, plan["mode"], billable, plan["extras"], plan["merge"])

    digest = sha256(src)
    # The whole document fits under the cap: the cap doesn't change the result.
    whole = total is not None and "page_range" not in fields and total <= limit
    ckey = cache_key(digest, {k: v for k, v in fields.items() if not (whole and k == "max_pages")})
    stem = safe_name(args.name or src.stem)
    out_dir = Path(args.output).expanduser() if args.output else Path.cwd() / stem
    cached = None if args.refresh else cache_get(ckey)

    budget = float(cfg["budget_usd_30d"])
    spent = spent_30d()
    print(f"{src.name}: {pages_note}; mode {plan['mode']}"
          f"{', images' if plan['images'] else ', no images'}"
          f"{', extras ' + ','.join(plan['extras']) if plan['extras'] else ''}"
          f"{', cross-page merge' if plan['merge'] else ''}; formats {','.join(plan['outputs'])}")
    if cached is not None:
        print("cost: $0 (cached result)")
    else:
        print(f"cost: about {money(est)} (list price); 30-day spend {money(spent)} "
              f"of {money(budget)} budget")
    sys.stdout.flush()
    if args.dry_run:
        return
    if cached is None and spent + est > budget:
        refuse(f"this would take 30-day spend to about {money(spent + est)}, over the "
               f"{money(budget)} budget. Ask the user; only they should raise it "
               f"(`pdfc.py config budget_usd_30d N`).")

    meta = {"source": str(src.resolve()), "sha256": digest, "preset": args.preset,
            "request": fields, "converted": now().isoformat(timespec="seconds")}
    if cached is not None:
        result = cached
        meta.update(cached=True, request_id=cached.get("_request_id"))
    else:
        key = require_key(cfg)
        try:
            rid = submit(key, src, fields)
        except ApiError as e:
            die(str(e))
        ledger_append({"event": "submit", "request_id": rid, "file": str(src.resolve()),
                       "sha256": digest, "mode": plan["mode"], "pages_est": billable,
                       "cost_est": round(est, 6), "cache_key": ckey, "out_dir": str(out_dir.resolve()),
                       "stem": stem, "outputs": plan["outputs"], "fields": fields,
                       "preset": args.preset})
        print(f"submitted: request {rid}", file=sys.stderr)
        result = _finish(key, rid, ckey, args.wait)
        meta.update(cached=False, request_id=rid)
    _report(result, out_dir, stem, plan["outputs"], meta)


def _finish(key: str, rid: str, ckey: str, wait: float) -> dict[str, Any]:
    try:
        result = poll(key, rid, wait)
    except Pending:
        print(f"still processing after {int(wait)}s. Nothing is lost and it is billed once: "
              f"collect it later with `pdfc.py fetch {rid}` (do not convert again).",
              file=sys.stderr)
        raise SystemExit(EXIT_PENDING)
    except ApiError as e:
        die(f"{e} (request {rid}; retry collecting it with `pdfc.py fetch {rid}`)")
    ok = str(result.get("status")).lower() == "complete" and result.get("success") is not False
    ledger_append({"event": "complete" if ok else "failed", "request_id": rid,
                   "pages": result.get("page_count"),
                   "cost": cost_usd(result),
                   "cost_breakdown": result.get("cost_breakdown")})
    if not ok:
        die(f"conversion failed: {result.get('error') or result.get('status')} (request {rid})")
    result["_request_id"] = rid
    cache_put(ckey, result)
    return result


def _report(result: dict[str, Any], out_dir: Path, stem: str, outputs: list[str],
            meta: dict[str, Any]) -> None:
    written = write_outputs(result, out_dir, stem, outputs, meta)
    n_img = sum(1 for p in written if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".gif"))
    docs = [p for p in written if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".gif")]
    print(f"pages converted: {result.get('page_count')}; cost reported: "
          f"{money(cost_usd(result)) if not meta.get('cached') else '$0 (cached)'}")
    print(f"wrote to {out_dir}:")
    for p in docs:
        print(f"  {p.name}")
    if n_img:
        print(f"  + {n_img} image file(s), referenced from the markdown by file name")


def cmd_fetch(args: argparse.Namespace) -> None:
    cfg = load_config()
    rows = [r for r in ledger_read() if r.get("request_id") == args.request_id
            and r.get("event") == "submit"]
    if not rows:
        die(f"request {args.request_id} is not in the ledger ({LEDGER})")
    sub = rows[-1]
    key = require_key(cfg)
    result = _finish(key, args.request_id, sub["cache_key"], args.wait)
    out_dir = Path(args.output).expanduser() if args.output else Path(sub["out_dir"])
    meta = {"source": sub.get("file"), "sha256": sub.get("sha256"), "preset": sub.get("preset"),
            "request": sub.get("fields"), "request_id": args.request_id, "cached": False,
            "converted": now().isoformat(timespec="seconds")}
    _report(result, out_dir, sub["stem"], sub["outputs"], meta)


def cmd_setup(args: argparse.Namespace) -> None:
    if args.remove:
        removed = remove_key()
        save_config({"key_store": None})
        print("removed the key from: " + (", ".join(removed) if removed else "nowhere (none stored)"))
        return
    print(f"""Datalab key setup.
  1. Create a key just for agents at {KEYS_URL}
  2. Give that key a 30-day spend cap (e.g. $5-10). The cap is the only hard limit:
     once reached, the API refuses with HTTP 402, whatever the caller does.
""")
    if sys.stdin.isatty():
        key = getpass.getpass("Paste the key (input hidden): ").strip()
    else:
        key = sys.stdin.readline().strip()
    if not key:
        die("no key given")
    status, raw = _http("GET", f"{API}/user_health", key, timeout=30)
    if status != 200:
        die("the key did not work: " + _error_text(status, raw))
    print("key verified with Datalab")

    usable, why = keyring_usable()
    store = args.store or ("keyring" if usable else "file")
    if store == "keyring" and not usable:
        die(f"cannot use the OS keyring: {why}. Use --store file.")
    try:
        where = store_key(key, store)
    except Exception as e:  # noqa: BLE001
        if store == "keyring" and not args.store:
            print(f"keyring failed ({e}); using a file instead", file=sys.stderr)
            store, where = "file", store_key(key, "file")
        else:
            die(f"could not store the key: {e}")
    if store == "keyring" and KEY_FILE.exists():
        KEY_FILE.unlink()  # one copy only
    updates: dict[str, Any] = {"key_store": store}
    if args.budget is not None:
        updates["budget_usd_30d"] = args.budget
    if args.max_pages is not None:
        updates["max_pages"] = args.max_pages
    save_config(updates)
    cfg = load_config()
    print(f"stored in: {where}")
    print(f"local guards: {cfg['max_pages']} pages per call, {money(float(cfg['budget_usd_30d']))} "
          f"per 30 days (change with `pdfc.py config`)")
    if os.environ.get(ENV_KEY):
        print(f"note: ${ENV_KEY} is set in this shell and takes precedence over the stored key")


def cmd_doctor(args: argparse.Namespace) -> None:
    cfg = load_config()

    def line(tag: str, msg: str) -> None:
        print(f"  [{tag}] {msg}")

    print("pdf-convert doctor")
    line("ok", f"python {sys.version.split()[0]}")
    try:
        import pypdf  # type: ignore
        line("ok", f"pypdf {pypdf.__version__} (page counts before upload)")
    except ImportError:
        line("warn", "pypdf missing: page counts unknown, so each call is capped at max_pages "
                     "and estimated at that many pages (run with `uv run` to get pypdf)")
    usable, why = keyring_usable()
    line("ok" if usable else "info", f"OS keyring: {why if not usable else 'available (' + why + ')'}")
    pandoc = shutil.which("pandoc")
    if pandoc:
        v = subprocess.run([pandoc, "--version"], capture_output=True, text=True).stdout.split("\n")[0]
        line("ok", f"{v} (LaTeX output)")
    else:
        line("warn", "pandoc missing: everything works except --format latex")

    key, source = load_key(cfg)
    if not key:
        line("miss", f"no API key: run `{_self_cmd()} setup` in a terminal")
    else:
        if source == str(KEY_FILE) and os.name != "nt" and KEY_FILE.stat().st_mode & 0o077:
            line("warn", f"{KEY_FILE} is readable by other users: chmod 600 it")
        try:
            status, raw = _http("GET", f"{API}/user_health", key, timeout=30)
            if status == 200:
                line("ok", f"API key from {source} accepted by Datalab")
            else:
                line("fail", f"API key from {source}: {_error_text(status, raw)}")
        except (urllib.error.URLError, OSError) as e:
            line("fail", f"cannot reach Datalab: {e}")
        line("info", "the key's own spend cap can't be checked from here; confirm it at " + KEYS_URL)

    reqs = requests_30d()
    spent = sum(row_cost(r) for r in reqs.values())
    pending = [rid for rid, r in reqs.items() if r.get("event") == "submit"]
    line("ok" if spent < float(cfg["budget_usd_30d"]) else "warn",
         f"30-day spend {money(spent)} of {money(float(cfg['budget_usd_30d']))} budget over "
         f"{len(reqs)} request(s); page limit {cfg['max_pages']} per call")
    for rid in pending:
        line("warn", f"request {rid} was never collected: `pdfc.py fetch {rid}`")
    size = sum(p.stat().st_size for p in CACHE_DIR.rglob("*.json.gz")) if CACHE_DIR.exists() else 0
    line("info", f"cache {size / 1e6:.1f} MB in {CACHE_DIR}; config {CONFIG_DIR}; ledger {LEDGER}")


def cmd_usage(args: argparse.Namespace) -> None:
    cfg = load_config()
    reqs = requests_30d()
    if not reqs:
        print("no conversions in the last 30 days")
    for rid, r in sorted(reqs.items(), key=lambda kv: kv[1].get("submitted") or ""):
        state = {"submit": "pending"}.get(r.get("event"), r.get("event"))
        cost = money(r["cost"]) if r.get("cost") is not None else f"~{money(r.get('cost_est'))}"
        print(f"{(r.get('submitted') or '')[:16]}  {state:<8} {r.get('mode', ''):<8} "
              f"{r.get('pages') or r.get('pages_est') or '?':>4} p  {cost:>9}  "
              f"{Path(r.get('file', '?')).name}")
    print(f"total {money(spent_30d())} of {money(float(cfg['budget_usd_30d']))} budget (30 days)")


def cmd_config(args: argparse.Namespace) -> None:
    if args.key is None:
        cfg = load_config()
        print(json.dumps({k: v for k, v in cfg.items()}, indent=2))
        print(f"(file: {CONFIG_FILE})")
        return
    if args.key not in SETTABLE:
        die(f"settable keys: {', '.join(SETTABLE)}")
    if args.value is None:
        die("give a value")
    try:
        val = SETTABLE[args.key](args.value)
    except ValueError:
        die(f"{args.key} needs a number")
    if val <= 0:
        die(f"{args.key} must be positive")
    save_config({args.key: val})
    print(f"{args.key} = {val}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="pdfc.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("convert", help="convert one document")
    c.add_argument("file")
    c.add_argument("-o", "--output", help="output directory (default: ./<name>/)")
    c.add_argument("--name", help="base name for output files (default: the file's stem)")
    c.add_argument("--preset", choices=list(PRESETS), default="standard")
    c.add_argument("--mode", choices=MODES, help="override the preset's mode")
    c.add_argument("--format", help="comma list of md, html, json, chunks, latex (default md)")
    c.add_argument("--pages", help="0-based page range, e.g. 0,4-9 (page 1 is 0)")
    c.add_argument("--max-pages", type=int, help="per-call page limit for this call "
                                                 "(default: the configured max_pages)")
    c.add_argument("--images", dest="images", action="store_true", default=None)
    c.add_argument("--no-images", dest="images", action="store_false")
    c.add_argument("--extras", help="extra API features, comma list (e.g. chart_understanding)")
    c.add_argument("--merge-cross-page", dest="merge_cross_page", action="store_true", default=None)
    c.add_argument("--no-merge-cross-page", dest="merge_cross_page", action="store_false")
    c.add_argument("--refresh", action="store_true", help="ignore the local cache (costs again)")
    c.add_argument("--dry-run", action="store_true", help="print the plan and cost; no API call")
    c.add_argument("--wait", type=float, default=600, help="seconds to wait for the result")
    c.set_defaults(func=cmd_convert)

    f = sub.add_parser("fetch", help="collect a submitted conversion by request id")
    f.add_argument("request_id")
    f.add_argument("-o", "--output")
    f.add_argument("--wait", type=float, default=600)
    f.set_defaults(func=cmd_fetch)

    s = sub.add_parser("setup", help="store and verify a Datalab API key")
    s.add_argument("--store", choices=["keyring", "file"])
    s.add_argument("--budget", type=float, help="30-day local budget in USD")
    s.add_argument("--max-pages", type=int, help="per-call page limit")
    s.add_argument("--remove", action="store_true", help="delete the stored key")
    s.set_defaults(func=cmd_setup)

    sub.add_parser("doctor", help="check key, tools, budget, cache").set_defaults(func=cmd_doctor)
    sub.add_parser("usage", help="spend over the last 30 days").set_defaults(func=cmd_usage)

    g = sub.add_parser("config", help="show config, or set budget_usd_30d / max_pages")
    g.add_argument("key", nargs="?")
    g.add_argument("value", nargs="?")
    g.set_defaults(func=cmd_config)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
