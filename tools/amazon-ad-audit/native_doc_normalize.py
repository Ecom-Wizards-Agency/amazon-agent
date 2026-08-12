#!/usr/bin/env python3
"""Make an imported audit's cover native-safe in Google Docs.

Google flattens an imported DOCX cover section: the zero-margin full-bleed page one
becomes a normal-margin page with the cover image sized to the text column, so the
artwork sits inside the margins with a white band around it. The DOCX cannot express
this in a way conversion preserves, so the geometry is rebuilt after import instead.

    doc  = <full documents.get?includeTabsContent=true response>
    reqs = build_native_account_audit_requests(doc)
    # apply as ONE documents.batchUpdate with writeControl.requiredRevisionId

What the batch does, in order:

  1. deletes the imported page break after the cover
  2. inserts a NEXT_PAGE section break in its place
  3. makes the resulting first section zero-margin
  4. replaces the cover image with the same image at full page size
  5. tells the document to use a separate (empty) first-page header and footer

Deliberately NOT here: any repair of running-header tab stops. The renderer lays the
header and footer out with fixed-width tables now, so there is nothing to realign. The
previous tab repair inserted a literal tab before a hardcoded "ACCOUNT AUDIT" string,
which silently did nothing for any client using a `branding.doc_label` override and
inserted a stray third tab whenever the logo asset was missing.
"""
from __future__ import annotations

# Height in points given back to the paragraph Docs inserts before a section break.
# A 1pt line at 100% spacing needs a bit over 1pt; 2pt is the smallest safe value and
# is a 0.7mm sliver at the very bottom of the cover, below the artwork's own margin.
TRAILING_LINE = 2.0


def _dimension(magnitude: float) -> dict:
    return {"magnitude": magnitude, "unit": "PT"}


def _tab(document: dict) -> dict:
    """The document's first tab, flattened.

    `documents.get?includeTabsContent=true` nests the content under
    `tabs[i].documentTab` and puts the id under `tabs[i].tabProperties.tabId`, while a
    hand-built or already-flattened tab carries `body` and `tabId` directly. Accept both,
    because reading only the flat shape makes every real API response look like a
    document with no cover.
    """
    tabs = document.get("tabs") or []
    if not tabs:
        raise ValueError("Google Doc readback has no tab")
    tab = tabs[0]
    if "documentTab" in tab:
        tab_id = (tab.get("tabProperties") or {}).get("tabId")
        return {**tab["documentTab"], "tabId": tab_id}
    return tab


def _paragraph_text(paragraph: dict) -> str:
    return "".join(
        element.get("textRun", {}).get("content", "")
        for element in paragraph.get("elements", [])
    )


def _cover_contract(tab: dict) -> tuple[dict, dict, dict]:
    """The cover paragraph, its image object, and the page break that follows it."""
    content = tab.get("body", {}).get("content", [])
    if len(content) < 3:
        raise ValueError("Deep audit has no imported cover structure")

    cover = content[1]
    image_element = next(
        (e for e in cover.get("paragraph", {}).get("elements", [])
         if e.get("inlineObjectElement", {}).get("inlineObjectId")),
        None,
    )
    if image_element is None:
        raise ValueError("First audit paragraph has no cover image")

    cover_id = image_element["inlineObjectElement"]["inlineObjectId"]
    inline_object = (tab.get("inlineObjects") or {}).get(cover_id)
    if not inline_object:
        raise ValueError(f"Cover inline object {cover_id!r} is missing")

    imported_break = content[2]
    if not any("pageBreak" in e for e in imported_break.get("paragraph", {}).get("elements", [])):
        raise ValueError("Expected the imported page break immediately after the cover")
    return cover, inline_object, imported_break


def has_cover(document: dict) -> bool:
    """Whether this document imported a cover. A `monthly` audit renders without one."""
    try:
        _cover_contract(_tab(document))
        return True
    except ValueError:
        return False


