"""Extract reference material from oversized SKILL.md files into references/ subdirectories.

Usage:
    python scripts/extract_references.py [--dry-run] [--skill SKILL_NAME] [--threshold 500]

For each oversized skill, identifies large sections (code blocks, tables, detailed guides)
and moves them to references/*.md, replacing with pointers in SKILL.md.
"""

import argparse
import re
import sys
from pathlib import Path


def count_content_lines(text: str) -> int:
    """Count non-empty lines in text."""
    return len([l for l in text.splitlines() if l.strip()])


def parse_sections(content: str) -> list[dict]:
    """Parse SKILL.md into sections by ## headings.

    Returns list of dicts with keys: heading, level, start_line, end_line, content, lines.
    The first section (before any heading) has heading=None.
    """
    lines = content.splitlines(keepends=True)
    sections = []
    current = {"heading": None, "level": 0, "start_line": 0, "lines": []}

    for i, line in enumerate(lines):
        match = re.match(r"^(#{1,4})\s+(.+)", line)
        if match:
            current["end_line"] = i
            current["content"] = "".join(current["lines"])
            sections.append(current)
            current = {
                "heading": match.group(2).strip(),
                "level": len(match.group(1)),
                "start_line": i,
                "lines": [line],
            }
        else:
            current["lines"].append(line)

    current["end_line"] = len(lines)
    current["content"] = "".join(current["lines"])
    sections.append(current)
    return sections


def is_frontmatter_or_preamble(section: dict, idx: int) -> bool:
    """Check if section is frontmatter, title, or preamble (should stay in SKILL.md)."""
    if idx == 0:
        return True
    heading = section.get("heading", "") or ""
    if section["level"] == 1:
        return True
    return False


def is_critical_section(section: dict) -> bool:
    """Check if section is a MUST DO/MUST NOT DO or CRITICAL RULES section."""
    heading = (section.get("heading") or "").upper()
    critical_keywords = ["MUST DO", "MUST NOT", "CRITICAL RULE", "CRITICAL:", "IMPORTANT"]
    return any(kw in heading for kw in critical_keywords)


def is_step_heading(section: dict) -> bool:
    """Check if this is a numbered STEP section."""
    heading = section.get("heading") or ""
    return bool(re.match(r"STEP\s+\d+", heading, re.IGNORECASE))


def estimate_section_weight(section: dict) -> int:
    """Estimate how many lines a section contributes."""
    return len(section["lines"])


def make_reference_filename(heading: str) -> str:
    """Convert a heading into a valid filename."""
    name = heading.lower()
    name = re.sub(r"^step\s+\d+[.:]\s*", "", name)
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    name = name[:50].rstrip("-")
    return name + ".md" if name else "extracted.md"


def collect_subsections(sections: list[dict], parent_idx: int) -> list[int]:
    """Collect indices of all subsections under a parent section."""
    parent_level = sections[parent_idx]["level"]
    children = []
    for i in range(parent_idx + 1, len(sections)):
        if sections[i]["level"] <= parent_level:
            break
        children.append(i)
    return children


