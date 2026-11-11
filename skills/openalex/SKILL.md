---
name: openalex
description: Literature search and citation-graph exploration through the OpenAlex API, with a bundled CLI (oa.py). Use whenever the user wants to find papers on a topic, run a literature search or review, snowball from a paper's references or citers, look up a paper by DOI or title, list or disambiguate a researcher's publications, profile what a group of people works on (a PhD committee, a lab, reviewers, collaborators), or map how a paper or field connects to specific researchers. Also use for bibliometric questions (citation counts, who cites what, publication trends) and whenever OpenAlex is mentioned. For the user's own saved library and BibTeX, use the papis skill; hand it DOIs found here.
---

# OpenAlex literature search

OpenAlex is a free, open index of about 250M scholarly works, with authors, institutions,
topics, and the full citation graph. `oa.py` (next to this file) wraps the parts that matter
for literature work. Every fetched work is saved in one normalized JSONL schema with short
ids (`W...`, `A...`), so saved files grep and join cleanly.

The toolkit and the connection-mapping procedure were built for a PhD qualifying exam
(2026), to show how the exam paper related to the three committee members. The examples
below use that case because the numbers are verified.

## Running it

`oa.py` sits in this skill's directory, next to this SKILL.md. Call it by that absolute
path from any working directory. Below, `<skill-dir>` stands for that path.

```bash
uv run <skill-dir>/oa.py <command> ...    # uv supplies duckdb, which only `sql` needs
python3 <skill-dir>/oa.py <command> ...   # standard library only; everything except `sql`
```

Don't store the command in a shell variable such as `$OA`: zsh does not word-split
variables. Write it out, or define `oa(){ uv run -q <skill-dir>/oa.py "$@"; }` inside the
same shell call.

Saved files land relative to the current directory. Use a temporary directory (the
session scratchpad, if the harness provides one) for throwaway exploration. Use a
directory inside the project (e.g. `literature/`) when the data should outlive the session.

**API key and budget.** The key is read from `$OPENALEX_API_KEY`, else
`~/.config/openalex/api_key`. Never print it. OpenAlex meters use in credits that reset
daily: **10,000/day with the key, 1,000 without.** Every command reports the credits it
used and how many are left today. Without a key every command still works and prints a
note saying so. If the budget runs short, tell the user that a key is free with an
OpenAlex account.

| call | credits |
|---|---|
| a single record (`work`, `get works/W...`, `get authors/A...`) | 0 |
| a list/filter page of up to 100 (`refs`, `cites`, `resolve`, `author-works`, `corpus`) | 1 per page |
| any search: `search`, `--semantic`, `author`, and `*.search` filters | 10 per page |

Typical totals: `connect` about 30, plus about 80 for `--deep` on a 450-work corpus;
`corpus --enrich` for three people about 25. Prefer filters over searches when either
would do.

## Commands

| command | does |
|---|---|
| `work ID_OR_DOI...` | Title, authors **with author ids**, venue, counts, topics, abstract. Free. `--json`, `--full`. |
| `search "query"` | Keyword search (relevance order). `--filter`, `--sort`, `--limit N`, `--all`, `--save F`. |
| `search "plain-language description" --semantic` | Embedding search, up to 50 results. Finds papers that use different vocabulary. |
| `search --filter "..."` | Filter-only listing (1 credit/page), e.g. `cites:W...,type:review`. |
| `refs ID` | A work's references, resolved and sorted by citations. `--save`. |
| `cites ID` | Works citing it. Default sort is `cited_by_count:desc`; use `--sort publication_date:desc` for the frontier. `--limit`, `--all`, `--save`. |
| `resolve ID... [--from FILE]` | Metadata for a list of W ids, 100 per credit. |
| `author "Name"` | Candidate profiles: ORCID, affiliation history, topics, h-index. Flags split profiles that share an ORCID. |
| `author-works A...` | Every work of one person (pass several ids for a split profile). `--label`, `--save`. |
| `corpus DIR "Label=A1[,A2]" ...` | Labeled works for a group into `DIR`, with drift and split-profile warnings. `--enrich` also resolves the notable references. |
| `enrich DIR` | Resolve references cited more than once, or by more than one group (`--all` for every reference). |
| `connect SEED DIR` | Map every citation path from a seed paper to the corpus (below). `--deep`, `--threshold`, `--top`, `--refresh`. |
| `sql DIR ["QUERY"]` | DuckDB over the corpus with `views.sql` loaded. With no query, lists the views and their row counts. |
| `get ENDPOINT key=value...` | Raw API call printing JSON, e.g. `get works filter=cites:W... group_by=publication_year`. |

