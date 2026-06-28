#!/usr/bin/env python3
"""Refresh the local DataDive support article index.

This uses the public Zendesk Help Center API. It stores article metadata,
source URLs, update dates, tags, and short snippets. It does not store private
DataDive account data, API keys, cookies, sessions, or full article mirrors.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from html import unescape
from html.parser import HTMLParser
from urllib.request import Request, urlopen


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(REPO, "skills/amazon-seo/references/datadive-support")
BASE = "https://support.datadive.tools/api/v2/help_center/en-us"


class TextHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data and data.strip():
            self.parts.append(data.strip())

    def get_text(self) -> str:
        return re.sub(r"\s+", " ", unescape(" ".join(self.parts))).strip()


def fetch_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def all_pages(path: str) -> list[dict]:
    url = f"{BASE}/{path}"
    rows: list[dict] = []
    while url:
        data = fetch_json(url)
        key = "articles" if "articles" in data else "sections" if "sections" in data else "categories"
        rows.extend(data.get(key, []))
        url = data.get("next_page")
    return rows


def html_to_text(html: str) -> str:
    parser = TextHTMLParser()
    parser.feed(html or "")
    return parser.get_text()


def tag_article(title: str, text: str) -> list[str]:
    haystack = f"{title} {text}".lower()
    terms = [
        "master keyword list", "mkl", "roots", "outlier", "residue",
        "listing builder", "ranking juice", "rank radar", "niche pipeline",
        "product scorecard", "ppc", "export", "relevancy", "search volume",
        "competitor", "deep dive",
    ]
    return [term for term in terms if term in haystack]


def build_records() -> list[dict]:
    categories = all_pages("categories.json?per_page=100")
    sections = all_pages("sections.json?per_page=100")
    articles = all_pages("articles.json?per_page=100")
    cat_by_id = {c["id"]: c for c in categories}
    sec_by_id = {s["id"]: s for s in sections}

    records = []
    for article in articles:
        text = html_to_text(article.get("body", ""))
        section = sec_by_id.get(article.get("section_id"), {})
        category = cat_by_id.get(section.get("category_id"), {})
        records.append({
            "id": article["id"],
            "title": article.get("title", ""),
            "html_url": article.get("html_url", ""),
            "category": category.get("name", ""),
            "section": section.get("name", ""),
            "created_at": article.get("created_at", ""),
            "updated_at": article.get("updated_at", ""),
            "draft": article.get("draft", False),
            "outdated": article.get("outdated", False),
            "tags": tag_article(article.get("title", ""), text),
            "snippet": text[:420],
            "word_count": len(text.split()),
        })
    records.sort(key=lambda r: (r["category"], r["section"], r["title"].lower()))
    return records


def write_index(records: list[dict]) -> None:
    today = dt.date.today().isoformat()
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "datadive-support-article-inventory.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": dt.datetime.now().astimezone().isoformat(), "count": len(records), "articles": records}, f, ensure_ascii=False, indent=2)

    lines = [
        "---",
        "title: DataDive Support Article Index",
        "type: reference",
        "source: DataDive Zendesk Help Center API",
        f"updated: {today}",
        f"article_count: {len(records)}",
        "---",
        "",
        "# DataDive Support Article Index",
        "",
        "Local searchable index of the public DataDive support center. Stores metadata, links, update dates, tags, and short snippets, not a full article mirror.",
        "",
    ]
    current_group = None
    for record in records:
        group = f"{record['category']} / {record['section']}"
        if group != current_group:
            lines += [f"## {group}", ""]
            current_group = group
        tags = ", ".join(record["tags"]) if record["tags"] else "general"
        lines += [
            f"### [{record['title']}]({record['html_url']})",
            "",
            f"- Updated: `{record['updated_at'][:10]}` | Words indexed: `{record['word_count']}` | Tags: `{tags}`",
            f"- Snippet: {record['snippet']}",
            "",
        ]
    with open(os.path.join(OUT_DIR, "datadive-support-index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    seo_terms = {"master keyword list", "mkl", "roots", "outlier", "residue", "listing builder", "ranking juice", "rank radar", "niche pipeline", "product scorecard", "ppc", "export", "relevancy"}
    seo_records = [r for r in records if seo_terms.intersection(r["tags"])]
    seo_lines = [
        "---",
        "title: DataDive SEO Workflow Article Map",
        "type: reference",
        "source: DataDive Zendesk Help Center API",
        f"updated: {today}",
        "---",
        "",
        "# DataDive SEO Workflow Article Map",
        "",
        "Use this map when an Amazon SEO workflow needs DataDive terminology or UI context. Open source articles for exact current details.",
        "",
    ]
    for record in seo_records:
        seo_lines += [
            f"## [{record['title']}]({record['html_url']})",
            "",
            f"- Area: {record['category']} / {record['section']}",
            f"- Updated: `{record['updated_at'][:10]}`",
            f"- Tags: {', '.join(record['tags']) if record['tags'] else 'general'}",
            f"- Why it matters: {record['snippet']}",
            "",
        ]
    with open(os.path.join(OUT_DIR, "datadive-seo-workflow-article-map.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(seo_lines))


def main() -> int:
    records = build_records()
    write_index(records)
    print(f"Saved {len(records)} DataDive support article records to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
