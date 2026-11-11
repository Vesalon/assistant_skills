# AGENTS.md

This repo holds portable agent skills (`skills/<name>/SKILL.md` plus scripts). Read
`README.md` for what each skill does.

## If the user asks you to set up or install these skills

1. Find out which directory their harness loads skills from. If you know your own harness's
   skills directory, propose it. Otherwise ask. `~/.agents/skills` is the default and is
   read by several harnesses.
2. Run `./install.sh --check` and report the result.
3. Run `./install.sh [--skill NAME ...] DIR`. Symlinks are the default. Use `--copy` only
   if the harness doesn't follow symlinks. If a skill is reported as already present, show
   the user what is there and ask before re-running with `--force`. Never delete it yourself.
4. Help with the missing prerequisites the check reports. For the OpenAlex API key, the
   user creates the account and pastes the key; write it to `~/.config/openalex/api_key`
   with mode 600, and never echo it back or put it in a command that gets logged. Papis
   library configuration is the user's choice of directories: ask, don't invent.
5. If the harness has no native skill support, run `./install.sh --index` and offer to add
   its output to the user's global agent instruction file.
6. Tell the user to start a new agent session. Most harnesses scan skills only at startup.

## If you are editing a skill

- `SKILL.md` must start with YAML frontmatter holding `name` (equal to the folder name) and
  `description`. The description decides when an agent loads the skill, so say both what
  the skill does and when to use it.
- Keep skills vendor-neutral and machine-neutral. Don't use harness-specific tool names,
  absolute paths, usernames, or install locations. Refer to bundled files relative to the
  skill's own directory (`<skill-dir>/oa.py`), because the skill may be installed anywhere.
- Don't commit secrets, API keys, or personal library contents.
- Scripts should run with `python3` alone where possible. Declare extra dependencies inline
  (PEP 723 `# /// script` block) so `uv run` can supply them, as `oa.py` does.
- Before finishing, check that the script still runs. For openalex, `work` costs no credits:
  `python3 skills/openalex/oa.py work 10.1126/sciadv.abk0644`
- When adding a skill, add a row to the table in `README.md` and a prerequisite check for
  it in `install.sh` (`check()`), if it needs any software.
