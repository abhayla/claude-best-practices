"""Recommend hub Claude resources for a project based on stack detection and gap analysis.

Usage:
    # Report only (remote repo)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name

    # Report only (local directory)
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project

    # Apply recommendations via PR (remote repo)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --apply

    # Apply recommendations locally (copy files)
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project --apply

    # Provision project (apply + CLAUDE.md + settings.json)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --provision
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project --provision

    # Use stacks from repos.yml instead of auto-detection
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --use-config

    # Compare content of overlapping resources (detect divergence)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --diff
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project --diff

This module is a thin CLI entry point. Implementation lives in focused sibling
modules (dependency_detection, stack_detection, hub_resources, provisioning_tiers,
gap_analysis, sync_manifest, resource_copy, provision_local, provision_repo,
overlap_analysis, plugin_recommendations); everything is re-exported here for
backward compatibility with existing `from scripts.recommend import X` call sites.
"""

import argparse
import json
from pathlib import Path

from scripts.third_party_skills import (
    format_install_results,
    format_recommendations,
    resolve_skills as resolve_third_party_skills,
    try_install as try_install_third_party,
)
from scripts.dependency_detection import (
    STACK_DETECTORS,
    DEP_PATTERN_MAP,
    _DEP_SUBDIRS,
    _parse_package_json,
    _parse_requirements_txt,
    _parse_pyproject_toml,
    _parse_build_gradle,
    _parse_pubspec_yaml,
    _parse_cargo_toml,
    _parse_go_mod,
    _parse_gemfile,
    _DEP_FILE_PARSERS,
    detect_dependencies_from_dir,
    detect_dependencies_from_repo,
    resolve_dep_patterns,
)
from scripts.plugin_recommendations import (
    load_plugin_recommendations,
    recommend_plugins,
    print_plugin_recommendations,
)
from scripts.provisioning_tiers import (
    MUST_HAVE_HOOKS,
    CORE_WORKFLOW_SKILLS,
    MUST_HAVE_UNIVERSAL_SKILLS,
    NICE_TO_HAVE_UNIVERSAL_SKILLS,
    MUST_HAVE_RULES,
    MUST_HAVE_AGENTS,
    ALWAYS_SKIP,
    NICE_TO_HAVE_STACK_OVERRIDES,
    RESOURCE_STACK_REQUIREMENTS,
    _load_tier_registry,
    tier_resource,
    effectiveness_tier_adjustment,
    tier_resource_with_reason,
)
from scripts.stack_detection import (
    detect_stacks_from_dir,
    detect_stacks_from_repo,
    get_stacks_from_config,
)
from scripts.hub_resources import (
    get_hub_resources,
    get_project_resource_names,
    get_project_resources_from_repo,
    is_stack_specific,
    matches_stacks,
    name_matches_existing,
)
from scripts.sync_manifest import (
    _compute_file_hash,
    classify_sync_status,
    load_sync_manifest,
    save_sync_manifest,
    build_sync_classification,
    _resolve_resource_files,
    update_improved_to_local,
    update_manifest_after_sync,
)
from scripts.gap_analysis import (
    analyze_gaps,
    _parse_frontmatter_version,
    _version_gt,
    detect_improved_patterns,
    format_report,
)
from scripts.resource_copy import (
    _copy_if_changed,
    RUNTIME_IGNORE_ENTRIES,
    _RUNTIME_IGNORE_HEADER,
    _ensure_runtime_gitignore,
    _resource_copy_units,
    _existing_pattern_names,
    _provision_dependency_closure,
    _workflow_entry_skills,
)
from scripts.provision_local import (
    apply_to_local,
    PROVISION_START_MARKER,
    PROVISION_END_MARKER,
    get_rule_descriptions,
    generate_hub_practices_section,
    reconcile_claude_md_rules,
    provision_claude_md,
    provision_claude_local_md,
    deep_merge_settings,
    referenced_hook_basenames,
    _deliver_referenced_hooks,
    provision_settings_json,
    _resolve_conflict_mode,
    provision_to_local,
    _copy_resources_for_tier,
)
from scripts.provision_repo import (
    apply_to_repo,
    _format_nice_to_have_pr_body,
    _create_tier_branch_and_pr,
    provision_to_repo_multi_pr,
    provision_to_repo,
)
from scripts.overlap_analysis import (
    _resolve_hub_path,
    _resolve_project_path,
    _find_matching_project_name,
    _compute_line_overlap,
    classify_divergence,
    analyze_overlaps_local,
    analyze_overlaps_repo,
    format_diff_report,
    format_divergence_table,
)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Recommend Claude resources for a project based on tech stack analysis"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo", help="GitHub repo (owner/name)")
    group.add_argument("--local", help="Local project directory path")

    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--apply", action="store_true",
                              help="Apply recommendations (copy files or create PR)")
    action_group.add_argument("--provision", action="store_true",
                              help="Provision project (apply + CLAUDE.md + settings.json)")
    parser.add_argument("--tier", choices=["must-have", "nice-to-have"],
                        default="must-have",
                        help="Minimum tier to apply (default: must-have)")
    parser.add_argument("--workflows", default=None,
                        help="Comma-separated workflow orchestrators to provision "
                             "(e.g. development-loop,debugging-loop). Only these "
                             "workflow ORCHESTRATORS are copied among the workflows; "
                             "the others are skipped. Each selected workflow's full "
                             "closure travels (shared resources included). Standalone "
                             "must-have patterns still provision on their own merit. "
                             "Omit to provision all workflows.")
    parser.add_argument("--on-conflict",
                        choices=["auto", "skip", "overwrite", "error", "interactive"],
                        default="auto",
                        help="How to handle files changed in both hub and project "
                             "(default: auto — interactive if TTY, skip if not)")
    parser.add_argument("--use-config", action="store_true",
                        help="Use stacks from config/repos.yml instead of auto-detection")
    parser.add_argument("--diff", action="store_true",
                        help="Compare content of overlapping resources to detect divergence")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON")
    parser.add_argument("--multi-pr", action="store_true", dest="multi_pr",
                        default=True,
                        help="Create separate PRs per tier (default for --provision)")
    parser.add_argument("--single-pr", action="store_false", dest="multi_pr",
                        help="Create a single PR for all tiers (legacy behavior)")
    parser.add_argument("--skip-third-party", action="store_true",
                        help="Skip third-party skill recommendations and installation")
    return parser


