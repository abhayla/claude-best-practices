# Sync Manifest Implementation Plan

## Problem

recommend.py --provision copies MISSING patterns but never updates EXISTING ones.
The current detect_improved_patterns() (line 889) cannot distinguish between:
- Hub updated, project untouched (safe to auto-update)
- Project customized the file (must not clobber)
- Both sides changed (conflict -- needs user decision)

## Solution

A manifest file at .claude/sync-manifest.json records SHA256 hashes of hub files
at sync time, creating the common ancestor for 3-way classification.

See the full plan details in the conversation thread -- this file is a summary.
