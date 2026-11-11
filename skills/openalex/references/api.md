# OpenAlex API cheat sheet

For `oa.py search --filter`, `oa.py get`, and anything the commands don't cover.
Base URL `https://api.openalex.org`. `oa.py get` adds the key and URL-encodes values, so
pass plain text with real spaces, not `%20`.

## Entities

`works`, `authors`, `sources` (journals and repositories), `institutions`, `topics`,
`keywords`, `funders`, `publishers`. Get one by id (free): `get works/W2137983211`,
`get works/doi:10.1126/sciadv.abk0644`, `get authors/A5041159213`,
`get authors/orcid:0000-0003-1542-2700`.

## Filters (`filter=` / `--filter`)

- Join with a comma for AND: `type:article,publication_year:2024`.
- `|` for OR, **up to 100 values**: `author.id:A1|A2`. More than 100 returns HTTP 400.
- `!` for NOT: `type:!article`. `>` and `<` for ranges: `cited_by_count:>500`,
  `publication_year:>2019`.

Useful work filters (all verified):

| filter | meaning |
|---|---|
| `cites:W...` | works citing W (forward) |
| `cited_by:W...` | works W cites (its references) |
| `author.id:A...` | works by an author |
| `authorships.institutions.id:I...` | works with an author at an institution |
| `primary_topic.id:T...`, `topics.id:T...` | topic membership (ids from `work` output or `get topics`) |
| `publication_year:2024`, `from_publication_date:2025-06-01`, `to_publication_date:...` | dates |
| `type:article` / `review` / `preprint` / `conference-paper` / `book-chapter` / `dataset` | work type (`review` misses most reviews) |
| `cited_by_count:>N` | citation threshold |
| `is_oa:true`, `has_doi:true`, `is_retracted:false` | flags |
| `title.search:...`, `abstract.search:...`, `title_and_abstract.search:...` | text match inside a filter (costs 10, like `search`) |
| `openalex_id:W1|W2|...` | batch lookup (what `resolve` uses) |
| `doi:10.x/y` | by DOI |

Author filters: `orcid:0000-...`, `last_known_institutions.id:I...`, `works_count:>20`.

## Other parameters

- `search=` keyword relevance search. `search.semantic=` embedding search (50 results max,
  no pagination).
- `sort=cited_by_count:desc`, `publication_date:desc`, `relevance_score:desc` (search only).
- `select=id,title,cited_by_count`: top-level fields only, which cuts payload.
- `per_page=` up to 100. `cursor=*` then `meta.next_cursor` to page through everything
  (`oa.py` does this).
- `group_by=publication_year` (or `type`, `primary_topic.id`, `authorships.institutions.id`, ...)
  returns counts instead of records. For trends:
  `get works filter=cites:W4213199992 group_by=publication_year`. For entity-valued
  groups the `key` is a URL; read `key_display_name`.

## Response notes

- Ids come back as full URLs (`https://openalex.org/W123`). `oa.py` shortens them; grep for
  the bare `W123` in raw files.
- `abstract_inverted_index` is `{word: [positions]}`. `oa.py` rebuilds the text.
- Rate-limit headers: `x-ratelimit-credits-used` (cost of this call) and
  `x-ratelimit-remaining` (credits left today).
