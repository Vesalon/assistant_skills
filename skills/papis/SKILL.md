---
name: papis
description: Search, read, add, and export papers from the user's papis bibliography libraries. Use when the user mentions papis, their paper/reference library, wants to look up or add a paper, cite something, find a DOI, check what's in their bibliography, or sync references into a .bib file for a manuscript.
---

# Papis

Papis is the user's local bibliography manager. This skill was written against papis 0.15.
Libraries are plain directories of per-document folders, each holding an `info.yaml` plus
attached PDFs. `papis list --libraries` prints each library's name and directory.

## Rule zero: always pass `--all`

Papis opens an **interactive picker** whenever a command could match more than one document.
In a non-TTY context (i.e. every command you run) that picker fails and the command returns
**nothing, with exit code 0** — a silent empty result that looks like "no such paper" but isn't.

Always pass `-a`/`--all` on read commands, and `-b`/`--batch` on `add`.

```bash
papis -l LIB list --all                      # correct
papis -l LIB list                            # returns nothing, exits 0. Never do this.
```

If a papis command returns empty, suspect a missing `--all` before concluding the library is empty.

## Rule one: reset the cache after editing `info.yaml` by hand

Papis keeps a pickled index under `~/.cache/papis/database/`. Writing to an `info.yaml`
directly does **not** invalidate it, and stale-cache failures are silent:

- `papis list` keeps reporting the old field values;
- worse, `papis add` de-duplicates against the *cached* copy, so an add can match a document
  that no longer exists in that form, create nothing, and still print
  `[INFO] commands.add: Created reference '...'`.

```bash
papis -l LIB cache reset      # clear + rebuild; run after every hand edit
papis -l LIB cache update     # cheaper: reload info.yaml files from disk
```

Prefer `papis update --set key value`, which maintains the cache. Hand-edit YAML only for what
`--set` cannot express, such as the nested `author_list` entries — then reset.

## Selecting a library

`-l/--lib` goes **before** the subcommand. Without it you get `default-library` from
`~/.config/papis/config`.

```bash
papis -l LIB list --all
papis list --libraries          # what libraries exist
cat ~/.config/papis/config      # library dirs, ref-format, per-library overrides
```

Prefer naming the library explicitly rather than relying on the default — the right library
depends on the project (see "Project configuration" below).

## How refs are generated — and why they collide

A document's BibTeX key is its `ref` field. On `add`, papis builds one with
`papis.bibtex.create_reference`: it applies the `ref-format` pattern from the config, then
slugifies (unicode stripped, disallowed characters to `_`). Read the pattern before predicting
anything — `grep ref-format ~/.config/papis/config`. A common one is
`{doc[author]:.10} {doc[year]}`: the first 10 characters of the raw `author` string, then the
year. Truncation lands mid-name, so keys like `Xu_Min_an_2018` are normal, not corruption.

To predict a key before adding:

```bash
python3 -c "
import papis.config, papis.document, papis.bibtex
papis.config.set_lib_from_name('LIB')
d = papis.document.from_data({'author': 'Provencher, Stephen W.', 'year': '1982'})
print(papis.bibtex.create_reference(d, force=True))"
```

**There is no collision handling.** `create_reference` is a pure function of one document — it
never sees the rest of the library — and `add` writes the result blindly. Two papers by the
same first author in the same year silently receive the same `ref`, i.e. a duplicate BibTeX
key. `papis doctor --checks duplicated-keys` reports this but registers **no auto-fixer**,
unlike `duplicated-values`.

Fixing it by hand sticks, because `create_reference` returns an existing `ref` untouched
(`if not force and ref: return ref`). Suffix letters are the usual convention, ordered by
something stable such as page range:

```bash
papis -l LIB update -a -b --doc-folder <library-dir>/<doc-folder> --set ref Author_1982a
papis -l LIB cache reset
```

## Reading

```bash
# refs only
papis -l LIB list --all --format '{doc[ref]}'

# a scannable table
papis -l LIB list --all --format '{doc[ref]} | {doc[year]} | {doc[title]:.70}'

# folders, attached PDFs, notes, full info.yaml
papis -l LIB list --all --dir
papis -l LIB list --all --file
papis -l LIB list --all --notes
papis -l LIB list --all --info

papis -l LIB list --all --sort year --reverse
```

`{doc[field]}` reads any key in `info.yaml`; `:.N` truncates to N chars. Common fields:
`ref, title, author, year, doi, journal, volume, issue, pages, url, abstract, files, tags`.

Reading `info.yaml` directly is often easier than fighting format strings for bulk work:

```bash
find <library-dir> -name info.yaml | head    # <library-dir> from `papis list --libraries`
```

## Querying

Query strings go after the subcommand. `field:value` matches a field; a bare word is free text.

```bash
papis -l LIB list --all 'author:hopfield' --format '{doc[ref]}'
papis -l LIB list --all 'year:2015'
papis -l LIB list --all 'tags:review'
papis -l LIB list --all 'multiangle'
```

Free-text search covers indexed metadata (title, author), **not** PDF full text and not
reliably the abstract. A term that clearly appears in a paper's abstract may still not match —
for content searches, grep the `info.yaml` files or the PDFs instead.

## Adding

Always `--batch`, or it will block on a prompt.

```bash
papis -l LIB add --batch --from doi 10.1039/c4sm01995d
papis -l LIB add --batch --from arxiv 2301.12345
papis -l LIB add --batch --from isbn 9780471293408
papis -l LIB add --batch --from bibtex file.bib
papis -l LIB add --batch --from crossref 'query terms'

# attach a local PDF, and set fields at add time
papis -l LIB add --batch paper.pdf --from doi 10.xxxx/yyy
papis -l LIB add --batch --set tags 'inverse-problems,mcmc' --from doi 10.xxxx/yyy
```