Filter syntax, sort keys, entity types, and `group_by` are in
[references/api.md](references/api.md). Read it before composing `--filter` or `get` calls.

## Procedure A: find literature on a question

1. **Map with reviews first.** Run 2-3 keyword searches phrased the way authors title papers,
   narrowed with `--filter publication_year:>2019`. Add `review` to the query text. The
   `type:review` filter misses most reviews, which OpenAlex types as `article`.
2. **One semantic search** describing the idea in plain words. It surfaces work under other
   vocabularies. A PINN-defect question returned 1990s neural-network NDE papers that
   keyword search never showed.
3. **Snowball from the 2-5 most relevant hits.** `refs` gives the foundations. `cites` gives
   the influential follow-ups, and `cites --sort publication_date:desc` gives the current
   frontier. `--filter` narrows a `cites` listing: `search --filter "cites:W...,publication_year:>2023"`.
4. **Read before recommending.** `work` is free and prints the abstract and topics. Don't
   call a paper relevant from its title alone.
5. **Report** id, year, first author, title, venue, DOI, and one line on why it matters.
   Offer to add chosen papers to papis by DOI (papis skill).

Don't rank keyword hits with `--sort cited_by_count:desc`. It promotes highly cited
off-topic papers: a PINN query sorted that way returned a qualitative-interview methods
review in its top 3. Sort by relevance, then rank the relevant hits by citations yourself.

## Procedure B: profile a group of people

1. **Resolve each person to an author id.** The most reliable source is a paper you know
   they wrote: `work <DOI>` lists every author's id. Otherwise run `author "Full Name"` and
   choose by ORCID, affiliation history, and topics, not by name.
2. **Collect:** `corpus DIR "Shen=A5054124562" "Atlas=A5041159213" --enrich`. Read the
   warnings: a profile with fewer than 5 works is probably a fragment, and an id sharing an
   ORCID with yours is probably the same person (add it as `Label=A1,A2`).
3. **Query** with `sql DIR` (lists the views), then for example:
   - `themes_by_label`, `keywords_by_label`, `recent_work`: what each person works on now.
   - `top_cited`: their own canon. `touchstones`: works they cite repeatedly.
   - `shared_topics`, `shared_references`, `coauthorship`: overlap between people.
   - `SELECT * FROM find('term')`: substring search over titles, abstracts, and keywords.
     Zero hits can be a finding: "physics-informed" appears nowhere in the quals committee's
     corpus.

## Procedure C: how a paper connects to a group

Build the corpus (Procedure B), then run `connect SEED DIR`. It caches what it fetches
under `DIR/seed_<W>/` and writes `report.json`, so reruns are free unless `--refresh`.
Read the sections in order:

1. **Direct citation** in either direction. Usually none. Say so; it frames everything else.
2. **Author level.** Seed authors as co-authors of corpus works, citations between their
   other work and the corpus, and name-only matches to verify. This is often the strongest
   link. The quals exam paper had no citation contact with the committee, but its author
   Suresh had co-authored 18 papers with committee member Shen, who cites him 263 times.
