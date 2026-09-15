# Swissker United States: crop preparation, 14 September 2026

Historical evidence for [brand-store-updates.md](brand-store-updates.md). This
preparation did not establish live mutation compatibility or authorize an update.

The requested source draft and live edition each contained six pages. An older
default ended edition contained nine. Reading the page tree before selecting the
correct version would therefore have produced the wrong coverage assumption.

All 18 approved square PNGs matched their prior file hashes. Their decoded RGB
pixels matched 18 unique saved tiles exactly, although Amazon's PNG byte hashes
differed after reencoding. Eleven desktop images and all 18 mobile images already
retained the full square. Seven desktop images had a 1500 × 750 crop beginning
450 pixels down the original 1500 × 1500 image. Reusing verified existing artwork
could repair the crops without treating all 18 assets as incorrect.

Saved `imageWidth` and `imageHeight` represented cropped dimensions in this UI.
`canvasData` supplied original dimensions and displayed canvas geometry, and
`cropBoxData` supplied the displayed crop box. The saved image URL alone did not
identify the applied crop; the editor's transformed image URL exposed it separately.

Opening the existing Crop editor, then clicking Cancel and closing without a drag,
upload or Crop confirmation, changed seven saved canvas/crop display-geometry
fields on the source draft. The effective natural-image crop, image, link and all
other content remained identical. The live edition remained unchanged. This
incidental write was disclosed, the original snapshot and manifest were retained,
and the proposed baseline was refreshed explicitly before approval. Cancel did not
guarantee a read-only inspection of that control.

An initial scoped-adapter probe could not get a fresh page response because the
builder cached visited pages. Replaying the observed business POST returned HTTP
403. Reloading with response listeners active, selecting the exact edition and
visiting pages through the UI yielded fresh saved data without inspecting
authentication headers or browser storage. These are read-path findings; uploads,
crop correction and publishing were not tested by them.

The final scoped-adapter read probe passed account/country/version verification,
desktop and mobile editor readback with existing-asset receipts for both a full-frame
tile and a cropped tile, and complete six-page source/live preservation checks
against the explicitly refreshed baselines. It left the Crop control closed.
An uncropped tile lacked `canvasData`/`cropBoxData`; its full frame was established
through verified source PNG dimensions, saved width/height, zero offsets and editor
readback. Missing crop metadata is therefore not a universal blocker, but arbitrary
or partial geometry still cannot be assumed correct.

Evidence is under `output/swissker/catalog/2026-09-14-store-updater/` in the Amazon
Agent workspace: `preparation-report.md`, original/current source snapshots,
`crop-inspection-metadata-diff.json`, `current-asset-matches.json` and the adapter
probe reports, including `adapter-final-probe.json`. The original request is linked
in that run's prepared manifest.