Importers: `arxiv, bibtex, crossref, dblp, doi, folder, isbn` (`papis add --list-importers`).

Adding writes to the user's library on disk. Confirm with the user before adding, removing, or
editing documents in bulk — a bad batch import is tedious to unpick.

**Verify a DOI resolves to the work you mean, not merely to the right title.** A DOI can carry
the exact title, journal, volume and pages you expected and still credit a different author —
a misattribution in a hand-written bib stays invisible until someone looks. Check the authors:

```bash
curl -s "https://api.crossref.org/works/<DOI>" | python3 -c "
import json,sys; d=json.load(sys.stdin)['message']
print(d.get('title'), [(a.get('given'), a.get('family')) for a in d.get('author', [])])"
```

### Documents with no DOI

Conference papers, theses, standards, vendor white papers and older books often have no DOI and
no Crossref record. Build the entry from an attached file plus explicit `--set` fields, and
attach the actual backing document — a PDF where one exists, otherwise the source page saved to
disk — so the claim can be checked later:

```bash
papis -l LIB add --batch whitepaper.pdf \
  --set author "Goldin, Alexander A." --set title "..." \
  --set year 2002 --set type misc --set url "https://..."
```

Before concluding a document is unobtainable, try beyond Crossref: HAL
(`https://api.archives-ouvertes.fr/search/?q=...&fl=fileMain_s,title_s&wt=json`) for French
theses and preprints, `theses.fr/api/v1/theses/recherche/?q=<NNT>`, `papers.nips.cc` for NeurIPS,
Open Library (`https://openlibrary.org/isbn/<ISBN>.json`) for books, and the publisher's own
file URL — a journal's volume index may omit a year that its file server still serves.

When `add` is given a local file *and* explicit `--set` fields, papis first runs its importers
against the file **path** and logs alarming failures before falling through to your values:

```
[ERROR] importer.bibtex: Error reading BibTeX file or string: '.../paper.pdf'...
[ERROR] importer: Network error! Failed to fetch data from importer 'fallback'...
```

These are harmless. Confirm success by the `Created reference '...'` line, not by the absence of
errors.

## Exporting to BibTeX

```bash
papis -l LIB export --all --format bibtex                 # whole library to stdout
papis -l LIB export --all 'author:hopfield' --format bibtex
papis -l LIB export --all --format bibtex --out refs.bib
```

`--out` **prompts before overwriting** an existing file, which hangs in a non-TTY. Back the
target up and delete it first, then export.

**Review exported entries before committing them to a manuscript bib.** Metadata harvested from
Crossref/DOI is frequently malformed in ways that break or corrupt a bibliography:

- `year` can carry a full date (`year = {2004 March 11}`) where BibTeX wants a bare year
- author lists can arrive `;`-separated instead of BibTeX's required ` and ` separator
- some publishers deposit names in ALL CAPS (`GREEN, PETER J.`), which prints verbatim
- edited volumes often deposit **no author at all**; with an author-based `ref-format` the key
  then degenerates to a bare year (`ref: 1993`). Set the editor and a real `ref`.
- a book DOI frequently resolves to a later reissue, so `year` is the reprint's, not the
  edition being cited
- publisher titles can carry raw JATS/HTML (`<i>...</i>`, `<jats:p>`). Harmless inside
  `abstract`, but in a `title` it renders literally in the bibliography.
- publisher-supplied titles sometimes embed the journal name
- unicode and math in titles may need brace-protection for correct capitalization

Two export behaviours worth knowing:

- **`author_list` overrides `author`.** Correcting a malformed `author` string alone changes
  nothing in the output — fix both, or the old name still ships.
- **`note` is a real BibTeX field and most styles print it** in the reference list. Never park
  provenance, caveats or working notes there. `annote` is not declared by common styles, so it
  survives into the `.bib` and stays out of print. Confirm against the style being used:

```bash
sed -n '/^ENTRY/,/^}/p' "$(kpsewhich aipnum4-2.bst)"   # fields the style actually reads
```

Never blind-append an export into a live `.bib` — diff it first, and check for entries that
duplicate something already cited under a different key.

## Notes and files

```bash
papis -l LIB list --all --notes          # note file paths (notes-name in config)
papis -l LIB list --all --file           # attached PDF paths
```

Read notes/PDF paths and open them with `Read`; don't use `papis open`/`papis edit`, which
need a TTY and will hang or fail.

## Health check

```bash
papis -l LIB doctor --all                          # every default check
papis -l LIB doctor --all --checks duplicated-keys # one check (note: --checks, not --check)
papis list --doctors                               # available checks
```

Run it before every export, and after any hand edit plus `cache reset`. Note that
`duplicated-keys` compares within the queried set, so it only catches ref collisions under
`--all`.

The strongest check is a real compile: export to a scratch directory, build the manuscript
there, and confirm the log reports zero undefined citations before touching the live `.bib`.
LaTeX needs `pdflatex` → `bibtex` → `pdflatex` ×2; a stale log from an earlier pass will
happily show undefined citations that a further pass resolves, so read the log only after the
full cycle.

## Project configuration

Which library a project uses, where its manuscript `.bib` lives, and its citation-key
conventions are **project-specific** and are not recorded in this skill. Before doing papis work
in a repo, check for those notes in this order:

1. Your memory directory for the project (a `papis-*` entry)
2. `CLAUDE.md` in the repo, or a `PAPIS.md` next to it
3. Otherwise: infer from `papis list --libraries` plus any `.bib` in the repo, then **ask the
   user to confirm** which library is correct before writing anything

When you learn a durable project fact — the library name, the bib path, a key convention, a
known duplicate — record it in the project notes, not in this file. Keep this skill general.
