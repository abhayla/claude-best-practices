# T-320 HIGH-4 repro: batch `cd /d` failure semantics

Run on this host with a real cmd.exe (Windows Server 2022):

```bat
@echo off
cd /d C:\Abhay\GetWorkDone
echo BEFORE cwd=%CD%
cd /d C:\NoSuchPath\Nope\Missing
echo AFTER  cwd=%CD%  errorlevel=%errorlevel%
echo SCRIPT CONTINUED
```

Output:

```
BEFORE cwd=C:\Abhay\GetWorkDone
The system cannot find the path specified.
AFTER  cwd=C:\Abhay\GetWorkDone  errorlevel=1
SCRIPT CONTINUED
```

Three facts this establishes, all load-bearing for keeper-tick.cmd:26/:212/:256:

1. a failed `cd /d` DOES set errorlevel 1 — the signal exists and is simply discarded;
2. it does NOT abort the script — execution continues to the git commands below;
3. the working directory is UNCHANGED — so those git commands mutate the PREVIOUS repository.

Combined: `git add -A` / `git commit` / `git push` after an unchecked failed chdir commit and push
the wrong repo, while the tick's own guards (HEAD-is-main, commit-message match) all still pass.
