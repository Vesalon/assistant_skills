#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb"]
# ///
"""OpenAlex literature search and citation-graph CLI.

Fetching uses only the standard library; `sql` needs duckdb (declared inline,
so `uv run oa.py ...` provides it). Every saved work uses one normalized
schema with short ids (W.../A...), so any saved file can be joined in DuckDB.

    oa.py work W4213199992 10.1126/sciadv.abk0644     # free
    oa.py search "physics-informed neural network defect" --limit 25
    oa.py search "neural nets locating voids in solids" --semantic
    oa.py refs W4213199992 --save refs.jsonl
    oa.py cites W4213199992 --limit 50 --sort publication_date:desc
    oa.py author "Susan R. Atlas"
    oa.py author-works A5041159213 --save atlas.jsonl
    oa.py corpus DIR "Shen=A5107232437" "Suresh=A5101640166,A5108087555"
    oa.py enrich DIR
    oa.py connect W4213199992 DIR [--deep]
    oa.py sql DIR "SELECT * FROM shared_references LIMIT 20"
    oa.py get authors/A5041159213 select=id,display_name

API key: $OPENALEX_API_KEY, else ~/.config/openalex/api_key.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

BASE = "https://api.openalex.org"
SKILL_DIR = Path(__file__).resolve().parent
KEY_FILE = Path.home() / ".config" / "openalex" / "api_key"
USER_AGENT = "openalex-skill/1.0 (personal academic research)"

# The API rejects OR filters with more than 100 values, and pages cap at 100.
OR_LIMIT = 100
PAGE = 100

# Enough for normalize() to fill everything but abstract/topics/keywords.
# Used for bulk graph fetches (citers, reference resolution) to keep payloads small.
GRAPH_SELECT = (
    "id,doi,title,publication_year,publication_date,type,cited_by_count,"
    "authorships,primary_location,referenced_works"
)


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

def _load_key() -> str | None:
    key = os.environ.get("OPENALEX_API_KEY")
    if not key and KEY_FILE.exists():
        key = KEY_FILE.read_text()
    return key.strip() if key and key.strip() else None


API_KEY = _load_key()
USAGE = {"calls": 0, "credits": 0, "remaining": None}


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


class NotFound(Exception):
    pass


def _track(headers) -> None:
    if headers is None:
        return
    used = headers.get("x-ratelimit-credits-used")
    if used is not None:
        USAGE["credits"] += int(used)
    if headers.get("x-ratelimit-remaining") is not None:
        USAGE["remaining"] = headers.get("x-ratelimit-remaining")


def get_json(endpoint: str, params: dict[str, Any] | None = None,
             attempts: int = 6) -> dict[str, Any]:
    """GET one API endpoint, retrying 429/5xx/network errors with backoff."""
    params = {k: v for k, v in (params or {}).items() if v is not None}
    shown = f"{endpoint} {params}" if params else endpoint  # never includes the key
    if API_KEY:
        params["api_key"] = API_KEY
    url = f"{BASE}/{endpoint.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            USAGE["calls"] += 1
            with urllib.request.urlopen(request, timeout=60) as response:
                _track(response.headers)
                return json.load(response)
        except urllib.error.HTTPError as exc:
            _track(exc.headers)
            body = exc.read().decode(errors="replace")
            try:
                message = json.loads(body).get("message") or body
            except ValueError:
                message = body
            if exc.code == 429 and USAGE["remaining"] in ("0", 0):
                die(f"daily OpenAlex budget exhausted ({message[:200]})")
            if exc.code == 429 or exc.code >= 500:
                time.sleep(min(2 ** attempt, 30))
                continue
            if exc.code == 404:
                raise NotFound(shown) from None
            die(f"OpenAlex HTTP {exc.code} for {shown}: {message[:300]}")
        except (urllib.error.URLError, TimeoutError):
            time.sleep(min(2 ** attempt, 30))
    die(f"request repeatedly failed: {shown}")


def fetch_works(params: dict[str, Any], limit: int | None = None,
                endpoint: str = "works") -> tuple[list[dict], int]:
    """Cursor-paginate a list endpoint. Returns (raw records, total match count)."""
    params = dict(params)
    params["per_page"] = PAGE if limit is None else max(1, min(PAGE, limit))
    params.setdefault("cursor", "*")
    records: list[dict] = []
    total = 0
    while True:
        payload = get_json(endpoint, params)
        total = payload.get("meta", {}).get("count") or total
        results = payload.get("results", [])
        records.extend(results)
        if limit is not None and len(records) >= limit:
            return records[:limit], total
        cursor = payload.get("meta", {}).get("next_cursor")
        if not cursor or not results:
            return records, total
        params["cursor"] = cursor


def resolve_ids(ids: Iterable[str], select: str | None = None) -> list[dict]:
    """Fetch works by id, 100 per call. Unindexed ids are silently dropped by the API."""
    unique = list(dict.fromkeys(short(i) for i in ids if i))
    records: list[dict] = []
    for start in range(0, len(unique), OR_LIMIT):
        batch = unique[start:start + OR_LIMIT]
        payload = get_json("works", {"filter": f"openalex_id:{'|'.join(batch)}",
                                     "per_page": PAGE, "select": select})
        records.extend(payload["results"])
    return records


def fetch_by_or_filter(field: str, values: list[str], select: str | None = None,
                       sort: str | None = None) -> list[dict]:
    """All works matching field:v1|v2|..., batching the OR list and de-duplicating."""
    seen: dict[str, dict] = {}
    for start in range(0, len(values), OR_LIMIT):
        batch = values[start:start + OR_LIMIT]
        records, _ = fetch_works({"filter": f"{field}:{'|'.join(batch)}",
                                  "select": select, "sort": sort})
        for record in records:
            seen.setdefault(record["id"], record)
    return list(seen.values())


# --------------------------------------------------------------------------- #
# Ids and normalization
# --------------------------------------------------------------------------- #

def short(openalex_id: str | None) -> str | None:
    """https://openalex.org/W123 -> W123 (no-op on short ids)."""
    return openalex_id.rsplit("/", 1)[-1] if openalex_id else openalex_id


