"""Validate the okf/ knowledge bundle against OKF v0.2 basics and project conventions.

Usage: python scripts/check_okf.py   (requires PyYAML)
Exit code 0 when valid, 1 when errors are found.
"""

from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "okf"
REQUIRED_FILES = ["index.md", "project.md", "current-state.md", "log.md"]
REQUIRED_DIRS = ["architecture", "features", "decisions", "development"]
STATUS_VALUES = {"draft", "stable", "deprecated"}
ACTOR = re.compile(r"^(human:|process:)\S+$|^[^\s/]+/\S+$")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"```.*?```", re.S)
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|gsk_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?i:(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}))"
)

errors: list[str] = []


def err(path: Path, msg: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {msg}")


def split_frontmatter(text: str):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text
    return text[4:end], text[end + 5:]


def check_timestamp(path: Path, field: str, value) -> None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            err(path, f"{field} must include a UTC offset")
        return
    if not isinstance(value, str):
        err(path, f"{field} must be an ISO 8601 datetime")
        return
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        err(path, f"{field} is not ISO 8601: {value!r}")
        return
    if parsed.tzinfo is None:
        err(path, f"{field} must include a UTC offset")


def check_actor_event(path: Path, field: str, event) -> None:
    if not isinstance(event, dict) or "by" not in event:
        err(path, f"{field} entries need a 'by' actor")
        return
    if not ACTOR.match(str(event["by"])):
        err(path, f"{field}.by does not follow the actor convention: {event['by']!r}")
    if "at" in event:
        check_timestamp(path, f"{field}.at", event["at"])


def check_concept(path: Path, meta) -> None:
    if not isinstance(meta, dict):
        err(path, "frontmatter must be a YAML mapping")
        return
    if not str(meta.get("type") or "").strip():
        err(path, "missing non-empty 'type'")
    if "status" in meta and meta["status"] not in STATUS_VALUES:
        err(path, f"status must be one of {sorted(STATUS_VALUES)}")
    if "tags" in meta and not isinstance(meta["tags"], list):
        err(path, "tags must be a list")
    if "generated" in meta:
        check_actor_event(path, "generated", meta["generated"])
    if "verified" in meta:
        events = meta["verified"] if isinstance(meta["verified"], list) else [meta["verified"]]
        for e in events:
            check_actor_event(path, "verified", e)
    if "stale_after" in meta:
        check_timestamp(path, "stale_after", meta["stale_after"])
    for i, s in enumerate(meta.get("sources") or []):
        if not isinstance(s, dict) or not s.get("resource"):
            err(path, f"sources[{i}] requires 'resource'")


def check_links(path: Path, body: str) -> None:
    for target in LINK.findall(FENCE.sub("", body)):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        resolved = (BUNDLE / target.lstrip("/")) if target.startswith("/") else (path.parent / target)
        resolved = resolved.resolve()
        if resolved.is_dir():
            resolved = resolved / "index.md"
        if not resolved.exists():
            err(path, f"broken link: {target}")


def check_log(path: Path, body: str) -> None:
    headings = re.findall(r"^## (.+)$", body, re.M)
    if not headings:
        err(path, "log has no date headings")
    dates = []
    for h in headings:
        try:
            dates.append(date.fromisoformat(h.strip()))
        except ValueError:
            err(path, f"log heading is not YYYY-MM-DD: {h!r}")
    if dates != sorted(dates, reverse=True):
        err(path, "log headings must be newest first")


def check_index_coverage(index: Path, body: str) -> None:
    linked = {(index.parent / t.split("#", 1)[0]).resolve() for t in LINK.findall(body) if not t.startswith(("http", "/"))}
    for md in index.parent.glob("*.md"):
        if md.name in ("index.md", "log.md"):
            continue
        if md.resolve() not in linked:
            err(index, f"does not list {md.name}")
    for sub in (p for p in index.parent.iterdir() if p.is_dir()):
        if sub.resolve() not in linked and (sub / "index.md").resolve() not in linked:
            err(index, f"does not list subdirectory {sub.name}/")


def main() -> int:
    if not BUNDLE.is_dir():
        print("okf/ directory not found")
        return 1
    for f in REQUIRED_FILES:
        if not (BUNDLE / f).is_file():
            err(BUNDLE / f, "required file missing")
    for d in REQUIRED_DIRS:
        if not (BUNDLE / d / "index.md").is_file():
            err(BUNDLE / d, "required directory or its index.md missing")

    count = 0
    for path in sorted(BUNDLE.rglob("*.md")):
        count += 1
        text = path.read_text(encoding="utf-8")
        if SECRET.search(text):
            err(path, "possible secret detected")
        raw, body = split_frontmatter(text.replace("\r\n", "\n"))
        meta = None
        if raw is not None:
            try:
                meta = yaml.safe_load(raw) or {}
            except yaml.YAMLError as e:
                err(path, f"invalid YAML frontmatter: {e}")
                continue

        if path.name == "index.md":
            if meta is not None and not (path.parent == BUNDLE and set(meta) <= {"okf_version"}):
                err(path, "index files must not carry frontmatter (root may carry only okf_version)")
            check_index_coverage(path, body)
        elif path.name == "log.md":
            if meta is not None:
                err(path, "log files must not carry frontmatter")
            check_log(path, body)
        else:
            if meta is None:
                err(path, "concept document missing YAML frontmatter")
            else:
                check_concept(path, meta)
        check_links(path, body)

    if errors:
        print(f"OKF check failed ({len(errors)} errors in {count} files):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OKF check passed: {count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