def _detect_stacks_and_deps(args, hub_root):
    """Step 1: stacks. Step 1b: dependencies. Step 1c/1d: third-party + plugin recs."""
    stacks = None
    if args.use_config and args.repo:
        config_path = hub_root / "config" / "repos.yml"
        stacks = get_stacks_from_config(args.repo, config_path)
        if stacks:
            print(f"Stacks from config: {', '.join(stacks)}")
        else:
            print(f"Repo '{args.repo}' not found in config/repos.yml, falling back to auto-detection")

    if stacks is None:
        if args.local:
            stacks = detect_stacks_from_dir(Path(args.local))
        else:
            stacks = detect_stacks_from_repo(args.repo)
        print(f"Auto-detected stacks: {', '.join(stacks) if stacks else 'none'}")

    if args.local:
        deps = detect_dependencies_from_dir(Path(args.local))
    else:
        deps = detect_dependencies_from_repo(args.repo)
    dep_promoted = resolve_dep_patterns(deps)
    if dep_promoted:
        print(f"Dependency-promoted patterns: {', '.join(sorted(dep_promoted))}")

    third_party_matched = []
    if not args.skip_third_party:
        project_dir = Path(args.local) if args.local else None
        third_party_matched = resolve_third_party_skills(deps, project_dir, hub_root)
        if third_party_matched:
            names = [e.get("skill", e.get("repo", "").split("/")[-1]) for e in third_party_matched]
            print(f"Third-party skills matched: {', '.join(names)}")

    plugin_rec = recommend_plugins(
        stacks, deps, load_plugin_recommendations(hub_root / "config" / "plugin-recommendations.yml")
    )
    print_plugin_recommendations(plugin_rec)

    return stacks, deps, third_party_matched