def work_path(ref: str) -> str:
    """Endpoint for a work given a W id, OpenAlex URL, or DOI in any common form."""
    ref = ref.strip()
    lower = ref.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi.org/", "doi:"):
        if lower.startswith(prefix):
            return f"works/doi:{ref[len(prefix):]}"
    if lower.startswith("10."):
        return f"works/doi:{ref}"
    return f"works/{short(ref)}"


def get_work(ref: str, select: str | None = None) -> dict:
    try:
        return get_json(work_path(ref), {"select": select})
    except NotFound:
        die(f"no OpenAlex work for {ref!r}")


def reconstruct_abstract(inverted: dict[str, list[int]] | None) -> str | None:
    """OpenAlex stores abstracts as {word: [positions]}; rebuild the text."""
    if not inverted:
        return None
    size = max(p for positions in inverted.values() for p in positions) + 1
    words: list[str] = [""] * size
    for word, positions in inverted.items():
        for p in positions:
            words[p] = word
    return " ".join(w for w in words if w)


def normalize(work: dict, label: str | None = None) -> dict:
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    authorships = work.get("authorships") or []
    doi = work.get("doi")
    record = {
        "id": short(work.get("id")),
        "doi": doi.removeprefix("https://doi.org/") if doi else None,
        "title": work.get("title") or work.get("display_name"),
        "year": work.get("publication_year"),
        "date": work.get("publication_date"),
        "type": work.get("type"),
        "venue": source.get("display_name"),
        "authors": [(a.get("author") or {}).get("display_name") for a in authorships],
        "author_ids": [short((a.get("author") or {}).get("id")) for a in authorships],
        "cited_by_count": work.get("cited_by_count"),
        "referenced_works": [short(r) for r in work.get("referenced_works") or []],
        "topics": [t["display_name"] for t in work.get("topics") or [] if t.get("display_name")],
        "keywords": [k["display_name"] for k in work.get("keywords") or [] if k.get("display_name")],
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "oa_pdf": (work.get("best_oa_location") or {}).get("pdf_url"),
        "is_retracted": work.get("is_retracted"),
    }
    return {"label": label, **record} if label is not None else record


def name_key(name: str | None) -> tuple[str, str] | None:
    """(surname, first initial) for loose author matching across split profiles."""
    if not name:
        return None
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    parts = re.sub(r"[^\w\s]", " ", ascii_name).split()
    if not parts:
        return None
    return parts[-1].lower(), parts[0][0].lower()


# --------------------------------------------------------------------------- #
# Files and display
# --------------------------------------------------------------------------- #

