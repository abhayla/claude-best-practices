# STEP 6: Output Format Selection

### JSON Output Structure

```json
{
  "report_version": "1.0.0",
  "generated_at": "2026-03-13T01:15:00Z",
  "scan_summary": {
    "sources_scanned": 7,
    "by_platform": {"github": 3, "reddit": 2, "twitter": 2},
    "total_discovered": 12,
    "by_type": {"skill": 8, "agent": 2, "rule": 1, "hook": 1}
  },
  "classifications": {
    "new": [
      {
        "name": "kotlin-coroutine-debug",
        "type": "skill",
        "source": "https://github.com/...",
        "platform": "github",
        "description": "...",
        "tags": ["android", "kotlin"],
        "stack_fit": ["android-compose"],
        "priority": 1
      }
    ],
    "exact_duplicates": [...],
    "structural_overlaps": [
      {
        "discovered": "android-run-tests",
        "hub_pattern": "android-run-tests",
        "overlap_score": 5,
        "verdict": "MERGE",
        "unique_to_discovered": ["..."],
        "unique_to_hub": ["..."],
        "comparison_scores": {
          "completeness": {"discovered": 7, "hub": 5},
          "specificity": {"discovered": 8, "hub": 6},
          "recency": {"discovered": 9, "hub": 7},
          "error_handling": {"discovered": 6, "hub": 8},
          "documentation": {"discovered": 5, "hub": 7},
          "community": {"discovered": 8, "hub": null}
        }
      }
    ],
    "functional_overlaps": [...],
    "replacements": [
      {
        "hub_pattern": "compose-ui",
        "replacement": "compose-ui-v2",
        "score_delta": 0.7,
        "verdict": "REPLACE",
        "risks": ["..."],
        "migration_path": ["..."]
      }
    ]
  },
  "stack_coverage": {
    "android-compose": {
      "covered": ["unit testing", "UI testing", ...],
      "upgraded": ["unit testing"],
      "new_coverage": ["gradle optimization", "coroutine debugging"],
      "open_gaps": ["ProGuard/R8", "baseline profiles"]
    }
  },
  "actions": {
    "import_now": [...],
    "merge": [...],
    "replace": [...],
    "evaluate": [...],
    "skip": [...],
    "remaining_gaps": [...]
  },
  "source_quality": [
    {
      "source": "https://github.com/...",
      "patterns_found": 5,
      "quality": "high",
      "recommendation": "add_to_watchlist"
    }
  ]
}
```

### PR Comment Format (Condensed)

```markdown
