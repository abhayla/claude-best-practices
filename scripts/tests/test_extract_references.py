"""Tests for extract_references.py — focus on idempotency and no-orphan behavior."""

import textwrap
from pathlib import Path

import pytest

from scripts.extract_references import extract_skill


def _write_oversized_skill(skill_dir: Path, heading_count: int = 8) -> Path:
    """Create a synthetic SKILL.md over the threshold with several ## sections
    large enough to be extracted. Returns the SKILL.md path."""
    skill_dir.mkdir(parents=True, exist_ok=True)
    body_sections = []
    for i in range(heading_count):
        body_sections.append(
            f"## STEP {i + 1}: Section {i + 1}\n\n"
            + "\n".join([f"line {n} of section {i + 1} padding padding padding" for n in range(80)])
            + "\n"
        )
    content = textwrap.dedent("""\
        ---
        name: test-skill
        description: Oversized test skill for extraction testing.
        type: workflow
        allowed-tools: "Read"
        argument-hint: "<arg>"
        version: "1.0.0"
        ---

        # Test Skill

        Preamble text.

    """) + "\n".join(body_sections) + "\n## CRITICAL RULES\n- MUST do X\n"
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(content, encoding="utf-8")
    return skill_md


class TestExtractReferencesIdempotency:
    """Running extract twice on the same skill must not create orphan
    `-new.md` files. The prior behavior suffixed any pre-existing reference
    with `-new.md`, accumulating dead content on every re-run."""

    def test_re_extraction_does_not_create_new_suffix_orphans(self, tmp_path):
        skill_dir = tmp_path / "skills" / "my-skill"
        _write_oversized_skill(skill_dir)

        first = extract_skill(skill_dir, threshold=200)
        assert not first["errors"], first
        assert len(first["extracted_files"]) > 0

        refs_dir = skill_dir / "references"
        first_refs = sorted(p.name for p in refs_dir.iterdir())

        # Mutate SKILL.md back to an oversized state so re-extraction has work to do
        # (in real usage, the skill grows again over time; here we just reset it)
        _write_oversized_skill(skill_dir)

        second = extract_skill(skill_dir, threshold=200)
        assert not second["errors"], second

        second_refs = sorted(p.name for p in refs_dir.iterdir())

        # No `-new.md` suffix files — that was the bug we're fixing.
        assert not any("-new.md" in name for name in second_refs), (
            f"Re-extraction produced -new.md orphan files: {second_refs}"
        )
        # The set of reference files is the same (idempotent), not a superset.
        assert set(second_refs) == set(first_refs), (
            f"Re-extraction changed the reference-file set.\n"
            f"First:  {first_refs}\nSecond: {second_refs}"
        )

    def test_re_extraction_preserves_reference_content(self, tmp_path):
        """Running extract again with the same skill body must leave the
        existing reference files byte-identical (true idempotency)."""
        skill_dir = tmp_path / "skills" / "my-skill"
        _write_oversized_skill(skill_dir)

        extract_skill(skill_dir, threshold=200)
        refs_dir = skill_dir / "references"
        before = {p.name: p.read_text(encoding="utf-8") for p in refs_dir.iterdir()}

        _write_oversized_skill(skill_dir)
        extract_skill(skill_dir, threshold=200)

        after = {p.name: p.read_text(encoding="utf-8") for p in refs_dir.iterdir()}

        assert before == after, (
            "Reference file contents should be identical across re-extractions "
            "(no mutation, no -new.md variants)"
        )
