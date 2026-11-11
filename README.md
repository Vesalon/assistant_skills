# assistant_skills

Research skills for AI coding agents, in the open
[Agent Skills](https://agentskills.io) format: one folder per skill, each with a `SKILL.md`
(YAML frontmatter `name` + `description`, then instructions) plus any scripts it uses.
Nothing here is tied to one vendor. Any harness that loads skill folders can use them
directly, and the rest can be pointed at them (see below).

| skill | what it does | needs |
|---|---|---|
| [openalex](skills/openalex/SKILL.md) | Literature search, citation snowballing, author disambiguation and citation-graph mapping through the [OpenAlex](https://openalex.org) API, with a bundled CLI (`oa.py`) and DuckDB views | Python ≥ 3.10; [uv](https://docs.astral.sh/uv/) for the `sql` command; optional free API key |
| [papis](skills/papis/SKILL.md) | Drive a local [papis](https://github.com/papis/papis) bibliography: search, add by DOI/arXiv/ISBN, export and audit BibTeX, while avoiding papis's silent non-TTY failure modes | papis (written against 0.15) with at least one library configured |
| [figure-craft](skills/figure-craft/SKILL.md) | Design and critique research plots and schematics, from quick feedback to whole figure sets; align figures with text, compare visual alternatives, and retain decisions across sessions | none for guidance; production tools depend on the project |

openalex finds papers; papis keeps the ones you want and produces the `.bib`; figure-craft
helps communicate research through figures. Each skill also works independently.

## Install

```bash
git clone <this repo> ~/repos/assistant_skills
cd ~/repos/assistant_skills
./install.sh                  # symlinks each skill into ~/.agents/skills, then checks prerequisites
```

`~/.agents/skills` is read by several harnesses. If yours reads a different directory, pass
that directory instead, or pass several:

```bash
./install.sh ~/.claude/skills                 # e.g. Claude Code
./install.sh ~/.agents/skills ~/.claude/skills
./install.sh --skill openalex DIR             # only some skills
./install.sh --copy DIR                       # copies, for harnesses that don't follow symlinks
./install.sh --check                          # just re-run the prerequisite check
./install.sh --uninstall DIR                  # remove the links this script made
```

The script never overwrites anything it didn't create. If a skill of the same name is already
in the target, it is skipped. `--force` moves it to `~/.local/state/assistant_skills/backups/`
first.

**Harness without skill support?** Run `./install.sh --index` and paste the output into the
agent's instruction file (`AGENTS.md`, a system prompt, or similar). It lists each skill's
trigger description and the path of its `SKILL.md`, which is all an agent needs to load a skill
on demand.

### Prerequisites

- **openalex:** `python3` ≥ 3.10. The CLI uses only the standard library, except `oa.py sql`,
  which needs duckdb. `uv run` installs duckdb automatically from the script's inline metadata.
  An API key raises the daily budget from 1,000 to 10,000 credits. Create a free account at
  openalex.org, then store the key where `oa.py` looks for it:

  ```bash
  mkdir -p ~/.config/openalex && (umask 077; printf %s 'YOUR_KEY' > ~/.config/openalex/api_key)
  # or: export OPENALEX_API_KEY=...
  ```

- **papis:** `uv tool install papis` (or `pipx install papis`), then configure a library in
  `~/.config/papis/config`. See the [papis docs](https://papis.readthedocs.io). Check it with
  `papis list --libraries`.

## Updating

With the default symlinks, `git pull` updates every harness at once. Copies (`--copy`) need
`./install.sh --copy --force DIR` again.

## Layout and conventions

```
skills/<name>/SKILL.md      required: frontmatter (name, description) + instructions
skills/<name>/*.py, *.sql   scripts the skill runs, addressed relative to the skill folder
skills/<name>/references/   longer material the skill loads only when needed
install.sh                  installer, prerequisite check, index generator
AGENTS.md                   instructions for an agent working in this repo
```

Skills stay general. Facts about one machine or project, such as which papis library a
manuscript uses or where its `.bib` lives, belong in that project's own agent notes, not in
the skill.
