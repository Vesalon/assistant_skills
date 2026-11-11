# Production

This skill holds no default sizes, fonts, line weights, or resolutions. Those come from the
venue and the project. Keep them in the project's figure notes for sustained work.

## Establish the constraints

- Find the venue's current instructions: a journal's artwork guidelines, a conference
  template, a poster specification, a slide aspect ratio. Record each requirement with its
  source and the date you checked: slot widths, maximum height, minimum text size, minimum
  line weight, raster resolution, accepted formats, font embedding, color mode, transparency.
- Look for places where the template and the venue disagree. A document template's text
  width can differ from the publisher's artwork limit. Satisfy both when compatible; flag
  conflicting requirements rather than assuming one always takes precedence.
- Record the project's own choices next to them: fonts, color requirements, caption
  convention.

## Build at final size

Choose the slot (one column, full width, slide region) first, then build the figure at
exactly that size so it is placed at 100% scale. Sizes set in points are then the sizes
readers see, and legibility can be checked while building rather than at submission.

The asymmetry: a figure built small and enlarged looks chunky but stays legible. A figure
built large and shrunk loses its text and its thin lines. When a figure may appear in more
than one place, proof each intended size or make separate layouts when scaling alone fails.

## Proof at natural size

Review the figure where it will live: on a page proof beside body text at 100%; on a slide
viewed from the distance of the back of the room; on a poster at reading distance. Check the
smallest text, the thinnest line, the smallest marker, and the densest region.

## Keep styles in one place

For a figure set, define semantic roles (treatment, control, reference, signed error, and so
on) in a shared style module, configuration, or design-tool styles. Map roles to colors, line
styles, and fills there. Reuse the project's existing conventions; a single diagram need not
acquire a style framework.

Keep variants explicit when tasks or media need them: observations may use points while
predictions use lines, or a slide palette may need a print alternative. Check that the roles
remain recognizable and that a shared style change reaches the affected figures.

If the project has hard constraints, its own build can assert them (minimum text size, line
weight, canvas size) so that violations fail when the figure is made. That code belongs to
the project.

## Reproducibility

- Retain editable sources, relevant inputs, and the steps needed to regenerate the output.
  These may be plotting scripts, vector documents, or saved workflows in a scientific GUI.
- For data figures, keep transformations traceable to the source data. If assembly or
  annotation happens in a design tool, preserve that editable stage as well; exported files
  alone are insufficient. Keep data-bearing marks tied to their computed positions and values.
- For schematics, retain editable geometry, labels, and linked assets. Distinguish illustrative
  dimensions or relationships from measured ones where readers could confuse them.
- Precise numbers quoted in the text come from a traceable calculation or source value;
  record its location in the inventory or project notes when maintained.
- After a change, regenerate the affected output through the recorded workflow and check
  dependent text and records (`SKILL.md`, working rules).

## Toolchain checks

Use checks relevant to the actual output and available tools; these are optional examples,
not dependencies of the skill. A vector editor or export inspector may provide equivalent
checks. If a check cannot be performed, identify what remains unverified.

- Fonts embedded, and not as Type 3 (`pdffonts file.pdf`). Matplotlib's PDF backend writes
  Type 3 fonts unless `pdf.fonttype` is set to 42.
- The saved size equals the requested size. Matplotlib's `bbox_inches="tight"` crops to the
  ink and changes the saved size. Constrained layout keeps the canvas fixed.
- Dense artists (heatmaps, large scatters) can be rasterized inside an otherwise vector file
  while text and axes stay vector. `pdfimages -list file.pdf` reports the resolution of the
  raster parts.
- Some production formats (EPS among them) do not support transparency. If the venue
  requires one, avoid transparency or flatten it.
- Text inside a figure can be extracted (`pdftotext -layout file.pdf -`) to check spelling
  and naming against the text.