def extract_skill(skill_dir: Path, threshold: int = 500, dry_run: bool = False) -> dict:
    """Extract reference material from an oversized SKILL.md.

    Returns dict with: skill_name, original_lines, final_lines, extracted_files, errors.
    """
    skill_md = skill_dir / "SKILL.md"
    result = {
        "skill_name": skill_dir.name,
        "original_lines": 0,
        "final_lines": 0,
        "extracted_files": [],
        "errors": [],
        "skipped": False,
    }

    if not skill_md.exists():
        result["errors"].append("SKILL.md not found")
        return result

    content = skill_md.read_text(encoding="utf-8")
    original_lines = len(content.splitlines())
    result["original_lines"] = original_lines

    if original_lines <= threshold:
        result["final_lines"] = original_lines
        result["skipped"] = True
        return result

    lines_to_cut = original_lines - threshold + 100  # aim 100 lines under threshold for safety

    sections = parse_sections(content)

    # Score sections for extraction eligibility
    candidates = []
    for i, sec in enumerate(sections):
        if is_frontmatter_or_preamble(sec, i):
            continue
        if is_critical_section(sec):
            continue

        weight = estimate_section_weight(sec)
        if weight < 10:
            continue

        # Higher score = more extractable
        score = weight
        # Prefer extracting subsections within STEP sections over the STEP itself
        if is_step_heading(sec):
            # Don't extract the STEP heading itself, but its children are candidates
            continue

        # Subsections (### or ####) are good extraction candidates
        if sec["level"] >= 3:
            score += 10

        candidates.append((i, score, weight))

    # Sort by score descending
    candidates.sort(key=lambda x: x[1], reverse=True)

    # Group subsections under their parent ## for cleaner extraction
    # Handles both STEP sections and non-STEP ## sections (e.g., ## Configuration)
    step_groups = {}
    for i, sec in enumerate(sections):
        if sec["level"] == 2 and not is_critical_section(sec) and not is_frontmatter_or_preamble(sec, i):
            children = collect_subsections(sections, i)
            if children:
                total_weight = sum(estimate_section_weight(sections[c]) for c in children)
                if total_weight >= 20:
                    step_groups[i] = {
                        "heading": sec["heading"],
                        "children": children,
                        "total_weight": total_weight,
                        "step_section": sec,
                    }

    # Also add large ## sections without children as standalone extraction candidates
    for i, sec in enumerate(sections):
        if (sec["level"] == 2
                and i not in step_groups
                and not is_critical_section(sec)
                and not is_frontmatter_or_preamble(sec, i)
                and estimate_section_weight(sec) >= 20):
            step_groups[i] = {
                "heading": sec["heading"],
                "children": [i],  # extract the section itself
                "total_weight": estimate_section_weight(sec),
                "step_section": sec,
                "self_extract": True,  # flag: extract whole section, not just children
            }

    # Sort step groups by total weight descending
    sorted_groups = sorted(step_groups.items(), key=lambda x: x[1]["total_weight"], reverse=True)

    # Extract the heaviest step groups until we've cut enough
    refs_dir = skill_dir / "references"
    extracted_indices = set()
    lines_cut = 0
    extractions = []

    for parent_idx, group in sorted_groups:
        if lines_cut >= lines_to_cut:
            break

        ref_filename = make_reference_filename(group["heading"])

        # Check for filename collision
        counter = 1
        base_name = ref_filename
        while any(e["filename"] == ref_filename for e in extractions):
            ref_filename = base_name.replace(".md", f"-{counter}.md")
            counter += 1

        # Build reference file content
        is_self = group.get("self_extract", False)
        if is_self:
            ref_content = f"# {group['heading']}\n\n{sections[parent_idx]['content']}"
        else:
            ref_lines = [f"# {group['heading']}\n\n"]
            for child_idx in group["children"]:
                ref_lines.append(sections[child_idx]["content"])
            ref_content = "".join(ref_lines)

        # Build the replacement pointer
        step_sec = group["step_section"]
        step_summary = step_sec["heading"]
        pointer = f"\n**Read:** `references/{ref_filename}` for detailed {step_summary.lower()} reference material.\n\n"

        if is_self:
            child_weight = estimate_section_weight(sections[parent_idx])
        else:
            child_weight = sum(estimate_section_weight(sections[c]) for c in group["children"])
        lines_cut += child_weight

        extractions.append({
            "filename": ref_filename,
            "content": ref_content,
            "parent_idx": parent_idx,
            "child_indices": group["children"],
            "pointer": pointer,
            "lines_saved": child_weight,
            "self_extract": is_self,
        })

        if is_self:
            # Don't add parent to extracted_indices — rebuild handles it via extraction check
            pass
        else:
            for ci in group["children"]:
                extracted_indices.add(ci)

    # If we still need to cut more, extract individual large subsections
    if lines_cut < lines_to_cut:
        for idx, score, weight in candidates:
            if lines_cut >= lines_to_cut:
                break
            if idx in extracted_indices:
                continue

            sec = sections[idx]
            ref_filename = make_reference_filename(sec["heading"])

            counter = 1
            base_name = ref_filename
            while any(e["filename"] == ref_filename for e in extractions):
                ref_filename = base_name.replace(".md", f"-{counter}.md")
                counter += 1

            ref_content = f"# {sec['heading']}\n\n{sec['content']}"
            pointer = f"\n**Read:** `references/{ref_filename}` for {sec['heading'].lower()} details.\n\n"

            extractions.append({
                "filename": ref_filename,
                "content": ref_content,
                "parent_idx": None,
                "child_indices": [idx],
                "pointer": pointer,
                "lines_saved": weight,
            })
            extracted_indices.add(idx)
            lines_cut += weight

    if not extractions:
        result["errors"].append("Could not identify extractable sections")
        result["final_lines"] = original_lines
        return result

    # Rebuild SKILL.md
    new_lines = []
    skip_until_level = None

    for i, sec in enumerate(sections):
        if i in extracted_indices:
            continue

        # Check if this is a parent STEP whose children were extracted
        extraction = next((e for e in extractions if e["parent_idx"] == i), None)
        if extraction:
            if extraction.get("self_extract", False) or (extraction["child_indices"] == [i]):
                # Self-extracted: replace whole section with just a pointer line
                heading_line = sec["lines"][0] if sec["lines"] else ""
                new_lines.append(heading_line)
                new_lines.append(extraction["pointer"])
            else:
                # Keep the heading line(s) but replace children with pointer
                new_lines.append(sec["content"])
                new_lines.append(extraction["pointer"])
            continue

        new_lines.append(sec["content"])

    new_content = "".join(new_lines)

    # Clean up excessive blank lines
    new_content = re.sub(r"\n{4,}", "\n\n\n", new_content)

    result["final_lines"] = len(new_content.splitlines())

    if dry_run:
        for ext in extractions:
            result["extracted_files"].append(ext["filename"])
        return result

    # Write reference files
    refs_dir.mkdir(exist_ok=True)
    for ext in extractions:
        ref_path = refs_dir / ext["filename"]
        # Don't overwrite existing reference files
        if ref_path.exists():
            ext["filename"] = ext["filename"].replace(".md", "-new.md")
            ref_path = refs_dir / ext["filename"]
        ref_path.write_text(ext["content"], encoding="utf-8")
        result["extracted_files"].append(ext["filename"])

    # Write updated SKILL.md
    skill_md.write_text(new_content, encoding="utf-8")

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract references from oversized skills")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be extracted without writing")
    parser.add_argument("--skill", type=str, help="Process a single skill by name")
    parser.add_argument("--threshold", type=int, default=500, help="Line threshold (default: 500)")
    parser.add_argument("--hub-root", type=str, default=".", help="Hub root directory")
    args = parser.parse_args()

    hub_root = Path(args.hub_root)
    skills_dir = hub_root / "core" / ".claude" / "skills"

    if not skills_dir.exists():
        print(f"ERROR: Skills directory not found: {skills_dir}")
        sys.exit(1)

    if args.skill:
        skill_dirs = [skills_dir / args.skill]
        if not skill_dirs[0].exists():
            print(f"ERROR: Skill not found: {args.skill}")
            sys.exit(1)
    else:
        skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists())

    mode = "DRY RUN" if args.dry_run else "EXTRACT"
    print(f"\n{'='*60}")
    print(f"  Reference Extraction ({mode})")
    print(f"  Threshold: {args.threshold} lines")
    print(f"{'='*60}\n")

    results = []
    for skill_dir in skill_dirs:
        result = extract_skill(skill_dir, args.threshold, args.dry_run)
        results.append(result)

        if result["skipped"]:
            continue

        status = "OK" if result["final_lines"] <= args.threshold else "STILL OVER"
        icon = "v" if status == "OK" else "!"

        if result["errors"]:
            print(f"  [{icon}] {result['skill_name']}: ERROR - {', '.join(result['errors'])}")
        elif result["extracted_files"]:
            print(f"  [{icon}] {result['skill_name']}: {result['original_lines']} -> {result['final_lines']} lines "
                  f"({len(result['extracted_files'])} files extracted) [{status}]")
        else:
            print(f"  [{icon}] {result['skill_name']}: {result['original_lines']} lines (nothing to extract)")

    # Summary
    processed = [r for r in results if not r["skipped"]]
    succeeded = [r for r in processed if r["final_lines"] <= args.threshold and not r["errors"]]
    still_over = [r for r in processed if r["final_lines"] > args.threshold and not r["errors"]]
    errored = [r for r in processed if r["errors"]]

    print(f"\n{'='*60}")
    print(f"  Summary: {len(succeeded)} succeeded, {len(still_over)} still over, {len(errored)} errors")
    print(f"  Total files extracted: {sum(len(r['extracted_files']) for r in processed)}")
    print(f"{'='*60}\n")

    if still_over:
        print("Still over threshold:")
        for r in still_over:
            print(f"  {r['skill_name']}: {r['final_lines']} lines")

    return 0 if not errored else 1


if __name__ == "__main__":
    sys.exit(main())
