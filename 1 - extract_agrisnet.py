# run with "python extract_agrisnet.py --output "D:\*****\proper address" --headed"
import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://www.tnagrisnet.tn.gov.in/home/schemes/en"

FIELD_NAMES = [
    "department",
    "scheme",
    "input_type",
    "component",
]

HEADINGS = [
    "Scheme Description",
    "Subsidy",
    "Eligibility",
    "Documents Required",
]


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def get_options(select):
    """Return non-placeholder options from a native HTML select."""
    return select.locator("option").evaluate_all("""
        options => options.map(o => ({
            value: o.value,
            label: (o.innerText || o.textContent || '').trim(),
            disabled: o.disabled
        }))
    """)


def visible_selects(page):
    return page.locator("select:visible")


def read_page(page):
    """Capture the visible page text and best-effort detail sections."""
    body = page.locator("body").inner_text()
    lines = [clean(line) for line in body.splitlines()]
    lines = [line for line in lines if line]

    result = {
        "page_text": "\n".join(lines),
        "scheme_description": None,
        "subsidy": None,
        "eligibility": None,
        "documents_required": None,
    }

    # Best-effort extraction based on visible section headings.
    heading_map = {
        "Scheme Description": "scheme_description",
        "Subsidy": "subsidy",
        "Eligibility": "eligibility",
        "Documents Required": "documents_required",
    }

    found = []
    for i, line in enumerate(lines):
        for heading, key in heading_map.items():
            if line.lower().rstrip(":") == heading.lower():
                found.append((i, heading, key))

    for j, (start, heading, key) in enumerate(found):
        end = found[j + 1][0] if j + 1 < len(found) else len(lines)
        section_lines = lines[start + 1:end]
        result[key] = "\n".join(section_lines).strip() or None

    return result


def non_placeholder_options(select):
    options = get_options(select)
    valid = []

    for option in options:
        label = clean(option["label"])
        value = option["value"]

        if option["disabled"]:
            continue
        if not value or not label:
            continue
        if label.lower() in {
            "select", "--select--", "choose", "please select"
        }:
            continue

        valid.append({"value": value, "label": label})

    return valid


def main():
    parser = argparse.ArgumentParser(
        description="Extract AGRISNET scheme data into JSON."
    )
    parser.add_argument(
        "--output",
        default="./agrisnet_data",
        help="Folder for JSON output and extraction report",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.8,
        help="Wait time after changing a dropdown, in seconds",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Show the browser while extracting",
    )
    args = parser.parse_args()

    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    failures = []
    seen = set()
    combinations_checked = 0

    def wait_for_update(page):
        page.wait_for_timeout(int(args.delay * 1000))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        page = browser.new_page()
        page.set_default_timeout(15000)

        try:
            page.goto(URL, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            # Some websites keep background requests open.
            page.wait_for_timeout(3000)

        if visible_selects(page).count() < 4:
            snapshot = output_dir / "initial_page.html"
            snapshot.write_text(page.content(), encoding="utf-8")
            browser.close()
            raise RuntimeError(
                "Could not find four visible native dropdowns. "
                f"Saved page HTML to {snapshot}. "
                "The portal may use custom dropdowns or changed its layout."
            )

        def walk(level, selected):
            nonlocal combinations_checked

            selects = visible_selects(page)
            if level >= len(FIELD_NAMES) or level >= selects.count():
                return

            field = FIELD_NAMES[level]
            options = non_placeholder_options(selects.nth(level))

            if not options:
                failures.append({
                    "selection": selected.copy(),
                    "field": field,
                    "error": "No selectable options found",
                })
                return

            for option in options:
                try:
                    # Reacquire the locator after each page update.
                    current_selects = visible_selects(page)
                    if level >= current_selects.count():
                        raise RuntimeError("Dropdown disappeared")

                    current_selects.nth(level).select_option(
                        value=option["value"]
                    )
                    wait_for_update(page)

                    chosen = selected.copy()
                    chosen[field] = option["label"]

                    if level < len(FIELD_NAMES) - 1:
                        walk(level + 1, chosen)
                        continue

                    # All four dropdowns have been selected.
                    combinations_checked += 1
                    details = read_page(page)

                    record = {
                        "source_url": page.url,
                        "extracted_at": datetime.now(
                            timezone.utc
                        ).isoformat(),
                        "department": chosen.get("department"),
                        "scheme": chosen.get("scheme"),
                        "input_type": chosen.get("input_type"),
                        "component": chosen.get("component"),
                        **details,
                    }

                    # Keep the combination even if some fields are empty.
                    fingerprint = json.dumps(
                        chosen, sort_keys=True, ensure_ascii=False
                    )
                    if fingerprint not in seen:
                        seen.add(fingerprint)
                        records.append(record)

                except Exception as exc:
                    failures.append({
                        "selection": selected.copy(),
                        "field": field,
                        "option": option["label"],
                        "error": str(exc),
                    })
                    # Continue with the next option where possible.

        try:
            walk(0, {})
        finally:
            # Save partial progress even if extraction encounters errors.
            (output_dir / "agrisnet_schemes.json").write_text(
                json.dumps(records, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            report = {
                "source_url": URL,
                "finished_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "combinations_checked": combinations_checked,
                "unique_records_saved": len(records),
                "failure_count": len(failures),
                "failures": failures,
                "notes": [
                    "Extraction is based on visible browser content.",
                    "Verify completeness against the official portal.",
                    "A saved record does not establish current scheme validity.",
                ],
            }

            (output_dir / "extraction_report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            browser.close()

    print(f"\nExtraction finished.")
    print(f"Output folder: {output_dir}")
    print(f"Records saved: {len(records)}")
    print(f"Combinations checked: {combinations_checked}")
    print(f"Errors: {len(failures)}")
    print(f"JSON: {output_dir / 'agrisnet_schemes.json'}")
    print(f"Report: {output_dir / 'extraction_report.json'}")


if __name__ == "__main__":
    main()
