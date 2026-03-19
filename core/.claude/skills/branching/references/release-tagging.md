# Release Tagging

If this merge completes a milestone or the team follows release-on-merge practices,
handle version tagging.

## Determine if a Release Tag is Needed

```bash
# Check if the PR has a release-related label
RELEASE_LABEL=$(gh pr view "$PR_NUMBER" --json labels --jq '
  [.labels[].name] | map(select(test("release|version|milestone"))) | first // empty
')

# Check if the project has existing tags
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
echo "Latest tag: $LATEST_TAG"
echo "Release label: ${RELEASE_LABEL:-none}"
```

## Suggest Semantic Version

Based on the type of changes in the PR, suggest the appropriate version bump:

| Change Type | Version Bump | Example |
|-------------|-------------|---------|
| Breaking changes (`BREAKING CHANGE`, `remove:`) | Major | v1.0.0 -> v2.0.0 |
| New features (`feat:`) | Minor | v1.0.0 -> v1.1.0 |
| Bug fixes, patches (`fix:`, `perf:`) | Patch | v1.0.0 -> v1.0.1 |

```bash
if [ "$LATEST_TAG" != "none" ]; then
  # Parse the current version
  MAJOR=$(echo "$LATEST_TAG" | sed 's/v//' | cut -d. -f1)
  MINOR=$(echo "$LATEST_TAG" | sed 's/v//' | cut -d. -f2)
  PATCH=$(echo "$LATEST_TAG" | sed 's/v//' | cut -d. -f3)

  # Determine bump type from PR title
  if echo "$PR_TITLE" | grep -qi 'BREAKING\|remove'; then
    NEW_TAG="v$((MAJOR + 1)).0.0"
    BUMP="major"
  elif echo "$PR_TITLE" | grep -qi '^feat'; then
    NEW_TAG="v${MAJOR}.$((MINOR + 1)).0"
    BUMP="minor"
  else
    NEW_TAG="v${MAJOR}.${MINOR}.$((PATCH + 1))"
    BUMP="patch"
  fi

  echo "Suggested version: $NEW_TAG ($BUMP bump from $LATEST_TAG)"
fi
```

## Create and Push the Tag

Only proceed if the user confirms the release tag is appropriate.

```bash
# Create an annotated tag
git tag -a "$NEW_TAG" -m "Release $NEW_TAG

Changes in this release:
$(git log "$LATEST_TAG..HEAD" --oneline --no-decorate)
"

# Push the tag
git push origin "$NEW_TAG"
echo "Tag $NEW_TAG created and pushed."
```

## Generate Release Notes

```bash
# Create a GitHub release with auto-generated notes
gh release create "$NEW_TAG" \
  --title "$NEW_TAG" \
  --generate-notes \
  --latest

echo "GitHub release created: $NEW_TAG"
```
