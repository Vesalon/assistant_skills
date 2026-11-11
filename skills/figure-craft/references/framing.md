# Frame: what the figure must do

Use before building a figure, when restructuring one, and whenever the text around a figure
changes.

## Questions to settle

Resolve the questions that affect the current task from the supplied material. State useful
assumptions and ask where a missing answer would change the design. Record the frame for
sustained work; a small revision can use the existing frame.

1. **Where does it live?** The medium (page, slide, poster, screen) and the slot (one
   column, full width, half a slide). Slot changes can require a new layout. Establish the
   target before polishing; for early concepts an explicit provisional size is enough.
2. **Who reads it, and what do they know by this point?** Identify what the reader brings
   and what the graphic or caption must introduce: symbols, conventions, transformations.
   A figure viewed independently cannot depend on an earlier paragraph alone.
3. **What is the purpose?** State a supported claim or a reader task in one sentence.
   "Method B reduces error across the tested range" frames a result. "Trace the sample from
   preparation to measurement" frames a methods schematic; "locate each sampling site"
   frames a reference map. A topic alone gives little guidance. Distinct claims or tasks
   suggest splitting only when their separation would help the reader.
4. **What must the reader compare or follow?** Name what is set against what, or the path,
   hierarchy, or lookup the figure enables. For quantitative comparisons, favor a common
   scale and adjacent or overlaid marks. For diagrams, make sequence and relationships clear.
5. **What is the figure's job in the argument?** It sets up a problem, delivers a result, or
   supports a claim made elsewhere, explains a method, or provides a reference. Schematics
   should make their abstraction clear; empirical claims need the observations or summaries
   that support them.
6. **What would a skeptical reader distrust?** Truncated axes, smoothing, a selected range,
   a normalization, a hand-picked example. Answer these in the construction of the figure,
   and explain consequential choices where readers need them. Label hypothetical or
   illustrative material so it cannot be mistaken for measured evidence.

## Brainstorm structurally different concepts

Generate two to four concepts that differ in how the comparison is structured, not in
styling. Common axes of difference:

- superimpose on one axis, juxtapose in aligned panels, or plot the difference directly
- every observation, a summary (mean, quantiles, fit), or both, layered
- one dense panel or small multiples
- a full field (map, heatmap), a few slices through it, or both with the slices marked on
  the field
- raw scale or transformed (log, ratio, normalized), introducing the transform where needed
- the result alone or next to its reference (baseline, null model, ground truth, prior work)
- for schematics: sequence, spatial arrangement, or hierarchy, according to the reader's task

Sketch each concept cheaply: a rough plot with real or placeholder data, or a text wireframe
of the panel grid. Keep sketches visibly rough so the conversation stays on structure.

```
+------------------------------+------------------------------+
| (a) response vs dose         | (b) difference B - A         |
|     A and B overlaid         |     same x axis as (a)       |
+------------------------------+------------------------------+
| (c) per-subject trajectories, one small multiple per dose   |
+-------------------------------------------------------------+
```

For each concept, describe the likely first reading and compare it with the purpose. For a
diagram, ask whether readers can find the starting point and follow the intended path.
Recommend one, and say what each of the others does better.

## When the researcher is torn

Write a short decision brief:

- **Question**, in one line.
- **Options**, two to four, each with what it gains and what it costs the reader.
- **What would decide it**: an argument (integrity, encoding semantics), a render (salience,
  density, color), or a reader (does anyone misread it?).
- **Recommendation**, with the reason.

Questions that only a render can settle go to `options.md`. For questions that only a reader
can settle, suggest whom to ask and what to ask them. Neutral questions work: "What do you
see first?", "What goes with what?", "What is the main point?". "Do you like it?" does not.

## Additions get a trial

When someone proposes adding a panel, overlay, inset, or annotation, state which inference or
reader task it helps.

- If it adds no useful evidence, explanation, or navigation, say so, and offer the sentence
  that could carry it instead.
- If it helps (it shows the spread behind a summary, provides a reference, or makes a
  process easier to follow), try it, render it, and judge it in place.

Removing an addition after its trial is a normal outcome, not wasted work.

## When the argument moves

Revisit the frame whenever the text around a figure is reorganized, the figure moves to a
different section, or a neighboring figure changes. Re-ask questions 2, 3, and 5.

Signs a figure may benefit from splitting: unrelated purposes; panels cited from different
sections; a caption that reads as two halves; a figure much denser than its neighbors.

Signs figures should merge: they reuse the same data or construction; the reader has to flip
between them to see the link the argument depends on; the text keeps comparing them.

Scope can go back and forth over the life of a document. Retain editable sources and inputs
for removed panels so a reversal costs little.
