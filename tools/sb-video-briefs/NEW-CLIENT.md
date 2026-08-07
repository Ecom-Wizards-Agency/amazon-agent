# New client setup: SB video briefs

1. Copy `config.TEMPLATE.json` to `config.<client>-<market>-<product-line>.json`. It stays local and gitignored. Use one config per product line.
2. Fill the exact Seller Central account-picker name, expected `partnerAccountId`, optional agency parent, marketplace label, marketplace, language, ASINs, DataDive niche, AdLabs profile, and existing Drive creative folder.
3. Pin the latest Google Drive keyword-research workbook when one exists. The scouting pass combines its roots with DataDive roots before POE discovery.
4. Brand kit and footage locations can start as `none`. Missing strategy direction does not block a brief. Missing required footage becomes an exact production gap on the affected card.
5. Build or refresh the Creative Reference & Asset Library before the brief.
6. Run the SB workflow. It pauses at the 3 to 5 cluster shortlist for operator confirmation.
7. Deliver with `build_and_deliver.py --config <config> --brief-md <file> --reference-md <file>`. A first delivery imports both branded DOCX files as native Google Docs. When both canonical ids are configured, the same command updates them in place and verifies title, folder, native MIME type, content readback, and PDF export before it reports completion.

Legacy `client.amazon_account`, `economics.break_even_acos`, `economics.break_even_source`, and `testing` keys are ignored with a migration warning. They never appear in editor deliverables.
