---
name: pdf-convert
description: Convert PDFs (also Word, PowerPoint and images) into markdown, LaTeX, HTML or JSON with figures, through the Datalab marker API, at a chosen level of detail and cost, using a bundled CLI (pdfc.py) with spend guards. Use whenever you need to read, quote, summarize or extract tables, equations or figures from a PDF, turn a paper into markdown or LaTeX, or prepare documents for search or RAG. Prefer it over local text extraction when layout, tables, math or figures matter. Includes key setup and spend checks.
---

# PDF conversion with Datalab marker

`pdfc.py` (next to this file) sends one document to the Datalab convert API, waits for the
result, and writes markdown (or LaTeX, HTML, JSON) plus the extracted figures into a folder.
Each conversion costs real money, so the CLI makes the cheap path the default and stops
before an expensive one. Below, `<skill-dir>` is the directory holding this SKILL.md.

```bash
uv run <skill-dir>/pdfc.py <command> ...   # preferred: uv adds pypdf and keyring
python3 <skill-dir>/pdfc.py <command> ...  # standard library only; no page counts or OS keyring
```

Run `doctor` first in a new environment. It checks the key, tools and spend without
converting anything.

## First use: the API key

If `doctor` reports no key, the **user** sets one up. Don't ask for the key in chat: anything
pasted into a conversation is sent to the model provider and can end up in logs. Tell the user
to run this in their own terminal:

```bash
uv run <skill-dir>/pdfc.py setup
```

It explains the steps, reads the key without echoing it, verifies it with Datalab, and stores
it in the OS keyring (macOS Keychain, Windows Credential Manager, Linux Secret Service) or,
where there is none, in a mode-600 file in the config directory. `$DATALAB_API_KEY`
overrides the stored key. `setup --remove` deletes it.

Setup also asks the user to give the key a **30-day spend cap** in the Datalab dashboard. That
cap is the only hard limit: past it the API answers HTTP 402 no matter what the caller does.
The local guards below are softer and catch mistakes before they cost anything.

## Choosing the level

Pick the cheapest level that answers the question, and convert only the pages you need.

| preset | what you get | list price per 100 pages | use for |
|---|---|---|---|
| `text` | text, headings, lists, simple tables; no images | ~$0.05 | skimming, searching, quoting prose, deciding whether a paper matters |
| `standard` (default) | layout-aware markdown, tables, LaTeX math, figures as image files | ~$0.40 | reading a paper properly; most work |
| `full` | most accurate mode, chart reading, tables and paragraphs merged across pages | ~$1.30 + a few cents per document | data-heavy tables, equations you'll reuse, figures you need described |

Prices are Datalab's list prices as of 2026-11; the CLI prints an estimate before each call
and the cost the API reports after it.

- **`text` reads only the PDF's own text layer.** A scanned PDF (old papers often are) comes
  out empty or garbled, and math comes out escaped (`\$\$ \mathrm { N a } \_ 2`). For those,
  use `standard`, or `--preset text --mode fast` for OCR without figures.
- **`standard` may render equations as images** when the source draws them, especially in
  scans. If an equation matters, look at the image or use `full`.
- **Chart text is a reading, not data.** With `full`, `chart_understanding` writes synthetic
  descriptions of figures, sometimes with tables of numbers read off a plot. They are fenced
  in `<!-- BEGIN IMAGE CAPTION -->` / `<!-- END IMAGE CAPTION -->`. Treat them as a reading:
  view the image file before relying on a value, and never quote one as the paper's data.
- **Override one setting** instead of jumping a level: `--mode lite|fast|balanced|accurate`,
  `--images`/`--no-images`, `--extras chart_understanding`, `--merge-cross-page`.

## Converting

```bash
pdfc.py convert paper.pdf --dry-run                 # page count, plan and cost; no call
pdfc.py convert paper.pdf -o literature/smith1987   # standard preset, markdown
pdfc.py convert paper.pdf --preset text -o /tmp/x   # cheapest
pdfc.py convert paper.pdf --pages 0-3,10            # part of it (0-based: page 1 is 0)
pdfc.py convert paper.pdf --format md,latex         # also a standalone .tex via pandoc
pdfc.py convert paper.pdf --format md,json          # JSON block tree with bounding boxes
```

One file per call. Output goes to `-o DIR` (default `./<file stem>/`):

- `<stem>.md`: page separators `{N}------` mark the start of each page, with **N 0-based**.
- the figure images (`*.jpg`) next to it, linked from the markdown by file name.
- `<stem>.tex` / `.html` / `.json` / `.chunks.json` as requested.
- `<stem>.meta.json`: source path, hash, request settings, request id, pages, cost.

Put throwaway conversions in a temporary directory (the session scratchpad, if your harness
gives one). Put conversions the project will keep in a project folder such as `literature/`.

**Formats.** `md` is the default and the cheapest to read. `latex` converts that same markdown
with pandoc. Pandoc must be installed, and the conversion costs nothing extra: with the cache,
adding `--format latex` later is free. Compile the `.tex` with `lualatex` or `xelatex`
because of the Unicode. `json` and `chunks` are for programs (block types, bounding boxes,
RAG chunks). They are large, so don't read them whole.

**Reading the result.** For a long document, list the headings (`grep -n '^#' file.md`) and
read the sections you need rather than the whole file. Look at figures by opening the image
files. The markdown only says where they are.

## Guards and what to do when one fires

| exit | meaning | what to do |
|---|---|---|
| 0 | done (or `--dry-run` printed the plan) | |
| 1 | error (bad file, bad key, API error, conversion failed) | read the message; fix and retry only if the cause is clear |
| 3 | still processing when `--wait` ran out | `pdfc.py fetch REQUEST_ID` later; **never convert again**, that pays twice |
| 4 | refused by a local guard | stop and ask the user (below) |

- **Page limit** (default 60 pages per call). A longer document is refused. Convert the part
  you need with `--pages`, or, after the user agrees to the cost, pass `--max-pages N` for
  that call.
- **30-day budget** (default $5, counted from a local ledger). It's a setting, not a flag,
  so you can't override it per call. Only change it with `pdfc.py config budget_usd_30d N`
  when the user asks.
- **HTTP 402** means the key reached its Datalab spend cap. Tell the user. Don't look for
  another key or another route.
- **Cache.** The same file with the same settings is served from the local cache for free.
  `--refresh` pays again. Use it only when a cached result was bad.
- **Uploads are never retried** once the server might have accepted them. If an upload fails
  midway, the message says so. Check the Datalab dashboard before converting the file again.

`pdfc.py usage` lists the last 30 days of conversions and their cost. `pdfc.py config`
shows the settings and where config, ledger and cache live: XDG directories on Linux and
macOS, AppData on Windows.
