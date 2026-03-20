# Revert command (if needed):

### Revert command (if needed):
\`\`\`bash
git checkout $BASE_BRANCH && git pull
git revert -m 1 $MERGE_SHA
git push origin $BASE_BRANCH
\`\`\`
EOF
)"
```

---

