# Lenses

The visualization literature turned into review questions. Each lens is a way of looking that
generates candidate improvements. Judge them against the reader's task, the evidence, and
the author's recorded preferences. Preferences guide design choices; they do not resolve
errors in what the figure represents.

## Contents

- Tufte: integrity, economy, small multiples, layering
- Bertin: visual variables and what each can carry
- Cleveland and McGill: accuracy of perceptual tasks
- Gestalt grouping and preattentive features
- Munzner: expressiveness and effectiveness
- Doumont: one message, the reader's effort
- Color
- Reading list

## Tufte: integrity, economy, small multiples, layering

*The Visual Display of Quantitative Information* (1983; 2nd ed. 2001); *Envisioning
Information* (1990); *Visual Explanations* (1997); *Beautiful Evidence* (2006).

- **Graphical integrity.** The size of an effect as drawn should match its size in the data
  (Tufte's "lie factor" is their ratio). Ask: could the axis range, area encoding,
  normalization, or smoothing make an effect look larger or smaller than it is?
- **Compared to what?** Ask: does the figure show the reference the claim needs?
- **Data-ink and chartjunk.** Ink that shows no data needs a reason to exist. Ask: what
  happens if this element is removed? If nothing is lost, remove it.
- **Small multiples.** The same design repeated across a varying condition lets the eye
  compare. Ask: can the reader compare panels without mentally rescaling or realigning?
- **Layering and separation.** Visual weight should rank elements by importance. Ask: does
  the context sit behind the data? Do two elements interact to create a form nobody drew
  (the "1 + 1 = 3" effect, such as the bright channel between two close dark lines)?
- **Integrating text and graphics.** Labels belong on the data, not in a separate key, when
  the layout allows.

Counterweight: maximal economy is not always best. Bateman et al. (CHI 2010) found that chart
embellishments improved memorability without hurting comprehension. For papers, economy
usually wins. For talks and posters, memorability can matter more.

## Bertin: visual variables and what each can carry

*Sémiologie graphique* (1967); *Semiology of Graphics*, trans. W. J. Berg (1983).

Bertin's retinal variables differ in what they let a reader do:

| Variable | Selective | Associative | Ordered | Quantitative |
|---|---|---|---|---|
| Position | yes | yes | yes | yes |
| Size | yes | no | yes | yes |
| Value (lightness) | yes | no | yes | no |
| Texture (grain) | yes | yes | yes | no |
| Color (hue) | yes | yes | no | no |
| Orientation | yes, for points and lines | yes | no | no |
| Shape | no | yes | no | no |

- **Selective:** the reader can isolate every mark of one category at a glance.
- **Associative:** marks that differ only in this variable still group together. Size and
  value are dissociative: they dominate, and break grouping by other variables.
- **Ordered:** the variable is perceived as an order without a legend.
- **Quantitative:** ratios can be read from it.

Ask:

- Does each data attribute use a variable that can carry its type? Is an ordered quantity
  shown in hue, which carries no order? Is a category shown in lightness, which implies an
  order that does not exist?
- Can the reader isolate the class the text discusses (selectivity)?
- Does a strong variable (size, lightness) break up a grouping the figure needs?
- When the hues are used up, can texture or lightness take a role?

Bertin also distinguishes levels of reading: a single value, a group, and the overall
pattern. Ask which level the message lives at, and design for that level first.

## Cleveland and McGill: accuracy of perceptual tasks

Cleveland and McGill, "Graphical Perception," *JASA* 79, 531–554 (1984). Cleveland, *The
Elements of Graphing Data* (1985; rev. 1994).

Readers judge these most accurately first:

1. position along a common scale
2. position along identical, nonaligned scales
3. length, direction, angle
4. area
5. volume, curvature
6. shading, color saturation

Ask:

- Is the most important comparison encoded as position on a common scale?
- Are compared panels aligned so the scales are effectively common?
- Does the reader have to judge the vertical distance between two curves? Readers do this
  poorly. Plot the difference directly.
- Are slopes the point? Banking line segments toward 45° makes them easier to judge
  (Cleveland, McGill and McGill, *JASA* 83, 289–300, 1988).

## Gestalt grouping and preattentive features

Ware, *Information Visualization: Perception for Design* (4th ed. 2020). B. Wong's "Points of
View" columns in *Nature Methods* (from 2010), including two on Gestalt principles. Healey and
Enns, *IEEE TVCG* 18, 1170–1188 (2012).

- **Gestalt grouping.** Readers group marks by proximity, similarity (color, shape, size),
  enclosure, connection, and continuity. Similarity works across panels and across figures:
  two marks that share a color are read as related wherever they appear.
- **Preattentive features.** A mark that differs in a single feature (hue, lightness, size,
  orientation, motion) pops out without search. A mark that differs only in a combination of
  features does not.

Ask:

- What will readers group that the author did not mean to group?
- Does the element the text points to pop out in a single feature?
- Are two highlighted elements competing for the same pop-out?

## Munzner: expressiveness and effectiveness

Munzner, *Visualization Analysis and Design* (2014); "A Nested Model for Visualization Design
and Validation," *IEEE TVCG* 15, 921–928 (2009). The two principles go back to Mackinlay, *ACM
Transactions on Graphics* 5, 110–141 (1986).

- **Expressiveness.** Encode all of the information in the data and only that. An encoding
  that implies order, magnitude, or grouping the data lack fails it.
- **Effectiveness.** Give the most important attributes the most effective channels. Channel
  rankings differ for magnitude (position first, then length, angle, area, lightness) and for
  identity (spatial region, then hue, then shape).
- **What, why, how.** What data, why the reader looks (which task), how it is encoded. A
  design is judged against the task, not in the abstract.

Ask: does any encoding claim more than the data contain? Which attribute is most important,
and does it have the best channel?

## Doumont: one message, the reader's effort

Doumont, *Trees, Maps, and Theorems: Effective Communication for Rational Minds* (2009). For
slides: Alley, *The Craft of Scientific Presentations* (2nd ed. 2013).

Doumont's three laws: adapt to your audience; maximize the signal-to-noise ratio; use
effective redundancy.

- A figure should answer one question, and its message should be statable as an assertion.
- The message goes in words (caption or slide headline); the figure is the evidence for it.
- Redundancy is effective when it helps the reader decode (a direct label that repeats the
  legend) and noise when it repeats what the reader already has.

Ask: can the message be stated in one sentence? Does every panel serve it? Does the order of
reading match the order of the argument?

For a schematic, atlas, or reference figure, apply the same focus to a reader task: following
a process, locating an item, or understanding a relationship. An asserted empirical finding
is not required for those purposes.

## Color

- **Kind of scheme.** Sequential for unsigned magnitudes, diverging for signed quantities
  around a meaningful midpoint, qualitative for categories. Harrower and Brewer, *The
  Cartographic Journal* 40, 27–37 (2003), and ColorBrewer.
- **Perceptual uniformity.** Equal steps in data should look like equal steps in color.
  Rainbow maps fail this and add false boundaries: Borland and Taylor, *IEEE CG&A* 27(2),
  14–17 (2007); Crameri, Shephard and Heron, *Nature Communications* 11, 5444 (2020), with
  their scientific colour maps. The viridis family is a common uniform default.
- **Lightness carries order, hue carries identity.** Check figures in grayscale: whatever
  order survives is carried by lightness.
- **Color-vision deficiency.** Check essential distinctions without relying on hue alone:
  use labels, shapes, or line styles where needed, and inspect relevant simulations when
  available. The Okabe–Ito palette is a useful qualitative starting point, not a guarantee
  that every use is distinguishable. Record audience and venue requirements under Constraints.
- **Context changes color.** The same color looks different against different neighbors
  (simultaneous contrast), and small marks look less saturated than large fills. Judge colors
  in the figure, at final size.
- **Colors form pairs.** Familiar schemes teach readers that certain colors are opposites or
  partners. Two colors from the ends of a well-known diverging scheme read as a pair wherever
  they appear.

## Reading list

- Wilke, *Fundamentals of Data Visualization* (2019): proportional ink, color by purpose.
- Rougier, Droettboom and Bourne, "Ten Simple Rules for Better Figures," *PLoS Comput. Biol.*
  10, e1003833 (2014).
- Healy, *Data Visualization: A Practical Introduction* (2018).
- Franconeri, Padilla, Shah, Zacks and Hullman, "The Science of Visual Data Communication:
  What Works," *Psychological Science in the Public Interest* 22, 110–161 (2021): a review of
  the experimental evidence behind many of these lenses.
