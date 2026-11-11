# Critique

A figure is critiqued against its purpose, its readers, and the surrounding material available
for review. A standalone screenshot can support useful feedback without a full manuscript.

## Gather the context

Use what is available; request missing material only when it would change a recommendation:

- the render at final size, and a page or slide proof if one exists
- the purpose and job, from the request or project notes
- the caption and the text that discusses the figure
- the other figures in the set
- the decision log and the encoding table
- any reactions from readers

Distinguish visible findings from questions that require the data or methods. If the final
size is unknown, report apparent crowding or weak hierarchy provisionally; do not certify
font sizes, line weights, or export quality from a screenshot.

## 1. Cold read

If you have not yet read the caption or intended purpose, inspect the render first and
briefly describe its likely first reading.

- What draws the eye first, and what second?
- What looks grouped together (by color, shape, proximity, alignment, enclosure)?
- What looks ordered or ranked, and in which direction?
- What comparison does the layout invite?
- What would a reader conclude in five seconds?

Then read the purpose and compare. Look for unintended groupings, misplaced emphasis, or a
layout that works against the intended comparison or reader task.

If you built the figure or already know its purpose, your reading is informed; do not present
it as an independent reader test. When an important ambiguity remains, suggest a cold read
from someone in the intended audience using neutral questions: "What do you see? What goes
with what? What is the main point?". A reader's misreading is evidence to investigate, with
more weight than a simulated reaction.

## 2. Review in priority order

Do not polish what a structural fix may remove.

**Integrity: could the figure imply something that was not measured?**

- Axis ranges, truncation, broken axes; area or length out of proportion to value.
- Interpolated, smoothed, or fitted marks that look like observations.
- Normalization that hides differences in scale; separate scales on panels readers will
  compare.
- Zero, missing, below-detection, clipped, and off-scale values that look alike.
- A selected example presented as typical.
- Undefined uncertainty: what a band or error bar represents (spread, uncertainty of an
  estimate, or prediction), its level, and how it was computed. Do not infer these from
  appearance; check the caption or methods.
- An unclear observational unit or sample size: subjects versus repeated measurements,
  independent runs versus plotted points. Check whether aggregation or omitted observations
  hides variation relevant to the claim.
- Claims of causality, significance, or generality that the displayed evidence alone does
  not establish. Ask for the underlying analysis where needed; do not invent one.
- Color scales: a sequential quantity on a diverging map, a diverging map without a
  meaningful midpoint, a rainbow map that adds boundaries the data do not have.

**Constraints: does it survive its medium?**

- Legible at final size: smallest text, thinnest line, smallest marker, densest region.
- The project's recorded color requirements, if any.
- Essential distinctions recoverable through labels, shapes, or line styles when hue is
  unavailable; alt text or a text equivalent appropriate to the medium.
- Viewing distance, for slides and posters.

**Structure: does the figure serve its purpose?**

- A coherent claim or reader task, with each panel contributing evidence or explanation.
- The required comparison sits on a common scale, adjacent or overlaid.
- Encodings fit the data: position for the most important comparison; ordered channels
  (lightness, size) for ordered data; hue for categories; a diverging scheme only around a
  meaningful midpoint. See `lenses.md` (Bertin, Cleveland and McGill).
- Panel order follows the argument or process; dependencies are explained where needed.
- The figure and the text agree (the checks in `inventory.md`).
- Reference and context marks are findable.

**Polish:** alignment, spacing, tick density, label placement, consistency of fonts and
weights.

## 3. Report

Lead with the few findings that matter most. A short critique can use prose or bullets; for
an ongoing audit, use one finding per row:

| ID | Tier | Where | What a reader sees or does | Why it matters | Move | Done when |
|---|---|---|---|---|---|---|
| F3 | structure | (a) inset | compares bar heights between inset and main panel, but the inset's y axis is log | the effect looks ten times smaller than it is | match the main panel's scale, or label the inset axis "log scale" in the panel | a cold reader states the right ratio |

- "What a reader sees or does" describes the reader's experience, not a rule broken.
- "Done when" makes the finding checkable on the next render.
- Use stable IDs so the researcher can triage by number and later rounds can mark findings
  resolved.
- Reopen settled preferences only with new evidence or changed constraints. If a finding
  identifies an unresolved error or misleading representation, explain it even if the
  treatment was previously approved.
- Say what came back clean.

Record open findings when a notebook is maintained. Suggested moves come from `moves.md`.

## Critiquing a set of figures

Use this when reviewing a manuscript, thesis chapter, or talk as a set. After a shared role
changes, check the affected figures; a small local edit need not trigger a full audit.

**Build the encoding table** from every figure: each hue, lightness ramp, line style, marker,
fill, and texture, with what it means in each figure. Then look for:

- **One value, two meanings.** The same color is a treatment in one figure and a threshold in
  another.
- **One meaning, two encodings.** The control group is gray in one figure and dashed black in
  the next without a clear reason. Distinguish accidental drift from deliberate differences
  for a medium, task, or data role, such as points for observations and a line for predictions.
- **Unintended pairs.** Readers pair colors that look like a set: the two ends of a familiar
  diverging scheme, complementary hues, two shades of one hue. If such colors appear together
  with unrelated meanings, readers will link them anyway.
- **Hue budget.** Check how many hues readers must remember at once. As the set grows,
  prefer direct labels and stable roles; use lightness, texture, or line style where these
  clarify the distinction. A fixed palette size alone does not establish readability.

**Then check the structure of the set:**

- **Position contracts.** Categories (methods, conditions, sites) keep the same order and
  position across figures.
- **Scales.** Quantities compared across figures share scales, or the difference is flagged.
- **Furniture.** Reference lines, boundaries, panel letters, and annotation styles are
  consistent.
- **Dependencies.** A figure relies on a symbol, encoding, or construction readers cannot
  decode from the graphic, caption, or material available at that point.
- **Distinct purposes.** Two figures duplicate a task without helping the reader, or a
  comparison is spread over figures that would work better together.
- **Density.** One figure is much denser than its neighbors, often because it carries two
  messages.
