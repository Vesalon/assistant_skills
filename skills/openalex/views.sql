-- DuckDB views over a corpus directory built by `oa.py corpus`.
-- Paths are relative to that directory (oa.py sql chdirs into it).
-- Nothing is persisted; the views re-read the flat files each session.

CREATE OR REPLACE VIEW works AS
SELECT * FROM read_json_auto('works.jsonl');

CREATE OR REPLACE VIEW reference_edges AS
SELECT * FROM read_csv('reference_edges.csv', header = true,
    columns = {'label': 'VARCHAR', 'citing_id': 'VARCHAR', 'referenced_id': 'VARCHAR'});

-- Readable metadata for the referenced works (from `oa.py enrich`). The schema is
-- fixed so the view still works while the file is an empty placeholder.
CREATE OR REPLACE VIEW referenced_works AS
SELECT * FROM read_json('referenced_works.jsonl', format = 'newline_delimited',
    columns = {id: 'VARCHAR', doi: 'VARCHAR', title: 'VARCHAR', year: 'BIGINT',
               venue: 'VARCHAR', authors: 'VARCHAR[]', cited_by_count: 'BIGINT'});

-- One row per (work, topic) / (work, keyword), for grouping and searching.
CREATE OR REPLACE VIEW work_topics AS
SELECT label, id, year, cited_by_count, UNNEST(topics) AS topic FROM works;

CREATE OR REPLACE VIEW work_keywords AS
SELECT label, id, year, cited_by_count, UNNEST(keywords) AS keyword FROM works;

-- What each group publishes under, and when.
CREATE OR REPLACE VIEW themes_by_label AS
SELECT label, topic, COUNT(*) AS n_papers, SUM(cited_by_count) AS total_citations,
       MIN(year) AS first_seen, MAX(year) AS last_seen
FROM work_topics
GROUP BY label, topic
ORDER BY label, n_papers DESC;

-- Favored vocabulary. OpenAlex keywords mix methods, materials and concepts.
CREATE OR REPLACE VIEW keywords_by_label AS
SELECT label, keyword, COUNT(*) AS n_papers, MAX(year) AS last_seen
FROM work_keywords
GROUP BY label, keyword
ORDER BY label, n_papers DESC;

-- Canon, sense 1: each group's own highest-impact work.
CREATE OR REPLACE VIEW top_cited AS
SELECT label, title, year, venue, cited_by_count, doi, id
FROM works
ORDER BY label, cited_by_count DESC;

-- Canon, sense 2: works a group cites again and again across its own papers.
CREATE OR REPLACE VIEW touchstones AS
SELECT r.label, r.referenced_id, rw.title, rw.authors, rw.year, rw.cited_by_count,
       COUNT(*) AS times_cited
FROM reference_edges r
LEFT JOIN referenced_works rw ON rw.id = r.referenced_id
GROUP BY ALL
HAVING COUNT(*) > 1
ORDER BY r.label, times_cited DESC;

-- Recent direction: the last 3 publication years, newest first.
CREATE OR REPLACE VIEW recent_work AS
SELECT label, title, date, year, venue, topics, cited_by_count
FROM works
WHERE year >= (SELECT MAX(year) FROM works) - 3
ORDER BY label, date DESC;

-- Overlap: topics shared by 2+ groups.
CREATE OR REPLACE VIEW shared_topics AS
SELECT topic, COUNT(DISTINCT label) AS n_labels, LIST(DISTINCT label) AS labels,
       SUM(n_papers) AS total_papers
FROM themes_by_label
GROUP BY topic
HAVING COUNT(DISTINCT label) > 1
ORDER BY n_labels DESC, total_papers DESC;

-- Overlap: works 2+ groups both cite (a shared canon).
CREATE OR REPLACE VIEW shared_references AS
SELECT r.referenced_id, rw.title, rw.authors, rw.year, rw.cited_by_count,
       COUNT(DISTINCT r.label) AS n_labels, LIST(DISTINCT r.label) AS labels,
       COUNT(*) AS total_citations
FROM reference_edges r
LEFT JOIN referenced_works rw ON rw.id = r.referenced_id
GROUP BY ALL
HAVING COUNT(DISTINCT r.label) > 1
ORDER BY n_labels DESC, total_citations DESC;

-- Overlap: works two groups wrote together (same id appears under both labels).
CREATE OR REPLACE VIEW coauthorship AS
SELECT DISTINCT w1.label AS label_a, w2.label AS label_b, w1.title, w1.year, w1.id
FROM works w1
JOIN works w2 ON w1.id = w2.id AND w1.label < w2.label;

-- Substring search over the corpus's titles, abstracts, and keywords.
-- Usage: SELECT * FROM find('finite element');
CREATE OR REPLACE MACRO find(term) AS TABLE
SELECT label, title, year, venue, cited_by_count, doi, id
FROM works
WHERE title ILIKE '%' || term || '%'
   OR abstract ILIKE '%' || term || '%'
   OR list_contains(keywords, term)
ORDER BY year DESC;
