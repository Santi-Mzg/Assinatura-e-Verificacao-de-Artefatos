"""
audit_log.py
Queries the Rekor public transparency log for all signatures of a given image,
and generates a human-readable audit report in JSON and Markdown.

Usage:
    python scripts/audit_log.py --image ghcr.io/OWNER/REPO

Requirements:
    pip install requests
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import requests

REKOR_BASE = "https://rekor.sigstore.dev"


def search_rekor(image: str) -> list[dict]:
    """Search Rekor log entries that reference the given image."""
    url = f"{REKOR_BASE}/api/v1/index/retrieve"
    payload = {"hash": f"sha256:{image.split('@sha256:')[-1]}"} if "@sha256:" in image else {}

    # If no digest provided, search by subject
    if not payload:
        url = f"{REKOR_BASE}/api/v1/log/entries/retrieve"
        payload = {"subjects": [image]}

    resp = requests.post(url, json=payload, timeout=15)
    if resp.status_code != 200:
        print(f"[Rekor] search returned {resp.status_code}: {resp.text}", file=sys.stderr)
        return []
    data = resp.json()
    return data if isinstance(data, list) else []


def get_entry(uuid: str) -> dict | None:
    """Fetch a single Rekor log entry by UUID."""
    url = f"{REKOR_BASE}/api/v1/log/entries/{uuid}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        return None
    return resp.json()


def parse_entry(uuid: str, raw: dict) -> dict:
    """Extract relevant fields from a Rekor entry."""
    import base64

    body_b64 = list(raw.values())[0].get("body", "")
    body     = json.loads(base64.b64decode(body_b64).decode()) if body_b64 else {}

    integrated_time = list(raw.values())[0].get("integratedTime", 0)
    ts = datetime.fromtimestamp(integrated_time, tz=timezone.utc).isoformat() if integrated_time else "N/A"

    spec = body.get("spec", {})
    sig  = spec.get("signature", {})
    data = spec.get("data", {})

    return {
        "uuid":       uuid,
        "log_index":  list(raw.values())[0].get("logIndex", "N/A"),
        "timestamp":  ts,
        "kind":       body.get("kind", "N/A"),
        "algorithm":  sig.get("algorithm", "N/A"),
        "image_hash": data.get("hash", {}).get("value", "N/A"),
    }


def generate_markdown(image: str, entries: list[dict]) -> str:
    lines = [
        f"# Audit Log – {image}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Total signatures found: {len(entries)}",
        "",
        "| # | Timestamp (UTC) | Log Index | Kind | Algorithm | Image Hash (sha256) |",
        "|---|-----------------|-----------|------|-----------|---------------------|",
    ]
    for i, e in enumerate(entries, 1):
        h = e["image_hash"][:16] + "…" if len(e["image_hash"]) > 16 else e["image_hash"]
        lines.append(
            f"| {i} | {e['timestamp']} | {e['log_index']} | {e['kind']} | {e['algorithm']} | {h} |"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Query Rekor for image signing history.")
    parser.add_argument("--image", required=True, help="Image reference, e.g. ghcr.io/owner/repo:tag")
    parser.add_argument("--out-json", default="audit_report.json", help="Output JSON path")
    parser.add_argument("--out-md",   default="audit_report.md",   help="Output Markdown path")
    args = parser.parse_args()

    print(f"Searching Rekor for: {args.image}")
    uuids = search_rekor(args.image)

    if not uuids:
        print("No entries found in Rekor for this image.")
        report = {"image": args.image, "entries": []}
    else:
        print(f"Found {len(uuids)} entry(ies). Fetching details...")
        entries = []
        for uuid in uuids:
            raw = get_entry(uuid)
            if raw:
                entries.append(parse_entry(uuid, raw))
        report = {"image": args.image, "entries": entries}

        md = generate_markdown(args.image, entries)
        with open(args.out_md, "w") as f:
            f.write(md)
        print(f"Markdown report written to: {args.out_md}")

    with open(args.out_json, "w") as f:
        json.dump(report, f, indent=2)
    print(f"JSON report written to: {args.out_json}")


if __name__ == "__main__":
    main()