def write_jsonl(records: Iterable[dict], path: str | Path) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def read_jsonl(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def cached_jsonl(path: Path, refresh: bool, fetch) -> list[dict]:
    """Reuse a saved fetch unless --refresh; fetching costs credits, files don't."""
    if path.exists() and not refresh:
        return read_jsonl(path)
    records = fetch()
    write_jsonl(records, path)
    return records


def row(record: dict, extra: str = "") -> str:
    authors = record.get("authors") or []
    who = "?"
    if authors:
        who = (authors[0] or "?") + (" et al." if len(authors) > 1 else "")
    title = (record.get("title") or "")[:90]
    cites = record.get("cited_by_count") or 0
    line = f"  {record.get('id') or '?':<12} {record.get('year') or '----'}  {cites:>6} cites  {who}: {title}"
    return f"{line}  {extra}" if extra else line


def print_rows(records: list[dict], top: int | None = None, sort_by_cites: bool = True) -> None:
    if sort_by_cites:
        records = sorted(records, key=lambda r: r.get("cited_by_count") or 0, reverse=True)
    for record in records[:top]:
        print(row(record))
    if top is not None and len(records) > top:
        print(f"  ... {len(records) - top} more")


def maybe_save(records: list[dict], path: str | None) -> None:
    if path:
        n = write_jsonl(records, path)
        print(f"\nsaved {n} records -> {path}")


# --------------------------------------------------------------------------- #
# Commands: single lookups and searches
# --------------------------------------------------------------------------- #

def cmd_work(args) -> None:
    for ref in args.ids:
        work = get_work(ref)
        record = normalize(work)
        if args.json:
            print(json.dumps(record, ensure_ascii=False))
            continue
        authors = ", ".join(f"{n} ({i})" for n, i in zip(record["authors"], record["author_ids"]))
        print(f"{record['id']}  {record['title']}")
        print(f"  authors:  {authors}")
        print(f"  year:     {record['year']}  venue: {record['venue']}  type: {record['type']}")
        print(f"  doi:      {record['doi']}  oa_pdf: {record['oa_pdf']}")
        print(f"  cited_by: {record['cited_by_count']}  references: {len(record['referenced_works'])}"
              + ("  RETRACTED" if record["is_retracted"] else ""))
        print(f"  topics:   {'; '.join(record['topics'])}")
        print(f"  keywords: {'; '.join(record['keywords'])}")
        abstract = record["abstract"] or "(none in OpenAlex)"
        if not args.full and len(abstract) > 700:
            abstract = abstract[:700] + " ..."
        print(f"  abstract: {abstract}\n")


def cmd_search(args) -> None:
    if not args.query and not args.filter:
        die("search needs a query and/or --filter")
    params: dict[str, Any] = {"filter": args.filter, "sort": args.sort}
    if args.semantic and args.query:
        # Semantic search returns at most 50 results and does not paginate.
        params.update({"search.semantic": args.query, "per_page": min(args.limit, 50)})
        payload = get_json("works", params)
        works, total = payload["results"], payload["meta"]["count"]
    else:
        params["search"] = args.query
        works, total = fetch_works(params, None if args.all else args.limit)
    records = [normalize(w) for w in works]
    print(f"{total} matches; showing {len(records)} "
          f"({'by ' + args.sort if args.sort else 'by relevance'})\n")
    print_rows(records, sort_by_cites=False)
    maybe_save(records, args.save)


def cmd_refs(args) -> None:
    work = get_work(args.id, select="id,title,referenced_works")
    ref_ids = work.get("referenced_works") or []
    records = [normalize(w) for w in resolve_ids(ref_ids)]
    print(f"{short(work['id'])}  {work.get('title')}")
    print(f"{len(ref_ids)} references, {len(records)} resolved "
          f"(the rest are not indexed works)\n")
    print_rows(records)
    maybe_save(records, args.save)


def cmd_cites(args) -> None:
    work_id = short(get_work(args.id, select="id")["id"])
    works, total = fetch_works({"filter": f"cites:{work_id}", "sort": args.sort},
                               None if args.all else args.limit)
    records = [normalize(w) for w in works]
    print(f"{total} works cite {work_id}; showing {len(records)} by {args.sort}\n")
    print_rows(records, sort_by_cites=False)
    maybe_save(records, args.save)


def cmd_resolve(args) -> None:
    ids = list(args.ids)
    if args.from_file:
        ids += [line.strip() for line in Path(args.from_file).read_text().splitlines() if line.strip()]
    records = [normalize(w) for w in resolve_ids(ids)]
    print(f"{len(set(map(short, ids)))} ids, {len(records)} resolved\n")
    print_rows(records)
    maybe_save(records, args.save)


def cmd_author(args) -> None:
    payload = get_json("authors", {"search": args.name, "per_page": args.limit})
    print(f"{payload['meta']['count']} candidates for {args.name!r}\n")
    first_with_orcid: dict[str, int] = {}
    for n, author in enumerate(payload["results"], start=1):
        stats = author.get("summary_stats") or {}
        orcid = short(author.get("orcid")) or "no ORCID"
        if author.get("orcid") in first_with_orcid:
            orcid += f"  (same ORCID as [{first_with_orcid[author['orcid']]}]: split profile)"
        elif author.get("orcid"):
            first_with_orcid[author["orcid"]] = n
        last = "; ".join(i.get("display_name") or "?"
                         for i in author.get("last_known_institutions") or [])
        history = []
        affiliations = sorted(author.get("affiliations") or [],
                              key=lambda a: max(a.get("years") or [0]), reverse=True)
        for aff in affiliations[:5]:
            years = aff.get("years") or []
            span = f"{min(years)}-{max(years)}" if years else "?"
            history.append(f"{(aff.get('institution') or {}).get('display_name')} ({span})")
        topics = "; ".join(f"{t['display_name']} ({t.get('count')})"
                           for t in (author.get("topics") or [])[:4])
        print(f"[{n}] {author.get('display_name')}  {short(author.get('id'))}  {orcid}")
        print(f"    works {author.get('works_count')}  cited {author.get('cited_by_count')}  "
              f"h-index {stats.get('h_index')}")
        print(f"    last known: {last or '?'}")
        print(f"    affiliations: {'; '.join(history) or '?'}")
        print(f"    topics: {topics or '?'}\n")


def author_works(author_ids: list[str], label: str | None = None,
                 select: str | None = None) -> list[dict]:
    """Every work by any of the given author ids (a split profile can have several)."""
    ids = [short(a) for a in author_ids]
    works = fetch_by_or_filter("author.id", ids, select=select, sort="publication_date:desc")
    return [normalize(w, label) for w in works]


def cmd_author_works(args) -> None:
    records = author_works(args.ids, args.label)
    print(f"{len(records)} works for {', '.join(args.ids)}; top by citations:\n")
    print_rows(records, top=args.top)
    maybe_save(records, args.save)


def cmd_get(args) -> None:
    params = dict(p.split("=", 1) for p in args.params)
    print(json.dumps(get_json(args.endpoint, params), indent=2, ensure_ascii=False))


# --------------------------------------------------------------------------- #
# Commands: group corpora
# --------------------------------------------------------------------------- #

def parse_group(spec: str) -> tuple[str, list[str]]:
    label, sep, ids = spec.rpartition("=")
    if not sep or not label or not ids:
        die(f"group spec must be LABEL=A123[,A456]; got {spec!r}")
    return label, [i.strip() for i in ids.split(",") if i.strip()]


def write_edges(records: list[dict], path: Path) -> None:
    import csv

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["label", "citing_id", "referenced_id"])
        for record in records:
            for ref in record["referenced_works"]:
                writer.writerow([record["label"], record["id"], ref])


