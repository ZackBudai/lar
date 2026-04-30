#!/usr/bin/env python3
"""
Download self-contained FOF problems from tptp.org.

Targets domains known for small, include-free, first-order form problems:
  SYN  – Syntactic (Pelletier problems and derivatives)
  LCL  – Logic Calculi
  PUZ  – Puzzles

Each downloaded file is validated:
  - No include() directives
  - Contains at least one fof() block with role 'conjecture'
  - Parseable by our tptp.py parser
  - Status is Theorem or CounterSatisfiable (so expected outcome is known)

Usage:
    python scripts/download_tptp_fof.py [--max-per-domain N] [--timeout SEC]
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Add src/ to path so we can import the parser for validation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lar.tptp import parse_tptp_problem  # noqa: E402

BASE_URL = "https://tptp.org/cgi-bin/SeeTPTP"
OUT_DIR = Path(__file__).resolve().parents[1] / "datasets" / "tptp_fof"

# Domains and problem number range to probe.
# Format: (domain, first_num, last_num, version_suffix)
# The +1 suffix means FOF version 1.
DOMAINS: list[tuple[str, int, int, str]] = [
    ("SYN", 1, 999, "+1"),
    ("LCL", 1, 999, "+1"),
    ("PUZ", 1, 999, "+1"),
]

# Statuses we accept — must map unambiguously to True/False expected value.
ACCEPTED_STATUSES = {
    "theorem",
    "unsatisfiable",
    "contradictoryaxioms",
    "countersatisfiable",
    "satisfiable",
}


def _fetch_html(url: str, timeout: int) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("iso-8859-1")
    except Exception:
        return None


def _extract_tptp(html: str) -> str | None:
    match = re.search(r"<pre>(.*?)</pre>", html, re.DOTALL)
    if not match:
        return None
    text = match.group(1)
    # Decode HTML entities so TPTP operators like <=> are restored.
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    # Strip HTML tags using a pattern that only matches tags starting with a
    # letter (e.g. <A HREF=...>, </A>).  The naive <[^>]+> pattern would
    # greedily consume TPTP operators like <= and <=> across line boundaries.
    text = re.sub(r"</?\w[^>]*>", "", text)
    return text.strip()


def _status_from_text(text: str) -> str | None:
    m = re.search(r"%\s*Status\s*:\s*([A-Za-z_]+)", text, re.IGNORECASE)
    return m.group(1).lower() if m else None


def _uses_equality(text: str) -> bool:
    """Return True if the problem uses equality predicates.

    Checks the SPC code first (most reliable), then scans formula lines for
    a standalone = that is not part of => or <=>.
    """
    # SPC code ending in _EQ means equality is used; _NEQ means it is not.
    spc = re.search(r"%\s*SPC\s*:\s*(\S+)", text, re.IGNORECASE)
    if spc:
        code = spc.group(1)
        if "_EQ" in code and "_NEQ" not in code:
            return True
        if "_NEQ" in code:
            return False
    # Fallback: scan non-comment lines for a bare = not part of => or <=>
    for line in text.splitlines():
        if line.lstrip().startswith("%"):
            continue
        # Remove => and <=> so only standalone = remains
        stripped = re.sub(r"<=>|=>|<=", "", line)
        if "=" in stripped:
            return True
    return False


def _is_valid(text: str, name: str) -> bool:
    """Return True only if the problem passes all quality filters."""
    # Must not use external includes
    if "include(" in text:
        return False
    # Must have at least one fof() block
    if "fof(" not in text:
        return False
    # Must have a conjecture role
    if "conjecture" not in text.lower():
        return False
    # Must not use equality (our prover has no equality reasoning)
    if _uses_equality(text):
        return False
    # Status must be one we can interpret
    status = _status_from_text(text)
    if status not in ACCEPTED_STATUSES:
        return False
    # Must be parseable by our parser
    try:
        parse_tptp_problem(text, fallback_name=name)
    except Exception:
        return False
    return True


def download_problem(
    domain: str, num: int, suffix: str, http_timeout: int
) -> tuple[str, str] | None:
    """Fetch one problem. Returns (filename, content) or None."""
    problem_id = f"{domain}{num:03d}{suffix}"
    url = f"{BASE_URL}?Category=Problems&Domain={domain}&File={problem_id}.p"
    html = _fetch_html(url, http_timeout)
    if html is None:
        return None
    # A missing problem typically returns a very short page
    if len(html) < 200:
        return None
    content = _extract_tptp(html)
    if not content or len(content) < 40:
        return None
    filename = problem_id.lower() + ".p"
    return filename, content


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-per-domain",
        type=int,
        default=200,
        help="Stop after this many valid problems per domain (default 200)",
    )
    parser.add_argument(
        "--http-timeout",
        type=int,
        default=10,
        help="HTTP request timeout in seconds (default 10)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.4,
        help="Delay between requests in seconds (default 0.4)",
    )
    parser.add_argument(
        "--max-consecutive-missing",
        type=int,
        default=20,
        help="Stop probing a domain after this many consecutive missing problems (default 20)",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_saved = 0
    total_skipped = 0

    for domain, first, last, suffix in DOMAINS:
        print(f"\n{'='*60}")
        print(f"Domain: {domain}  range: {domain}{first:03d} – {domain}{last:03d}")
        print(f"{'='*60}")
        saved = 0
        consecutive_missing = 0

        for num in range(first, last + 1):
            if saved >= args.max_per_domain:
                print(f"  Reached limit of {args.max_per_domain} for {domain}")
                break
            if consecutive_missing >= args.max_consecutive_missing:
                print(f"  {consecutive_missing} consecutive missing — stopping {domain}")
                break

            result = download_problem(domain, num, suffix, args.http_timeout)
            time.sleep(args.delay)

            if result is None:
                consecutive_missing += 1
                continue

            filename, content = result
            consecutive_missing = 0

            if not _is_valid(content, Path(filename).stem):
                status = _status_from_text(content) or "?"
                reason = (
                    "include()"
                    if "include(" in content
                    else "no conjecture"
                    if "conjecture" not in content.lower()
                    else "equality"
                    if _uses_equality(content)
                    else f"status={status}"
                    if status not in ACCEPTED_STATUSES
                    else "parse error"
                )
                print(f"  skip  {filename}  ({reason})")
                total_skipped += 1
                continue

            out_path = OUT_DIR / filename
            out_path.write_text(content, encoding="utf-8")
            status = _status_from_text(content) or "?"
            print(f"  saved {filename}  status={status}")
            saved += 1
            total_saved += 1

        print(f"  → {saved} saved for {domain}")

    print(f"\n{'='*60}")
    print(f"Done.  Saved: {total_saved}   Skipped: {total_skipped}")
    print(f"Output directory: {OUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
