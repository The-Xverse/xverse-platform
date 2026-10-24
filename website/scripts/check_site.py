#!/usr/bin/env python3
"""Check all built local links, fragments, required outputs, and public boundaries."""

from __future__ import annotations

from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urljoin, urlsplit

SITE = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "name" in attrs:
            self.ids.add(attrs["name"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])


def check(dist: Path, base: str) -> dict:
    errors: list[str] = []
    documents: dict[Path, Document] = {}
    for path in dist.rglob('*'):
        if path.name in {'.doctrees', '.buildinfo', '__pycache__', '.venv'} or path.suffix in {'.pickle', '.doctree', '.pyc'}:
            errors.append(f"Build cache in publication: {path.relative_to(dist)}")
    search_entry = dist / "pagefind/pagefind-entry.json"
    if search_entry.is_file():
        languages = set(json.loads(search_entry.read_text(encoding="utf-8")).get("languages", {}))
        if languages != {"en"}:
            errors.append(f"Shared search must contain one English index; found: {sorted(languages)}")
    for page in sorted(dist.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        if re.search(r"/home/[A-Za-z0-9_-]+/|/media/[A-Za-z0-9_-]+/|distributed_safety_critical_thesis", text):
            errors.append(f"Private/local path in {page.relative_to(dist)}")
        documents[page.resolve()] = Document(text)
    checked = 0
    for page, document in documents.items():
        relative = page.relative_to(dist.resolve()).as_posix()
        page_url = "https://docs.invalid" + base + relative
        for link in document.links:
            parts = urlsplit(urljoin(page_url, link))
            if parts.scheme not in ("http", "https") or parts.netloc != "docs.invalid":
                continue
            decoded = unquote(parts.path)
            if not decoded.startswith(base):
                errors.append(f"{relative}: link escapes base: {link}")
                continue
            target = (dist / decoded[len(base):]).resolve()
            if not target.is_relative_to(dist.resolve()):
                errors.append(f"{relative}: link escapes artifact: {link}")
                continue
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"{relative}: missing target: {link}")
            elif parts.fragment and target.suffix == ".html":
                target_document = documents.get(target)
                if target_document and unquote(parts.fragment) not in target_document.ids:
                    errors.append(f"{relative}: missing anchor: {link}")
            checked += 1
    required = ["index.html", "docs/index.html", "docs/getting-started/first-system/index.html", "reference/python/index.html", "reference/cpp/index.html", "publication-manifest.json", "pagefind/pagefind.js", "pagefind/pagefind-entry.json"]
    for filename in required:
        if not (dist / filename).is_file():
            errors.append(f"Missing required output: {filename}")
    if errors:
        raise ValueError("\n".join(errors[:100]) + (f"\n... {len(errors)} total errors" if len(errors) > 100 else ""))
    return {"htmlPages": len(documents), "localLinksChecked": checked, "errors": 0, "basePath": base}


if __name__ == "__main__":
    try:
        result = check(SITE / "dist", os.environ.get("BASE_PATH", "/xverse-platform/"))
        print(json.dumps(result, sort_keys=True))
    except Exception as error:
        print(f"Website check failed:\n{error}", file=sys.stderr)
        raise SystemExit(1)