def check_author_ids(label: str, ids: list[str]) -> None:
    """Warn about the two ways a stored author id goes wrong: it shrank to a
    fragment after OpenAlex re-clustered the person, or the person is split
    across several ids that share an ORCID."""
    for aid in ids:
        try:
            author = get_json(f"authors/{short(aid)}",
                              {"select": "id,display_name,works_count,orcid"})
        except NotFound:
            print(f"  WARNING {label}: {aid} not found; re-resolve with `author`", file=sys.stderr)
            continue
        print(f"  {label}: {aid} = {author['display_name']}, {author['works_count']} works, "
              f"ORCID {short(author.get('orcid')) or 'none'}", file=sys.stderr)
        if (author.get("works_count") or 0) < 5:
            print(f"  WARNING {label}: {aid} has only {author['works_count']} works; likely a "
                  f"fragment left by re-clustering. Re-resolve with `author`.", file=sys.stderr)
        if author.get("orcid"):
            twins = get_json("authors", {"filter": f"orcid:{short(author['orcid'])}",
                                         "select": "id,display_name,works_count"})["results"]
            known = {short(i) for i in ids}
            for twin in twins:
                tid = short(twin["id"])
                if tid in known:
                    continue
                print(f"  WARNING {label}: {tid} ({twin['display_name']}, "
                      f"{twin['works_count']} works) shares this ORCID; add it as "
                      f"{label}={','.join([*ids, str(tid)])} if it is the same person",
                      file=sys.stderr)


def cmd_corpus(args) -> None:
    out = Path(args.dir)
    out.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for spec in args.groups:
        label, ids = parse_group(spec)
        check_author_ids(label, ids)
        group = author_works(ids, label)
        print(f"  {label:<24} {len(group):>5} works collected", file=sys.stderr)
        records.extend(group)
    write_jsonl(records, out / "works.jsonl")
    write_edges(records, out / "reference_edges.csv")
    placeholder = out / "referenced_works.jsonl"
    if not placeholder.exists():
        placeholder.touch()
    print(f"wrote {len(records)} works -> {out}/works.jsonl (+ reference_edges.csv)")
    if args.enrich:
        enrich(out, all_refs=False)