def _compute_gaps(args, hub_root, stacks, deps):
    """Step 2: project resources. Step 3: hub resources. Step 4/4b: gap analysis."""
    if args.local:
        project_names = get_project_resource_names(Path(args.local) / ".claude")
    else:
        project_names = get_project_resources_from_repo(args.repo)

    existing_count = sum(len(v) for v in project_names.values())
    print(f"Project has {existing_count} existing resources")

    hub_resources = get_hub_resources(hub_root)

    _load_tier_registry(hub_root)  # Prime the cache before gap analysis
    gaps = analyze_gaps(hub_resources, project_names, stacks, deps)

    registry_path = hub_root / "registry" / "patterns.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        project_claude_dir = (
            Path(args.local) / ".claude" if args.local
            else None  # Remote mode handled separately
        )
        if project_claude_dir and project_claude_dir.exists():
            improved = detect_improved_patterns(
                hub_root, project_claude_dir, hub_resources, project_names, registry,
            )
            gaps["improved"] = [
                {"name": i["name"], "type": i["type"], "tier": "improved",
                 "reason": i["reason"]}
                for i in improved
            ]

    return gaps, project_names, hub_resources


def _output_gap_report(args, gaps, stacks, project_names, hub_resources, third_party_matched):
    """Step 5: output the gap report (JSON or text), deferring JSON when --provision is set."""
    if args.json_output and not args.provision:
        output = gaps
        if third_party_matched:
            output = dict(gaps)
            output["third_party_skills"] = [
                {"repo": e.get("repo"), "skill": e.get("skill", ""),
                 "match_reason": e.get("match_reason", "")}
                for e in third_party_matched
            ]
        print(json.dumps(output, indent=2))
    elif not args.json_output:
        report = format_report(gaps, stacks, project_names, hub_resources)
        print()
        print(report)
        # Append third-party recommendations
        if third_party_matched:
            print(format_recommendations(third_party_matched))


def _run_apply(args, hub_root, gaps, select_workflows):
    """Step 6: apply recommendations (copy files locally or create a PR remotely)."""
    print(f"\nApplying {args.tier} tier recommendations...")
    if args.local:
        copied = apply_to_local(hub_root, Path(args.local), gaps, args.tier,
                                select_workflows=select_workflows)
        print(f"Copied {len(copied)} files to {args.local}/.claude/")
        for f in copied:
            print(f"  + {f}")
    else:
        pr_url = apply_to_repo(hub_root, args.repo, gaps, args.tier)
        if pr_url:
            print(f"PR created: {pr_url}")


