# Inventory: every element, accounted for

The inventory is a table of everything visible in a figure: what it shows, how it is encoded,
what it is called, and where the reader learns what it means. It is written for the authors.
Working detail belongs here; information needed to interpret or assess the evidence belongs
in the published figure, caption, or methods as well.

## Build it

For a full audit, use one row per meaningful element or repeated class of elements, including
furniture (for example, one row for a shared tick convention). For a focused revision,
inventory only the changed or ambiguous elements; a simple figure may need only a short list.

| ID | Element | Shows | Encoding | Name or symbol | Explained in | Notes |
|---|---|---|---|---|---|---|
| a.1 | filled circles | annual mean per station | position: x latitude, y anomaly | "station means" | caption; Sec. 3.2 ¶2 | n = 41 |
| a.2 | dark line | smoothed trend through a.1 | position | "trend" | Sec. 3.2 ¶2 | smoothing span chosen for display |
| a.3 | light band | 95% bootstrap interval of a.2 | lightness fill | none | caption | 2000 resamples |
| a.4 | dashed horizontal | zero anomaly | line style | none | not needed | |
| b.cb | colorbar | anomaly scale for (b) | lightness ramp | "anomaly (K)" | axis label | symmetric limits |

Element kinds:

- data marks
- reference marks: baselines, thresholds, ground truth, model predictions
- labels and annotations
- furniture: axes, ticks, gridlines, panel letters, legends, colorbars

For every number the text reads off the figure ("the trend steepens by 12% north of 40°"),
note the calculation or source that produces it. Use computed or traceable source values for
precise claims, rather than estimating them from the render.

## Checks

- **Orphans.** Drawn but never explained in the figure, the caption, or the text. Explain it,
  or ask whether it needs to exist.
- **Ghosts.** The text or caption refers to something that is not visible, or is visible
  under another name.
- **Name drift.** One thing called different names in the figure, caption, and text
  ("control", "baseline", "untreated"). Pick one.
- **Order.** A panel relies on a symbol or construction introduced only later, with no
  explanation in the graphic or caption.
- **Unmet quantities.** A normalization, unit, or threshold is not defined where the
  intended reader can find it.
- **Unhelpful repetition.** Repetition that adds no decoding, interpretation, or independent
  readability. Keep repetition needed for self-contained captions or separate reading paths.
- **Display devices.** Smoothing for display, resampling, marker spacing, clipping. Record
  them here. Tell the reader only when they change what the figure means: clipping and
  off-scale values almost always do; resampling a continuous curve for display usually does
  not.

## Where each piece of information lives

Every fact about a figure has four possible homes.

- **The graphic:** the evidence, and the labels, legends, and scales needed to decode it.
- **The caption:** the purpose or main point, what each panel shows, and decoding the
  graphic cannot carry by itself. Define statistical marks, sample sizes, or other details
  needed for independent reading according to the venue's convention.
- **The text and methods:** interpretation, quantitative claims, transitions, and the
  procedures needed to assess or reproduce the evidence.
- **The inventory:** author-facing mappings, source locations, and production notes.

How much goes in the caption versus the text is a convention that varies by field and venue.
Some expect self-contained captions, some expect the text to carry the explanation. Settle it
once for the project, record it under Constraints when maintained, and apply it to the whole
set. Preserve what readers need at each point of use. The private inventory cannot substitute
for a public explanation of consequential processing or statistical choices.

## The walk-through test

For complex or ambiguous figures, write the tour a reader would need to understand the marks:
what each panel shows, what to compare or follow, and what the reader learns. A short spoken
walk-through can suffice for a simple figure. The document need not keep the tour.

Where the tour gets awkward, the figure usually has a problem:

- a mark you cannot explain in one clause
- a comparison that needs a sentence of setup before it makes sense
- a panel that only makes sense after a later one
- a feature you have to explain away because it comes from the plotting, not the data

Use the awkward passage to locate the problem: revise the figure, supply a missing
definition, or clarify the explanation as appropriate.
