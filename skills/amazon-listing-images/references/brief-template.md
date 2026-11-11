# Creative-pack brief

The brief a human fills before a creative pack is built. `R` marks a required field
and `O` an optional one. Copy the block, fill it, and attach or link the files it names.
The pack procedure that consumes it is `references/creative-pack.md`.

```text
CREATIVE-PACK BRIEF

Approver (R):                  name of the person who checks the pack
Brand (R):                     brand name as printed on the pack
Product (R):                   product name exactly as printed on the shipped pack,
                               with variant, size and count
ASIN (R):                      the ASIN, or "new"
Marketplace and copy language (R):  e.g. US, English
Label or spec file (R):        attached file or link; full size, every panel
Claims posture (R if regulated):    one of
                               - label facts only
                               - label facts + named structure/function lines:
                                 list each approved line exactly
                               - standard

Website URL (O):
Brand colours, fonts, logo file (O):   hex values, font names, logo as SVG or PNG
Style direction (O):           liked references, one reason each
                               disliked references, one reason each
Gallery size (O):              default one frame per buying job, up to MAIN + PT01 to PT06
Shopper evidence (O):          POE export, review notes, return reasons
Competitor ASINs (O):
Must say (O):
Never say (O):
Known decisions (O):           e.g. crisp label on every render; disclaimer on
                               every frame that shows the pack; type-size exceptions
Figma file for the later build (O):
Deadline (O):
```

## What makes a brief good

- **One buying job per image.** If you already know what a frame must answer
  ("how long does one bottle last", "will it fit my counter"), write it down. A list
  of jobs is more useful than a list of adjectives.
- **The product as shipped.** Write the name the way the pack prints it, not the
  internal or listing name. When the two differ, say which one the copy should use.
- **Decisions made early save rounds.** A choice settled in the brief (posture,
  approved structure/function lines, which frames carry the disclaimer, whether the
  pack's own printed claims may show) never comes back as a review comment.
- **References with reasons.** "Liked: warm side light and a quiet left third for
  text" helps. "Liked: this one" does not. One disliked reference with a reason often
  settles more than three liked ones.
- **Evidence over memory.** Attach the label file and the shopper evidence instead of
  summarising them. The pack quotes the label; it cannot quote a summary.

## Blocking gaps

These stop the pack. The builder sends one message that lists every blocking
question at once and waits for the answers:

- **Identity:** the brand, the product as printed, the variant or the ASIN is missing
  or contradicts the label file.
- **Marketplace:** the marketplace or copy language is missing.
- **Label file:** no label or spec file, or one too small to read every line.
- **Posture for a regulated product:** a supplement, food with a health angle,
  topical or other regulated product without a claims posture, or with
  structure/function lines named loosely instead of exactly.

Every other gap becomes a flagged assumption in `pack.md`. For example, no website
means the brand CI comes from the pack and the brief alone; no POE export means
lower confidence on the buying jobs, stated in the pack.