def _run_provision(args, hub_root, gaps, stacks, hub_resources, project_names,
                    third_party_matched, select_workflows):
    """Step 6b: provision (apply + CLAUDE.md + settings.json) and print the summary."""
    action_labels = {
        "must-have": "add (new)",
        "improved": "upgrade (hub newer)",
        "nice-to-have": "optional",
        "skip": "skip",
    }
    pr_urls = {}
    provision_summary = None
    summary = None

    if args.local:
        summary = provision_to_local(
            hub_root, Path(args.local), gaps, stacks, args.tier,
            on_conflict=args.on_conflict, select_workflows=select_workflows,
        )
        # Install third-party skills after hub patterns are copied
        if third_party_matched:
            tp_results = try_install_third_party(Path(args.local), third_party_matched)
            summary["third_party_skills"] = tp_results
        provision_summary = summary
    elif getattr(args, "multi_pr", True):
        pr_urls = provision_to_repo_multi_pr(
            hub_root, args.repo, gaps, stacks,
            hub_resources, project_names,
        )
    else:
        pr_url = provision_to_repo(
            hub_root, args.repo, gaps, stacks,
            hub_resources, project_names, args.tier,
        )
        if pr_url:
            pr_urls = {"all": pr_url}

    # Combined JSON output when both --provision and --json are set
    if args.json_output:
        combined = {"gaps": gaps, "provision": provision_summary or {}}
        print(json.dumps(combined, indent=2))
    else:
        # --- Print detailed summary ---
        print()
        print("=" * 100)
        print("PROVISION SUMMARY")
        print("=" * 100)

        for tier_name in ("must-have", "improved", "nice-to-have", "skip"):
            items = gaps.get(tier_name, [])
            if not items:
                continue
            action = action_labels.get(tier_name, tier_name)
            print(f"\n--- {tier_name.upper()} ({len(items)}) ---")
            print(f"  {'Type':<8s} {'Name':<40s} {'Action':<22s} {'Reason'}")
            print(f"  {'----':<8s} {'----':<40s} {'------':<22s} {'------'}")
            for item in sorted(items, key=lambda x: (x["type"], x["name"])):
                reason = item.get("reason", "")
                print(f"  {item['type']:<8s} {item['name']:<40s} {action:<22s} {reason}")

        # Third-party skills
        if third_party_matched:
            print(format_recommendations(third_party_matched))
            if args.local and summary.get("third_party_skills"):
                print(format_install_results(summary["third_party_skills"]))

        # Config files (local mode)
        if args.local:
            print(f"\n--- CONFIG ---")
            print(f"  CLAUDE.md:     {summary['claude_md']}")
            print(f"  settings.json: {summary['settings_json']}")
            print(f"\n  Files copied: {len(summary['copied_files'])}")

        # PRs (remote mode)
        if pr_urls:
            print(f"\n--- PRs CREATED ---")
            pr_action_hints = {
                "must-have": "merge confidently",
                "improved": "review diffs",
                "nice-to-have": "check boxes, comment /apply",
                "all": "review and merge",
            }
            for tier_name, url in pr_urls.items():
                if url:
                    hint = pr_action_hints.get(tier_name, "")
                    print(f"  {tier_name:<14s} {url} ({hint})")
                else:
                    print(f"  {tier_name:<14s} (skipped)")

        # Totals
        print()
        total_must = len(gaps.get("must-have", []))
        total_imp = len(gaps.get("improved", []))
        total_nice = len(gaps.get("nice-to-have", []))
        total_skip = len(gaps.get("skip", []))
        print(f"TOTAL: {total_must} must-have, {total_imp} improved, "
              f"{total_nice} nice-to-have, {total_skip} skip")
        print("=" * 100)


def _run_diff(args, hub_root, hub_resources, project_names):
    """Step 7: diff overlapping resources if requested."""
    print("\nAnalyzing content divergence for overlapping resources...")
    if args.local:
        overlaps = analyze_overlaps_local(
            hub_root, Path(args.local), hub_resources, project_names
        )
    else:
        overlaps = analyze_overlaps_repo(
            hub_root, args.repo, hub_resources, project_names
        )

    if args.json_output:
        # Strip non-serializable fields
        print(json.dumps(overlaps, indent=2))
    else:
        diff_report = format_diff_report(overlaps)
        print()
        print(diff_report)


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    hub_root = Path(__file__).parent.parent

    stacks, deps, third_party_matched = _detect_stacks_and_deps(args, hub_root)
    gaps, project_names, hub_resources = _compute_gaps(args, hub_root, stacks, deps)
    _output_gap_report(args, gaps, stacks, project_names, hub_resources, third_party_matched)

    # Parse optional workflow selection (subset provisioning).
    select_workflows = None
    if getattr(args, "workflows", None):
        select_workflows = {w.strip() for w in args.workflows.split(",") if w.strip()}

    if args.apply:
        _run_apply(args, hub_root, gaps, select_workflows)

    if args.provision:
        _run_provision(args, hub_root, gaps, stacks, hub_resources, project_names,
                        third_party_matched, select_workflows)

    if args.diff:
        _run_diff(args, hub_root, hub_resources, project_names)


if __name__ == "__main__":
    main()
