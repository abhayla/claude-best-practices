"""Discovery adapter — bridges external findings into the learning pipeline.

Converts free-text discoveries from GitHub, Reddit, Twitter scans into
structured entries for config/discoveries.json. Handles dedup across runs,
rejection tracking, and confidence scoring.

Usage:
    PYTHONPATH=. python scripts/discovery_adapter.py --add <json_entry>
    PYTHONPATH=. python scripts/discovery_adapter.py --reject <discovery_id> --reason <text>
    PYTHONPATH=. python scripts/discovery_adapter.py --pending
    PYTHONPATH=. python scripts/discovery_adapter.py --stats
    PYTHONPATH=. python scripts/discovery_adapter.py --to-learning <discovery_id>
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DISCOVERIES_PATH = ROOT / "config" / "discoveries.json"
LEARNINGS_PATH = ROOT / ".claude" / "learnings.json"
REGISTRY_PATH = ROOT / "registry" / "patterns.json"


def load_discoveries() -> dict:
    """Load the discoveries database."""
    if not DISCOVERIES_PATH.exists():
        return {"_meta": {"version": "1.0.0", "last_updated": ""}, "discoveries": [], "rejected": []}
    with open(DISCOVERIES_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_discoveries(data: dict):
    """Save the discoveries database."""
    data["_meta"]["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(DISCOVERIES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def content_hash(content: str) -> str:
    """Generate a stable hash for dedup."""
    normalized = content.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def is_duplicate(data: dict, new_hash: str) -> bool:
    """Check if a discovery with this hash already exists."""
    for d in data["discoveries"]:
        if d.get("hash") == new_hash:
            return True
    for r in data["rejected"]:
        if r.get("hash") == new_hash:
            return True
    return False


def is_in_registry(name: str) -> bool:
    """Check if a pattern name already exists in the hub registry."""
    if not REGISTRY_PATH.exists():
        return False
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)
    return name in registry and not name.startswith("_")


def compute_confidence(entry: dict) -> int:
    """Compute confidence score 0-100 for a discovery."""
    score = 50

    trust = entry.get("source_trust", "low")
    if trust == "high":
        score += 25
    elif trust == "medium":
        score += 10

    if entry.get("has_frontmatter"):
        score += 10
    if entry.get("has_steps"):
        score += 5
    if entry.get("community_signal", 0) > 10:
        score += 5
    if entry.get("multiple_sources"):
        score += 5

    return min(100, score)


def add_discovery(raw_entry: dict) -> dict:
    """Add a discovery to the database. Returns the processed entry."""
    data = load_discoveries()

    name = raw_entry.get("name", "unnamed")
    content = raw_entry.get("content", "")
    h = content_hash(content) if content else content_hash(name)

    if is_duplicate(data, h):
        # Increment seen_count on existing entry
        for d in data["discoveries"]:
            if d.get("hash") == h:
                d["seen_count"] = d.get("seen_count", 1) + 1
                d["last_seen"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                if raw_entry.get("source") and raw_entry["source"] not in d.get("sources", []):
                    d.setdefault("sources", []).append(raw_entry["source"])
                    d["multiple_sources"] = len(d["sources"]) > 1
                    d["confidence"] = compute_confidence(d)
                save_discoveries(data)
                return {"status": "duplicate", "id": d["id"], "seen_count": d["seen_count"]}
        return {"status": "rejected_duplicate"}

    if is_in_registry(name):
        return {"status": "already_in_registry", "name": name}

    entry = {
        "id": f"D{len(data['discoveries']) + len(data['rejected']) + 1:04d}",
        "hash": h,
        "name": name,
        "type": raw_entry.get("type", "unknown"),
        "category": raw_entry.get("category", "unknown"),
        "source": raw_entry.get("source", "unknown"),
        "sources": [raw_entry.get("source", "unknown")],
        "source_trust": raw_entry.get("source_trust", "low"),
        "content_preview": content[:200] if content else "",
        "has_frontmatter": raw_entry.get("has_frontmatter", False),
        "has_steps": raw_entry.get("has_steps", False),
        "community_signal": raw_entry.get("community_signal", 0),
        "multiple_sources": False,
        "confidence": 0,
        "status": "pending",
        "discovered": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "last_seen": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "seen_count": 1,
    }
    entry["confidence"] = compute_confidence(entry)

    data["discoveries"].append(entry)
    save_discoveries(data)
    return {"status": "added", "id": entry["id"], "confidence": entry["confidence"]}


def reject_discovery(discovery_id: str, reason: str) -> dict:
    """Move a discovery to the rejected list with reason."""
    data = load_discoveries()

    for i, d in enumerate(data["discoveries"]):
        if d["id"] == discovery_id:
            d["status"] = "rejected"
            d["rejection_reason"] = reason
            d["rejected_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            data["rejected"].append(d)
            data["discoveries"].pop(i)
            save_discoveries(data)
            return {"status": "rejected", "id": discovery_id}

    return {"status": "not_found", "id": discovery_id}


def convert_to_learning(discovery_id: str) -> dict:
    """Convert a discovery into a learn-n-improve learning entry."""
    data = load_discoveries()

    discovery = None
    for d in data["discoveries"]:
        if d["id"] == discovery_id:
            discovery = d
            break

    if not discovery:
        return {"status": "not_found"}

    # Load or create learnings.json
    learnings = {"learnings": []}
    if LEARNINGS_PATH.exists():
        with open(LEARNINGS_PATH, encoding="utf-8") as f:
            learnings = json.load(f)

    next_id = f"L{len(learnings['learnings']) + 1:03d}"
    learning = {
        "id": next_id,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "error": {
            "message": f"Discovery from {discovery['source']}: {discovery['name']}",
            "file": "",
            "context": discovery.get("content_preview", ""),
        },
        "fix": {
            "description": f"Pattern discovered externally: {discovery['type']}",
            "diff": "",
        },
        "lesson": f"External pattern '{discovery['name']}' from {discovery['source']} "
                  f"(confidence: {discovery['confidence']}, seen {discovery['seen_count']}x)",
        "tags": ["external-discovery", discovery.get("type", "unknown"), discovery.get("source_trust", "low")],
        "reuse_count": 0,
    }

    learnings["learnings"].append(learning)
    LEARNINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEARNINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(learnings, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Mark discovery as imported
    discovery["status"] = "imported"
    discovery["imported_as"] = next_id
    save_discoveries(data)

    return {"status": "converted", "learning_id": next_id, "discovery_id": discovery_id}


def get_pending() -> list:
    """Get all pending discoveries sorted by confidence."""
    data = load_discoveries()
    pending = [d for d in data["discoveries"] if d.get("status") == "pending"]
    return sorted(pending, key=lambda x: -x.get("confidence", 0))


def get_stats() -> dict:
    """Get discovery pipeline statistics."""
    data = load_discoveries()
    discoveries = data["discoveries"]
    rejected = data["rejected"]

    pending = [d for d in discoveries if d.get("status") == "pending"]
    imported = [d for d in discoveries if d.get("status") == "imported"]

    by_trust = {}
    for d in discoveries:
        trust = d.get("source_trust", "unknown")
        by_trust[trust] = by_trust.get(trust, 0) + 1

    by_type = {}
    for d in discoveries:
        ptype = d.get("type", "unknown")
        by_type[ptype] = by_type.get(ptype, 0) + 1

    auto_queue = [d for d in pending if d.get("confidence", 0) >= 85 and d.get("source_trust") == "high"]

    return {
        "total_discoveries": len(discoveries),
        "pending": len(pending),
        "imported": len(imported),
        "rejected": len(rejected),
        "auto_queue_eligible": len(auto_queue),
        "by_trust": by_trust,
        "by_type": by_type,
        "avg_confidence": sum(d.get("confidence", 0) for d in pending) / len(pending) if pending else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Discovery adapter for self-improvement pipeline")
    parser.add_argument("--add", type=str, help="Add a discovery (JSON string)")
    parser.add_argument("--reject", type=str, help="Reject a discovery by ID")
    parser.add_argument("--reason", type=str, default="", help="Rejection reason")
    parser.add_argument("--to-learning", type=str, help="Convert discovery to learning entry")
    parser.add_argument("--pending", action="store_true", help="Show pending discoveries")
    parser.add_argument("--stats", action="store_true", help="Show pipeline statistics")
    args = parser.parse_args()

    if args.add:
        entry = json.loads(args.add)
        result = add_discovery(entry)
        print(json.dumps(result, indent=2))

    elif args.reject:
        result = reject_discovery(args.reject, args.reason)
        print(json.dumps(result, indent=2))

    elif args.to_learning:
        result = convert_to_learning(args.to_learning)
        print(json.dumps(result, indent=2))

    elif args.pending:
        pending = get_pending()
        if not pending:
            print("No pending discoveries.")
            return
        print(f"Pending discoveries ({len(pending)}):\n")
        for d in pending:
            auto = " [AUTO-QUEUE]" if d.get("confidence", 0) >= 85 and d.get("source_trust") == "high" else ""
            print(f"  {d['id']} | {d['confidence']:3d}% | {d['source_trust']:6s} | "
                  f"{d['type']:8s} | {d['name']}{auto}")
            if d.get("seen_count", 1) > 1:
                print(f"         seen {d['seen_count']}x from {len(d.get('sources', []))} source(s)")

    elif args.stats:
        stats = get_stats()
        print(json.dumps(stats, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