3. **One intermediary.** *Shared ancestor*: both cite W. *Common descendant*: a later work
   cites both. *Chains*: the corpus cites a seed citer, or the seed cites a corpus citer.
4. **Shared ancestors of the seed's citers.** These are works cited both by papers citing
   the seed and by the corpus. It is the route most likely to reach every member, because
   it compares the seed's whole downstream field with each person's foundations.
   - `n` = how many seed citers cite W. Global citations measure specificity: a 76-citation
     paper on both sides is close intellectual contact, while a 5,000-citation paper is a
     field-level foundation.
   - Works with 10,000 or more citations (`--threshold`) are set aside as
     **superconnectors**: generic canon such as DFT codes, SciPy, and AlphaFold. Scan the
     list anyway, because one can still matter. Hornik's universal-approximation paper
     (21k citations) is cited by 44 of the 391 seed citers and by Atlas.
5. **`--deep`** (two-hop common descendants) also fetches every work citing the corpus. Use
   it only when someone is still unreached. In the quals run it mostly re-surfaced the
   Shen-side bridges already found.

When reporting, name the direction ("both cite X": common foundations; "Y cites both": the
field joining them later). Give the specific bridging works for each person, not just
counts. Separate tight links from generic ones. Every id in the report greps in `DIR`.

## Data layout

```
DIR/works.jsonl             one row per (label, work); co-authored works appear under each label
DIR/reference_edges.csv     label, citing_id, referenced_id
DIR/referenced_works.jsonl  from enrich (an empty placeholder until then)
DIR/seed_<W>/               seed.json, refs.jsonl, citers.jsonl, author_<A>.jsonl, coupled.jsonl, report.json
DIR/corpus_citers.jsonl     from connect --deep
```

Work record fields: `id doi title year date type venue authors author_ids cited_by_count
referenced_works topics keywords abstract oa_pdf is_retracted`, plus `label` in a corpus.
Ad hoc DuckDB over any of them: `sql DIR "SELECT ... FROM read_json_auto('seed_W.../citers.jsonl')"`.

`corpus` overwrites `works.jsonl` and `reference_edges.csv` in `DIR`. Use a new directory
per group.

## Gotchas

All observed on real data.

- **Author ids drift.** OpenAlex re-clusters authors, and a stored id can shrink to a
  fragment. Shen's July 2026 id held his corpus; by October it held 1 work, and his 245
  works lived under a new id. The API does not redirect old ids. Re-resolve ids that come
  from old notes; `corpus` warns about tiny profiles.
- **Split profiles.** One person can have several ids. Suresh: `A5107993005` (459 works)
  and `A5101640166` (3 works) share an ORCID. `author` and `corpus` flag shared ORCIDs, but
  not every split shares one. Check `connect`'s name-only matches too.
- **Conflated profiles.** One id can merge namesakes. Enrui Zhang's profile included a
  chemist's solar-cell papers. Check topics and affiliations, and skim titles from
  `author-works`.
- **Namesakes.** A name match is not identity. A "Suresh" in Jackson's references was a
  different person. Treat name-only hits as leads to verify.
- **Duplicate records.** Preprint/published twins (W4327634123 and W4384525023 are one
  review) and plain duplicates (one Bader-charge paper has two ids). Dedupe by title before
  counting.
- **Metadata errors.** Book venues can be nonsense ("Theory of Dislocations" in "Medical
  Entomology and Zoology"). Abstracts are often absent. Check the DOI before citing.
- **Unresolvable references.** Some referenced ids are not indexed works (books,
  datasets), so `refs` and `enrich` can resolve fewer than listed. Rows with a NULL title
  in `shared_references` are those.
- **Numbers move daily.** Citation counts and citer lists grow; the quals paper went from
  368 to 391 citers in three months. Saved files are the snapshot, so give the retrieval
  date when quoting counts.
- **`works_count` on an author record** can exceed what the author filter returns (245 vs
  240). Small gaps are normal.
