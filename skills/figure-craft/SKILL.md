---
name: figure-craft
description: Design, revise, and critique research figures, from a single plot or schematic to a manuscript-wide figure set. Use for figures in papers, theses, talks, or posters; choosing layouts, visual encodings, or colormaps; aligning figures with captions and claims; and preparing final artwork. Supports quick feedback and sustained development with visual comparisons and decision records. Not for exploratory plots intended only for the researcher's own use.
---

# Figure craft

A research figure is rarely designed once. It gets framed, built, read, argued over, split,
merged, recolored, and rewritten as the argument around it changes. This skill is for working
alongside a researcher through that process: asking the questions that frame a figure,
sketching alternatives, accounting for every element, critiquing single figures and the whole
set, putting options side by side, and keeping the record that lets decisions stick.

The researcher decides. Your job is to make each decision easier to see and harder to forget,
while keeping the evidence accurately represented.

## Match the work to the request

Use only the modes and records that help with the current task.

- **Quick critique:** review the supplied render and give the few findings that matter most.
  A screenshot is enough to assess visible structure and readability. State what you cannot
  judge without data, a caption, or a known final size; do not require a notebook or manuscript.
- **Focused revision:** use the existing sources and project choices, address the requested
  issue, and check the affected captions and shared encodings. Offer alternatives only where
  they help decide the change. Flag wider problems without expanding the edit unasked.
- **Sustained development:** keep a figure notebook, inventories for complex figures, and a
  decision log. Review the whole set at milestones and when shared meanings change.

Infer the purpose and constraints from the supplied material where possible. Ask only for
missing information that changes the next decision. Feedback alone does not require file
changes. When revising a figure, update dependent material within the authorized scope and
identify any follow-up outside it.

## What drives figure revisions

The visualization literature (`references/lenses.md`) generates candidate improvements. The
revisions that matter most often come from outside the figure. Expect these and look for them.

1. **The argument moves.** When the text is reorganized, a figure's job changes and the
   figure has to follow. Splitting a figure that carries two messages and merging figures
   whose link the reader must see are normal milestones, sometimes in both directions over
   the life of one document. Keep removed material reproducible so a reversal is cheap.
2. **Writing exposes the figure.** Writing a walk-through that explains every mark finds
   what visual review misses: an undefined symbol, a mark nobody can explain in one clause,
   a feature produced by the plotting rather than the data, a broken link between panels.
   See `references/inventory.md`.
3. **Readers misread.** A reader groups two things the author never meant to pair, or cannot
   find a reference line. Investigate the misreading rather than defending what readers
   ought to see. A simulated cold read is only a hypothesis; test important ambiguities with
   the intended audience. See `references/critique.md`.
4. **Encodings accrete.** Each color, line style, or marker is added for a local reason.
   After enough additions two of them collide in a way no single figure shows. Check a new
   encoding against the shared roles; audit affected figures when a role changes meaning.
5. **Figure changes can change the text.** A new panel, a new transform, or more
   realistic data can invalidate a sentence, a quoted number, a caption, or alt text.
   Propagate each change before calling it done.
6. **Taste is settled by looking.** Color, weight, density, and emphasis cannot be argued
   to a conclusion. Show the options side by side at final size, in rounds, and keep the
   record. See `references/options.md`.

## The figure notebook

For sustained work, keep state in the project's existing figure notes or a figure notebook
such as `FIGURES.md`. Read relevant decisions before recommending changes. If a genuine cold
read is still possible, inspect the render before reading its intended message. If no record
exists, create one as part of ongoing figure development; a one-off critique needs none.

Default layout:

```markdown
# Figures

## Constraints
Medium, slot sizes, minimum text and line sizes, file formats, fonts, color requirements
(color-vision deficiency, grayscale printing), caption convention. Source and date for each.

## Encoding table
| Channel and value | Meaning | Used in |
|---|---|---|
One row for every color, lightness ramp, line style, marker, fill, or texture that carries
meaning anywhere in the set.

## Fig N: <short name>
- Purpose: <supported claim or reader task, in one sentence>
- Job: <what the reader knows before it; what it sets up or delivers>
- Status: framing | building | in review | settled
- Inventory: <table, or a link to it>
- Open findings: <from critique, by ID>
- Decisions: <dated log entries, see references/options.md>

## Frozen references
Swatch sheets and approved renders, by ID. Never edited after freezing.
```

Split it into several files when one becomes unwieldy. The project's choices live in the
notebook, never in this skill: they are one author's decisions for one body of work.

## Modes

| The researcher wants to | Mode | Read |
|---|---|---|
| decide what a figure should show, or brainstorm layouts | Frame | `references/framing.md` |
| pin down what every element means and where the text explains it | Inventory | `references/inventory.md` |
| get feedback on one figure or on a set | Critique | `references/critique.md` |
| choose among colors, weights, layouts, or encodings | Options | `references/options.md` |
| fix a specific problem ("this panel is cluttered") | Moves | `references/moves.md` |
| ground a judgment in the literature | Lenses | `references/lenses.md` |
| make a figure final for its medium | Production | `references/production.md` |

Read only the references needed for the task. Modes can chain: a critique suggests moves;
an unresolved visual choice benefits from options; a settled choice updates affected text
and, when maintained, the inventory, encoding table, and decision log. A clear fix can be
recommended or applied directly without a comparison sheet.

When you write plotting code yourself, frame first, build at final size
(`references/production.md`), and critique your own render before showing it.

## Working rules

- **Look at the render, not the code.** Inspect the rendered image, at final size when known.
  If you cannot view images, distinguish a source review from visual verification and tell
  the researcher what remains to check. Do not claim a screenshot proves export quality.
- **Respect the decision log.** Reopen settled preferences when evidence or constraints
  change, citing the reason. Keep unresolved correctness issues distinct from preferences.
- **Distinguish preference from correctness.** Honor settled aesthetic and workflow choices.
  A logged preference does not resolve an incorrect label, misleading representation, or
  unsupported inference. Raise those with specific evidence and a concrete correction.
- **Recommend.** When you lay out options, say which you would pick and why. Leave a choice
  open only when it is a matter of taste, and then show it rather than describe it.
- **Change, then propagate.** After a figure changes, check its caption, the sentences that
  describe it, quoted numbers, alt text, and any maintained inventory or encoding table.
- **Keep meanings consistent.** Check changes to shared roles in affected figures. Different
  marks can distinguish observations from models of the same quantity, and different media
  may need different treatments. Keep the relationship clear and record deliberate variants.
- **Frozen records stay frozen.** A settled swatch sheet or approved render is a record. New
  exploration gets a new sheet.

## Failure modes

- Adding a panel, overlay, or annotation without improving the reader's inference,
  understanding, or ability to navigate the figure.
- Overloading captions with irrelevant methods or defenses, or stripping out decoding and
  statistical details needed to read the figure independently. Follow the venue's convention.
- Using a normalization, symbol, or threshold without introducing it in the graphic, caption,
  or preceding text available to the intended reader.
- Disclosing display devices (smoothing for display, resampled markers, evenly spaced
  labels) as if they were findings. Keep production details in the source or inventory;
  explain choices that affect interpretation in the published material.
- Offering many cosmetic variants when the question is structural, or one structural
  concept when the question is cosmetic.
- Polishing a panel that a structural fix may remove.
- Fixing a local problem with a color that already means something elsewhere in the set.
- Fading context (gridlines, reference lines, thresholds) until readers cannot find it.
  Background elements should read clearly without drawing attention to themselves.

In any review the order is: integrity first (could the figure imply something that was not
measured?), then the medium's constraints, then structure and encoding, then polish.
