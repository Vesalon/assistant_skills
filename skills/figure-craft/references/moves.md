# Moves

A catalog of design moves, each keyed to the symptom that calls for it. Use it to turn a
critique finding into a concrete change. Most moves have a cost, listed under "watch".

## Scope

| Move | Symptom | Watch |
|---|---|---|
| **Split** | Unrelated claims or tasks compete; panels are cited from different sections; the caption reads as two halves; the figure is much denser than its neighbors. | Related panels can serve one purpose. If the reader needs the link between the halves, keep a shared element, or merge back later. |
| **Merge** | Two figures reuse one data set or construction; the reader flips between them; the text keeps comparing them. | Density at final size. The merged figure still needs a coherent purpose. |
| **Demote** | A panel supports a side claim or a robustness check. Move it to the supplement or appendix. | The main text must not depend on it. |
| **Move to text** | A panel or annotation demonstrates an identity, a definition, or a parameter that one sentence can state. | Make sure the sentence exists before removing the panel. |
| **Remove** | An element adds no useful evidence, decoding, or navigation: a redundant title, frame, heavy gridline, or duplicated legend. | Preserve context needed for independent reading and for following a diagram. |

## Comparison

| Move | Symptom | Watch |
|---|---|---|
| **Common scale** | Panels meant to be compared have independent axes. | When ranges differ by orders of magnitude, use a log scale or plot ratios instead. |
| **Align** | Compared panels share a quantity but not an axis. Stack them to share x; place them side by side to share y. | Alignment beats symmetry of the grid. |
| **Superimpose** | Differences are small, on one scale, among a few series. | Overlap hides the lower series. Give it a contrasting mark (points under a line). |
| **Juxtapose** | An overlay is cluttered (more than about four series) or series cross repeatedly. Use small multiples with shared axes. | Keep panel geometry identical so the eye compares like with like. |
| **Plot the difference** | Two curves nearly coincide and the gap is the point. Readers judge the vertical distance between curves poorly. | Show the difference's scale explicitly, and keep the original nearby so readers know how big the gap is relative to the curves. |
| **Add the reference** | The result raises the question "compared to what?" Add the baseline, null model, prior result, ground truth, or noise level. | The reference should be visually neutral and clearly secondary. |
| **Show the data as observed** | A clean idealization hides what the claim must survive: scatter, noise, spread, outliers. Layer the raw observations under the summary. | This can change what the text is allowed to claim. Propagate. |
| **Clarify uncertainty** | A comparison depends on uncertain estimates, but uncertainty is absent or its marks are undefined. Use an appropriate interval or distribution and define it where readers can find it. | Confirm the quantity estimated, observational unit, and calculation from the data or analysis. Do not invent intervals or treat spread as uncertainty of an estimate. |
| **Show residuals** | Quality of fit matters. Add a residual panel under the fit, sharing x. | Use the residual scale the text discusses (raw, standardized). |
| **Reorder** | Categories sit in alphabetical or arbitrary order. Sort by value, or by the order of the argument. | A position kept constant across figures beats per-figure sorting. |
| **Change the aspect ratio** | Slopes or rates of change are the point. Bank the important line segments toward 45°. | The slot constrains the overall shape; adjust panel proportions within it. |
| **Transform** | Data span orders of magnitude, or ratios matter more than differences. | Label the transform and explain unfamiliar conventions. Check its domain, units, and treatment of zeros or negative values. |

## Encoding

| Move | Symptom | Watch |
|---|---|---|
| **Stabilize semantic roles** | A treatment, reference, or data role changes appearance across panels without explanation. | Observations and model predictions of the same quantity can use different marks. Preserve the meaning of each role, and explain deliberate variants. |
| **Redundant encoding** | A distinction the argument needs rests on hue alone. Add line style, marker shape, or a direct label. | Redundancy is for the distinctions that matter, not for every series. |
| **Swap hue for texture or lightness** | The hue budget is spent, or a hue implies a pairing or an order you do not mean. Hatching, stippling, or lightness steps carry categories without adding a hue. | Textures need enough area and line weight to survive final size. Labels placed over texture need a halo or a plain background. |
| **Ordered channel for ordered data** | Ordered categories (doses, years, sizes) are shown in unrelated hues. Use a lightness ramp of one hue. | Check that the steps stay distinguishable at mark size. |
| **Match the scheme to the data** | A signed quantity on a sequential map, or an unsigned one on a diverging map. | A diverging map needs a meaningful midpoint and, usually, symmetric limits. |
| **Direct labels** | A legend forces the eye back and forth. Label lines at their ends or beside distinctive features. | Labels must not collide with data at final size. |
| **Mark exceptional states with shape** | Clipped, off-scale, missing, or below-threshold values are told apart by color alone, or not at all. Use distinct markers (for example triangles at the axis edge for off-scale). | Explain the markers once, in the caption or a compact key. |

## Emphasis

| Move | Symptom | Watch |
|---|---|---|
| **Highlight one, gray the rest** | One series matters and the others are context. | The grayed series must still be readable if the text discusses them. |
| **Layer** | Data and context compete. Put context (gridlines, ranges, references) behind, lighter and thinner. | Do not fade context below findability. |
| **Promote context** | Readers miss a reference line, threshold, or boundary. Raise its weight or contrast, and give it the treatment it has in other figures. | Promoted context should still read as context, not as another data series. |
| **Annotate where the text points** | The text discusses a feature the reader has to hunt for. Mark it in place (label, arrow, bracket), in the words the text uses. | Use the fewest annotations that support the task. A process diagram may legitimately need many; a data panel should keep the evidence readable. |
| **Magnify** | The important feature lives in a small region. Add an inset or zoom panel, and mark its extent on the parent. | State the magnification or keep the axes labeled. |

## The boundary with the text

| Move | Symptom | Watch |
|---|---|---|
| **Move summaries out of the data region** | Metric boxes, percentages, or fit statistics obscure data or compete with the intended comparison. Move them to the caption, the text, or a compact key outside the plot area. | Retain numbers needed for the task; a comparison of metrics may itself be the figure's purpose. |
| **Rename to match the text** | The figure, caption, and text use different names for one thing. | Change all three at once, and the inventory. |
| **Move the figure or the text** | The reader lacks context needed to decode the figure at its current location. | A definition in the graphic or caption may suffice. Moving the figure can change its job; re-frame if needed. |
