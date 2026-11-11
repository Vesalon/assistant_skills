# Options: show, don't describe

Use when comparing visible alternatives would resolve a perceptual or taste decision (color,
weight, line style, density, emphasis, proportions). A clear correction can be applied
directly; a small choice may need only two crops. Structural choices can be shown with rough
sketches instead of finished renders (`framing.md`).

## Build a swatch sheet

- **In context.** Vary the actual figure, or the panel where the decision matters, with real
  data. Abstract color chips do not show how colors behave at real mark sizes next to the
  figure's other colors.
- **At final size.** Render at the size the reader will see. For print, show a crop at 100%
  beside a thumbnail of the page proof. Judgments about weight and density made at screen
  zoom do not transfer.
- **Isolate the choice.** For a cosmetic decision, hold other properties fixed. For a
  structural comparison, coordinated changes may be necessary; explain each concept's
  tradeoff rather than treating the sheet as a controlled experiment.
- **Include the current version** as a labeled control.
- **Few variants:** usually two to six, enough to expose the useful differences.
- **Stable IDs.** Label each variant with a round letter and a number (b1, b2, ...) so the
  researcher can answer by ID and later notes can cite it. Under each, say in a few words how
  it differs.
- **Checks the project requires.** If the constraints call for grayscale or
  color-vision-deficiency safety, add a row showing each variant under that simulation.

Use whatever format the researcher can view at full resolution: one image or PDF with the
variants in a grid, or an HTML page if your environment can publish one. For subtle
differences, two adjacent crops at 1:1 work better than a grid.

## Run rounds

- Ask what the researcher notices, not only which they prefer. "The line in b3 disappears in
  the dense cluster" narrows the next round better than "b2".
- Recommend one variant and say why. The researcher may overrule you.
- Each round narrows: refine around the winner, or move to the next axis.
- For sustained work, record the alternatives that explain the decision and the researcher's
  reasons. "Too heavy next to the data" or "reads as another series" saves a future round.

## Freeze

When a sheet is retained as an approved reference, mark it frozen and list it in the notebook
or existing project record. Preserve that artifact; if the question reopens, build a new
sheet that starts from it. A one-off choice does not need a frozen sheet.

## Log the decision

For sustained work, log decisions likely to matter in later sessions:

```markdown
- 2025-03-02 | Fig 5 | Colormap for expression z-scores
  Trigger: a coauthor read dark cells as "high" on both sides of zero.
  Options: sheet d (d1 current sequential map; d2-d5 diverging variants).
  Chosen: d3, diverging, centered on zero, symmetric limits.
  Rejected: d2 (red-green; project requires CVD safety); d5 (dark midpoint made zero look
  like signal).
  Reopen if: the revised data need asymmetric limits.
```

The trigger matters as much as the choice. A decision made because a reader misread something
should not be undone by an argument from principle. "Reopen if" tells a later session what
evidence would justify revisiting it.

If the choice changes a shared role, check the figures that use it and update shared styles
and records where maintained (`production.md`, "Keep styles in one place"). Record deliberate
variants for different tasks or media. A local spacing choice needs only a local update.
