# 6.4 Handle Verification Failures

### 6.4 Handle Verification Failures

If tests or build fail after the merge:

```
POST-MERGE FAILURE DETECTED

Failed step: <tests|build>
Error output:
<error details>

IMMEDIATE ACTIONS:
1. Do NOT panic — this is why we documented the rollback plan.
2. Investigate whether the failure is caused by the merge or pre-existing.
3. If caused by the merge, revert immediately:

   git revert -m 1 <MERGE_SHA>
   git push origin <BASE_BRANCH>

4. If pre-existing, file a separate issue and proceed.
```