def build_native_account_audit_requests(document: dict) -> list[dict]:
    """Return one ordered batch that makes an imported deep audit native-safe."""
    tab = _tab(document)
    cover, inline_object, imported_break = _cover_contract(tab)
    tab_id = tab["tabId"]
    page_size = (tab.get("documentStyle") or {}).get("pageSize") or {}
    width = page_size.get("width", {}).get("magnitude")
    height = page_size.get("height", {}).get("magnitude")
    if not width or not height:
        raise ValueError("Google Doc readback has no page size")

    cover_element = next(
        e for e in cover["paragraph"]["elements"]
        if e.get("inlineObjectElement", {}).get("inlineObjectId")
    )
    content_uri = inline_object["inlineObjectProperties"]["embeddedObject"]["imageProperties"]["contentUri"]

    def at(index):
        return {"tabId": tab_id, "index": index}

    requests: list[dict] = [
        # 1. drop the imported page break AND its paragraph mark.
        #
        # Deleting only the break character leaves an empty paragraph behind, and that
        # paragraph belongs to the zero-margin cover section. The cover image is exactly
        # one page tall, so the leftover line has nowhere to sit and pushes a BLANK second
        # page, still carrying the cover section's zero margins, which is why the running
        # header and footer appeared jammed against the paper edge on page two.
        {"deleteContentRange": {"range": {
            "tabId": tab_id,
            "startIndex": imported_break["startIndex"],
            "endIndex": imported_break["endIndex"],
        }}},
        # 2. a real section boundary in its place
        {"insertSectionBreak": {"sectionType": "NEXT_PAGE", "location": at(imported_break["startIndex"])}},
        # 3. the cover section carries no margins
        {"updateSectionStyle": {
            "range": {"tabId": tab_id,
                      "startIndex": cover["startIndex"],
                      "endIndex": imported_break["startIndex"]},
            "sectionStyle": {k: _dimension(0) for k in (
                "marginTop", "marginBottom", "marginLeft", "marginRight",
                "marginHeader", "marginFooter")},
            "fields": "marginTop,marginBottom,marginLeft,marginRight,marginHeader,marginFooter",
        }},
        # 4. the same image, at the full page
        {"deleteContentRange": {"range": {
            "tabId": tab_id,
            "startIndex": cover_element["startIndex"],
            "endIndex": cover_element["endIndex"],
        }}},
        {"insertInlineImage": {
            "uri": content_uri,
            "objectSize": {"width": _dimension(width), "height": _dimension(height - TRAILING_LINE)},
            "location": at(cover_element["startIndex"]),
        }},
        # Docs always puts a paragraph immediately BEFORE a section break, and that
        # paragraph belongs to the section being closed, so it inherits the cover's zero
        # margins. A full-page-height cover leaves it nowhere to sit, and it spills onto a
        # blank second page still carrying zero margins, which is what put the running
        # header and footer hard against the paper edge there. Collapse it to a hairline
        # and give the cover that hairline back, so page one holds both.
        {"updateTextStyle": {
            "range": {"tabId": tab_id,
                      "startIndex": imported_break["startIndex"],
                      "endIndex": imported_break["startIndex"] + 1},
            "textStyle": {"fontSize": _dimension(1)},
            "fields": "fontSize",
        }},
        {"updateParagraphStyle": {
            "range": {"tabId": tab_id,
                      "startIndex": imported_break["startIndex"],
                      "endIndex": imported_break["startIndex"] + 1},
            "paragraphStyle": {"lineSpacing": 100, "spaceAbove": _dimension(0),
                               "spaceBelow": _dimension(0)},
            "fields": "lineSpacing,spaceAbove,spaceBelow",
        }},
        # 5. an empty first page header and footer, so nothing prints over the cover
        {"updateDocumentStyle": {
            "tabId": tab_id,
            "documentStyle": {"useFirstPageHeaderFooter": True},
            "fields": "useFirstPageHeaderFooter",
        }},
    ]
    return requests


def zero_margin(section_style: dict) -> bool:
    """Whether every margin on a section reads as zero.

    The Docs API omits `magnitude` entirely for a zero value, so a correctly normalized
    cover section reads back as `{"unit": "PT"}` and an `== 0` check fails on it.
    """
    keys = ("marginTop", "marginBottom", "marginLeft", "marginRight")
    return all((section_style.get(k) or {}).get("magnitude", 0) == 0 for k in keys)