def enrich(directory: Path, all_refs: bool) -> None:
    records = read_jsonl(directory / "works.jsonl")
    counts: Counter = Counter()
    labels: dict[str, set] = defaultdict(set)
    for record in records:
        for ref in record["referenced_works"]:
            counts[ref] += 1
            labels[ref].add(record["label"])
    if all_refs:
        ids = list(counts)
    else:
        ids = [r for r in counts if counts[r] > 1 or len(labels[r]) > 1]
    print(f"resolving {len(ids)} of {len(counts)} referenced works "
          f"({'all' if all_refs else 'cited >1x or by >1 group'})...", file=sys.stderr)
    resolved = [normalize(w) for w in resolve_ids(ids, select=GRAPH_SELECT)]
    for record in resolved:
        record.pop("referenced_works")
    n = write_jsonl(resolved, directory / "referenced_works.jsonl")
    print(f"wrote {n} records -> {directory}/referenced_works.jsonl")


def cmd_enrich(args) -> None:
    enrich(Path(args.dir), args.all)


def cmd_sql(args) -> None:
    import duckdb

    directory = Path(args.dir).resolve()
    if not (directory / "works.jsonl").exists():
        die(f"{directory}/works.jsonl not found; build it with `corpus` first")
    os.chdir(directory)  # views.sql reads files relative to the corpus dir
    con = duckdb.connect()
    con.execute((SKILL_DIR / "views.sql").read_text())
    if args.query:
        con.sql(" ".join(args.query)).show(max_width=args.width, max_rows=args.rows)
        return
    views = [r[0] for r in con.execute(
        "SELECT view_name FROM duckdb_views() WHERE NOT internal ORDER BY 1").fetchall()]
    for view in views:
        count = con.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        print(f"  {view:<26} {count:>7} rows")


# --------------------------------------------------------------------------- #
# Command: connect (how a seed paper reaches a group's corpus)
# --------------------------------------------------------------------------- #

