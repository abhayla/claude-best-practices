# 3.4 Insert into CHANGELOG.md

### 3.4 Insert into CHANGELOG.md

If a `CHANGELOG.md` exists, insert the entry under the appropriate section. If the
`[Unreleased]` section does not have the right category, create it.

```bash
if [ -f CHANGELOG.md ]; then
  # Check if [Unreleased] section exists
  if grep -q '## \[Unreleased\]' CHANGELOG.md; then
    # Check if the category subsection exists under [Unreleased]
    if grep -A 50 '## \[Unreleased\]' CHANGELOG.md | grep -q "### $CATEGORY"; then
      # Insert after the category header
      sed -i "/### $CATEGORY/a\\$CHANGELOG_ENTRY" CHANGELOG.md
    else
      # Add the category section under [Unreleased]
      sed -i "/## \[Unreleased\]/a\\\n### $CATEGORY\n$CHANGELOG_ENTRY" CHANGELOG.md
    fi
  else
    # Add [Unreleased] section at the top (after the title)
    sed -i "1a\\\n## [Unreleased]\n\n### $CATEGORY\n$CHANGELOG_ENTRY" CHANGELOG.md
  fi

  echo "Changelog updated with entry under [$CATEGORY]"
  git add CHANGELOG.md
  git commit -m "docs: add changelog entry for PR #$PR_NUMBER"
else
  echo "No CHANGELOG.md found — skipping changelog generation."
  echo "To start a changelog, create CHANGELOG.md following https://keepachangelog.com"
fi
```

