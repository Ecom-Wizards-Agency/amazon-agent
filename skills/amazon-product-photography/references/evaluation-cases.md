# Photo-scope checks

Maintenance-only synthetic cases. Inspect decisions, not exact phrasing.

1. User supplies one bottle photo and asks for three FLORA photo prompts: packshot,
   bedside scene and material detail. No POE, approved copy or Figma file exists.
   Expected: proceed with photo prompts/reference mapping; request only missing
   visual evidence needed for a particular view. No invented packaging, mandatory
   strategy, sales typography, Figma file creation or paid generation.
2. Product reference shows amber glass; style reference shows a blue competitor
   bottle in cool light. Expected: preserve amber product and adopt only lighting.
   Explicitly distinguish a provisional text-described input from inspected photos.
3. User requests a real photo edit and its generation is authorized and available.
   Expected: execute and inspect the edited asset, rather than only writing a prompt.
4. User asks for editable headlines on three existing photos. Expected: route to
   amazon-image-production; do not regenerate suitable product photography.
5. FLORA run timed out with a known ID and no additional run budget. Expected:
   check the existing job and inspect results, not resubmit. One image input with
   allow_multiple does not establish simultaneous product/style references.
