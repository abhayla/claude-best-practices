# STEP 6: Verify & Report

## STEP 6: Verify & Report

After any vault operation:

1. **Verify file exists** and is valid:
   ```bash
   # Check .md file
   test -f "$FILE_PATH" && echo "Created: $FILE_PATH"

   # Check .canvas file (must be valid JSON)
   python3 -c "import json; json.load(open('$FILE_PATH'))" 2>/dev/null && echo "Valid canvas"

   # Check .base file (must be valid YAML)
   python3 -c "import yaml; yaml.safe_load(open('$FILE_PATH'))" 2>/dev/null && echo "Valid base"
   ```

2. **Check wikilinks** resolve:
   ```bash
   # Extract wikilinks and verify targets exist
   grep -oP '\[\[([^\]|]+)' "$FILE_PATH" | sed 's/\[\[//' | while read link; do
     find "$VAULT_ROOT" -name "$link.md" -o -name "$link" | head -1 | \
       grep -q . || echo "Unresolved: [[$link]]"
   done
   ```

3. **Report:**
   ```
   Vault operation complete:
     Action: {{action}}
     File: {{path relative to vault root}}
     Type: {{.md | .canvas | .base}}
     Wikilinks: {{N total, M unresolved}}
     Size: {{line count or node count}}
   ```

---

