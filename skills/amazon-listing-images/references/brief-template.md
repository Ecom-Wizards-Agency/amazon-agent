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
Claim tier (R):               see image-copy.md for conversion costs; choose one:
                               - label facts only
                               - label facts + named structure/function lines:
                                 list each approved line exactly
                               - standard

Generation budget (R):        spend cap/currency, attempt cap, repair allowance;
                               zero if supplied assets cover required scenes
Required scenes (R):          at least one in-use and one separate lifestyle scene;
                               available assets or planned generation
Primary buying benefit (R):   supported benefit and whether the tier retains it

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
- **Claim tier:** missing tier, structure/function lines named loosely instead of
  exactly, or a tier that removes the primary benefit without the person's explicit
  decision after seeing the conversion costs in `references/image-copy.md`.
- **Production direction:** missing generation budget, required scene plan or human
  approver. A person may explicitly waive the pilot look; an agent cannot approve
  its own creative direction.

Other input gaps are recorded in `pack.md`. No website means CI comes from the pack
and brief. Missing POE input triggers the archive search in
`references/creative-pack.md`; research gaps follow that reference's human decision
gate before concept approval.
