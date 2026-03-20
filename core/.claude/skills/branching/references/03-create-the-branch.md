# 0.3 Create the Branch

### 0.3 Create the Branch

```bash
BRANCH_NAME="<prefix>/<descriptive-name>"
BASE_BRANCH=$(git branch --show-current)

git checkout -b "$BRANCH_NAME"
echo "Created branch: $BRANCH_NAME (from $BASE_BRANCH)"
```