def cmd_connect(args) -> None:
    directory = Path(args.dir)
    corpus = read_jsonl(directory / "works.jsonl")
    if not corpus or "label" not in corpus[0]:
        die(f"{directory}/works.jsonl needs labeled works; build it with `corpus`")

    # Corpus side: which groups wrote each work, and which groups cite each work.
    work_labels: dict[str, set] = defaultdict(set)
    ref_labels: dict[str, set] = defaultdict(set)
    corpus_by_id: dict[str, dict] = {}
    for record in corpus:
        work_labels[record["id"]].add(record["label"])
        corpus_by_id.setdefault(record["id"], record)
        for ref in record["referenced_works"]:
            ref_labels[ref].add(record["label"])
    corpus_ids = set(work_labels)
    all_labels = sorted({r["label"] for r in corpus})

    seed = normalize(get_work(args.seed))
    sid = seed["id"]
    seed_dir = directory / f"seed_{sid}"
    seed_dir.mkdir(exist_ok=True)
    (seed_dir / "seed.json").write_text(json.dumps(seed, ensure_ascii=False, indent=1))

    seed_refs = cached_jsonl(seed_dir / "refs.jsonl", args.refresh, lambda: [
        normalize(w) for w in resolve_ids(seed["referenced_works"], select=GRAPH_SELECT)])
    citers = cached_jsonl(seed_dir / "citers.jsonl", args.refresh, lambda: [
        normalize(w) for w in fetch_works({"filter": f"cites:{sid}", "select": GRAPH_SELECT})[0]])
    citer_ids = {c["id"] for c in citers}
    seed_ref_ids = set(seed["referenced_works"])
    top = args.top
    report: dict[str, Any] = {"seed": sid, "threshold": args.threshold, "labels": all_labels}
    tally: dict[str, Counter] = defaultdict(Counter)

    def labels_str(labels: Iterable[str]) -> str:
        return "[" + ", ".join(sorted(labels)) + "]"

    def section(title: str, note: str) -> None:
        print(f"\n== {title}\n   {note}")

    print(f"seed   {sid}  {seed['title']} ({seed['year']})")
    print(f"       {len(seed['referenced_works'])} refs ({len(seed_refs)} resolved), "
          f"{len(citers)} citers")
    print(f"corpus {directory}: " + ", ".join(
        f"{lab} ({sum(1 for r in corpus if r['label'] == lab)})" for lab in all_labels))

    # 1. Direct citation either way.
    section("1. Direct citation", "corpus cites seed / seed cites corpus")
    direct = [r for r in corpus if sid in r["referenced_works"]]
    seed_cites = sorted(seed_ref_ids & corpus_ids)
    for r in direct:
        tally[r["label"]]["direct"] += 1
        print(row(r, f"{r['label']} cites seed"))
    for wid in seed_cites:
        for lab in work_labels[wid]:
            tally[lab]["direct"] += 1
        print(row(corpus_by_id[wid], f"seed cites {labels_str(work_labels[wid])}"))
    if not direct and not seed_cites:
        print("  none")
    report["direct"] = {"corpus_cites_seed": [r["id"] for r in direct], "seed_cites_corpus": seed_cites}

    # 2. Author level: seed authors co-authoring with, citing, or cited by the corpus.
    section("2. Author level", "seed authors as co-authors of corpus works, and citations between "
            "their other work and the corpus")
    seed_authors = [(a, n) for a, n in zip(seed["author_ids"], seed["authors"]) if a]
    author_report = []
    coauthored_works: dict[str, set] = defaultdict(set)  # distinct works, across seed authors
    for aid, name in seed_authors:
        coauthored = [r for r in corpus if aid in r["author_ids"]]
        key = name_key(name)
        name_only = [r for r in corpus if aid not in r["author_ids"] and key and any(
            name_key(n) == key for n in r["authors"])]
        works = cached_jsonl(seed_dir / f"author_{aid}.jsonl", args.refresh, lambda aid=aid: [
            normalize(w) for w in fetch_works({"filter": f"author.id:{aid}",
                                               "select": "id,title,publication_year,cited_by_count,"
                                                         "authorships,referenced_works"})[0]])
        their_ids = {w["id"] for w in works} - {sid}
        corpus_cites_them = Counter()
        for r in corpus:
            corpus_cites_them[r["label"]] += len(their_ids & set(r["referenced_works"]))
        they_cite_corpus = Counter()
        for w in works:
            for wid in set(w["referenced_works"]) & corpus_ids:
                for lab in work_labels[wid]:
                    they_cite_corpus[lab] += 1
        print(f"  {name} ({aid}, {len(works)} works)")
        for lab in all_labels:
            co = [r for r in coauthored if r["label"] == lab]
            nm = [r for r in name_only if r["label"] == lab]
            if co or nm or corpus_cites_them[lab] or they_cite_corpus[lab]:
                coauthored_works[lab].update(r["id"] for r in co)
                tally[lab]["coauthored"] = len(coauthored_works[lab])
                tally[lab]["cites_seed_authors"] += corpus_cites_them[lab]
                print(f"    {lab}: co-authored {len(co)}, name-match-only {len(nm)}, "
                      f"{lab} cites them {corpus_cites_them[lab]}x, they cite {lab} {they_cite_corpus[lab]}x")
                for r in sorted(co, key=lambda r: r.get("year") or 0)[:top]:
                    print("    " + row(r))
                for r in nm[:top]:
                    print("    " + row(r, "NAME MATCH ONLY: split profile or namesake, verify"))
        author_report.append({"author": aid, "name": name, "works": len(works),
                              "coauthored": [r["id"] for r in coauthored],
                              "name_match_only": [r["id"] for r in name_only],
                              "corpus_cites_them": dict(corpus_cites_them),
                              "they_cite_corpus": dict(they_cite_corpus)})
    report["authors"] = author_report

    # 3. One intermediary work.
    section("3. One intermediary", "shared ancestor: both cite W  |  common descendant: D cites both  |  "
            "chains: corpus cites a seed citer, or seed cites a corpus citer")
    ancestors = sorted(seed_ref_ids & set(ref_labels))
    descendants = [c for c in citers if set(c["referenced_works"]) & corpus_ids]
    corpus_cites_citer = sorted(citer_ids & set(ref_labels))
    seed_ref_cites_corpus = [r for r in seed_refs if set(r["referenced_works"]) & corpus_ids]
    refs_by_id = {r["id"]: r for r in seed_refs}
    citers_by_id = {c["id"]: c for c in citers}

    print(f"  shared ancestors: {len(ancestors)}")
    for wid in ancestors[:top]:
        print(row(refs_by_id.get(wid, {"id": wid}), labels_str(ref_labels[wid])))
    for wid in ancestors:
        for lab in ref_labels[wid]:
            tally[lab]["ancestor_1"] += 1
    print(f"  common descendants: {len(descendants)}")
    for c in sorted(descendants, key=lambda c: c.get("cited_by_count") or 0, reverse=True)[:top]:
        hit = set(c["referenced_works"]) & corpus_ids
        labs = set().union(*(work_labels[w] for w in hit))
        for lab in labs:
            tally[lab]["descendant_1"] += 1
        print(row(c, f"also cites {', '.join(sorted(hit))} {labels_str(labs)}"))
    print(f"  corpus cites a seed citer: {len(corpus_cites_citer)}")
    for wid in corpus_cites_citer[:top]:
        print(row(citers_by_id[wid], labels_str(ref_labels[wid])))
    print(f"  seed cites a corpus citer: {len(seed_ref_cites_corpus)}")
    for r in seed_ref_cites_corpus[:top]:
        hit = set(r["referenced_works"]) & corpus_ids
        print(row(r, f"cites {', '.join(sorted(hit))}"))
    report["one_intermediary"] = {
        "shared_ancestors": {w: sorted(ref_labels[w]) for w in ancestors},
        "common_descendants": {c["id"]: sorted(set(c["referenced_works"]) & corpus_ids) for c in descendants},
        "corpus_cites_seed_citer": corpus_cites_citer,
        "seed_cites_corpus_citer": [r["id"] for r in seed_ref_cites_corpus],
    }

    # 4. Two intermediaries: works cited by both the seed's citers and the corpus.
    section("4. Shared ancestors of the seed's citers", f"W cited by a seed citer AND by the corpus; "
            f"works with >= {args.threshold:,} global citations are set aside as superconnectors")
    coupling: Counter = Counter()
    for c in citers:
        for wid in set(c["referenced_works"]):
            if wid in ref_labels and wid not in seed_ref_ids and wid not in corpus_ids and wid != sid:
                coupling[wid] += 1
    meta = {r["id"]: r for r in cached_jsonl(seed_dir / "coupled.jsonl", args.refresh, lambda: [
        normalize(w) for w in resolve_ids(list(coupling), select=GRAPH_SELECT)])}
    specific = [w for w in coupling if (meta.get(w, {}).get("cited_by_count") or 0) < args.threshold]
    supers = [w for w in coupling if w not in set(specific)]

    def order(ids: list[str]) -> list[str]:
        # Most seed citers first; among ties, the less globally cited (more specific) first.
        return sorted(ids, key=lambda w: (-coupling[w], meta.get(w, {}).get("cited_by_count") or 0))
    for lab in all_labels:
        mine = [w for w in order(specific) if lab in ref_labels[w]]
        tally[lab]["ancestor_2"] = len(mine)
        print(f"\n  {lab}: {len(mine)} shared works (n = seed citers citing it)")
        for wid in mine[:top]:
            print(row(meta.get(wid, {"id": wid}), f"n={coupling[wid]}"))
    print(f"\n  superconnectors set aside: {len(supers)}")
    for wid in order(supers)[:top]:
        print(row(meta.get(wid, {"id": wid}), f"n={coupling[wid]} {labels_str(ref_labels[wid])}"))
    report["two_intermediaries"] = {
        "shared_ancestors": {w: {"citers": coupling[w], "labels": sorted(ref_labels[w])} for w in order(specific)},
        "superconnectors": {w: {"citers": coupling[w], "labels": sorted(ref_labels[w])} for w in order(supers)},
    }

    # 5. Optional: descendants two hops from one side (needs the corpus's own citers).
    if args.deep:
        section("5. Two-hop common descendants", "E cites a corpus work and a seed citer  |  "
                "a seed citer cites a corpus citer")
        corpus_citers = cached_jsonl(directory / "corpus_citers.jsonl", args.refresh, lambda: [
            normalize(w) for w in fetch_by_or_filter("cites", sorted(corpus_ids), select=GRAPH_SELECT)])
        descendant_ids = {c["id"] for c in descendants}
        corpus_citer_ids = {e["id"] for e in corpus_citers}
        via_citer = [e for e in corpus_citers
                     if set(e["referenced_works"]) & citer_ids and e["id"] not in descendant_ids]
        via_corpus_citer = [c for c in citers
                            if set(c["referenced_works"]) & corpus_citer_ids and c["id"] not in descendant_ids]
        # Which groups each two-hop descendant reaches: directly through the corpus
        # works it cites, or through the corpus works its corpus-citer references cite.
        corpus_citer_hits = {e["id"]: set(e["referenced_works"]) & corpus_ids for e in corpus_citers}
        def reached(w: dict, via: str) -> set:
            if via == "corpus":
                hits = set(w["referenced_works"]) & corpus_ids
            else:
                hits = set().union(*(corpus_citer_hits[e] for e in set(w["referenced_works"]) & corpus_citer_ids))
            return set().union(*(work_labels[h] for h in hits)) if hits else set()

        print(f"  ({len(corpus_citers)} works cite the corpus)")
        for title, found, via in (("E cites a corpus work + a seed citer", via_citer, "corpus"),
                                  ("seed citer cites a corpus citer", via_corpus_citer, "citer")):
            per_label = Counter(lab for w in found for lab in reached(w, via))
            print(f"  {title}: {len(found)}  {dict(per_label)}")
            for w in sorted(found, key=lambda w: w.get("cited_by_count") or 0, reverse=True)[:top]:
                print(row(w, labels_str(reached(w, via))))
        report["two_hop_descendants"] = {"cites_corpus_and_seed_citer": [e["id"] for e in via_citer],
                                         "seed_citer_cites_corpus_citer": [c["id"] for c in via_corpus_citer]}

    columns = ["direct", "coauthored", "cites_seed_authors", "ancestor_1", "descendant_1", "ancestor_2"]
    width = max(len(lab) for lab in all_labels + ["group"]) + 2
    print("\n== Summary by group (coauthored = distinct works; cites_seed_authors = citation count)")
    print("  " + f"{'group':<{width}}" + "".join(f"{c:>{len(c) + 2}}" for c in columns))
    for lab in all_labels:
        print("  " + f"{lab:<{width}}" + "".join(f"{tally[lab][c]:>{len(c) + 2}}" for c in columns))
    report["summary"] = {lab: {c: tally[lab][c] for c in columns} for lab in all_labels}
    (seed_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"\nfull report -> {seed_dir}/report.json (fetched data cached alongside)")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="oa.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("work", help="show works by W id or DOI (free)")
    p.add_argument("ids", nargs="+")
    p.add_argument("--json", action="store_true", help="print normalized JSON lines")
    p.add_argument("--full", action="store_true", help="do not truncate the abstract")
    p.set_defaults(func=cmd_work)

    p = sub.add_parser("search", help="keyword or semantic search over works")
    p.add_argument("query", nargs="?")
    p.add_argument("--filter", help="OpenAlex filter, e.g. publication_year:>2019,type:review")
    p.add_argument("--sort", help="e.g. cited_by_count:desc (default: relevance)")
    p.add_argument("--semantic", action="store_true", help="embedding search (max 50 results)")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--all", action="store_true", help="every match (100 per call)")
    p.add_argument("--save")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("refs", help="a work's references, resolved")
    p.add_argument("id")
    p.add_argument("--save")
    p.set_defaults(func=cmd_refs)

    p = sub.add_parser("cites", help="works citing a work")
    p.add_argument("id")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--all", action="store_true")
    p.add_argument("--sort", default="cited_by_count:desc")
    p.add_argument("--save")
    p.set_defaults(func=cmd_cites)

    p = sub.add_parser("resolve", help="metadata for a list of W ids")
    p.add_argument("ids", nargs="*")
    p.add_argument("--from", dest="from_file", help="file with one id per line")
    p.add_argument("--save")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("author", help="find author ids by name, with disambiguation detail")
    p.add_argument("name")
    p.add_argument("--limit", type=int, default=8)
    p.set_defaults(func=cmd_author)

    p = sub.add_parser("author-works", help="all works of one person (several ids if split)")
    p.add_argument("ids", nargs="+")
    p.add_argument("--label")
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--save")
    p.set_defaults(func=cmd_author_works)

    p = sub.add_parser("corpus", help="collect labeled works for a group of people into DIR")
    p.add_argument("dir")
    p.add_argument("groups", nargs="+", metavar="LABEL=A123[,A456]")
    p.add_argument("--enrich", action="store_true", help="also run enrich")
    p.set_defaults(func=cmd_corpus)

    p = sub.add_parser("enrich", help="resolve the corpus's notable referenced works")
    p.add_argument("dir")
    p.add_argument("--all", action="store_true", help="resolve every referenced work")
    p.set_defaults(func=cmd_enrich)

    p = sub.add_parser("connect", help="map how a seed paper reaches a corpus")
    p.add_argument("seed")
    p.add_argument("dir")
    p.add_argument("--threshold", type=int, default=10_000, help="superconnector citation cutoff")
    p.add_argument("--deep", action="store_true", help="also fetch the corpus's citers (costly)")
    p.add_argument("--refresh", action="store_true", help="refetch instead of using cached files")
    p.add_argument("--top", type=int, default=10)
    p.set_defaults(func=cmd_connect)

    p = sub.add_parser("sql", help="DuckDB over a corpus DIR (no query: list views)")
    p.add_argument("dir")
    p.add_argument("query", nargs="*")
    p.add_argument("--rows", type=int, default=60)
    p.add_argument("--width", type=int, default=220)
    p.set_defaults(func=cmd_sql)

    p = sub.add_parser("get", help="raw API call: get ENDPOINT [key=value ...]")
    p.add_argument("endpoint")
    p.add_argument("params", nargs="*")
    p.set_defaults(func=cmd_get)

    args = parser.parse_args(argv)
    if not API_KEY and args.cmd != "sql":
        print(f"note: no API key ($OPENALEX_API_KEY or {KEY_FILE}); daily budget is 10x smaller",
              file=sys.stderr)
    try:
        args.func(args)
    finally:
        sys.stdout.flush()
        if USAGE["calls"]:
            print(f"[openalex] {USAGE['calls']} calls, {USAGE['credits']} credits; "
                  f"{USAGE['remaining']} left today", file=sys.stderr)


if __name__ == "__main__":
    main()
