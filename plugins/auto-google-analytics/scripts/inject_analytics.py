#!/usr/bin/env python3
"""Inject the GA4 gtag + Consent Mode v2 + blanket ui_click snippet into static HTML.

Productization of the proven hub injector. Handles the autonomous, reversible case:
static HTML files (a webroot index.html, a built `dist/`, an exported static site). For
FRAMEWORK source (Next.js `<head>`/`app/layout`, Nuxt config, Astro/Svelte layout) the
auto-google-analytics SKILL performs the framework-specific edit — this script is the static path.

Safe by construction: writes a `<file>.pre-ga.bak` before changing anything, is idempotent
(skips a file already tagged with this ID or any gtag), and supports --dry-run.

Usage:
  inject_analytics.py --id G-XXXXXXX --file path/to/index.html [--file ...]
  inject_analytics.py --id G-XXXXXXX --webroot ./dist          # all *.html under a root
  inject_analytics.py --from-inventory .claude/analytics-inventory.json --webroot ./dist
                      # picks the single measurement_id from the inventory
Exit codes: 0 ok (incl. nothing-to-do); 2 config error.
"""
import argparse
import json
import os
import sys

SNIP = (
    '<!-- Google Analytics 4 (gtag) + Consent Mode v2 + blanket click tracking '
    '(auto-google-analytics plugin) -->\n'
    "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
    # analytics_storage GRANTED by default so GA4 actually collects (Abhay's
    # sites are India-focused — no GDPR; pair with a privacy-policy line). Leaving
    # it 'denied' with no consent-grant silently records ~0 (the 2026-06-29 bug).
    # Ad-storage stays denied. For an EU audience, switch to 'denied' + a consent banner.
    "gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',"
    "ad_personalization:'denied',analytics_storage:'granted',wait_for_update:500});"
    "gtag('js',new Date());gtag('config','__GA__');</script>\n"
    '<script async src="https://www.googletagmanager.com/gtag/js?id=__GA__"></script>\n'
    "<script>document.addEventListener('click',function(e){"
    "var el=e.target.closest('[data-track],a,button,[role=\"button\"]');if(!el)return;"
    "gtag('event','ui_click',{interaction_id:el.getAttribute('data-track')||null,"
    "link_text:(el.textContent||'').trim().slice(0,100),"
    "link_url:el.getAttribute('href')||null,element_id:el.id||null,"
    "page_section:el.getAttribute('data-section')||null});},{capture:true});</script>"
)


def _die(msg):
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(2)


def id_from_inventory(path):
    if not os.path.exists(path):
        _die(f"INVENTORY_MISSING: {path}")
    with open(path, encoding="utf-8") as f:
        sites = json.load(f).get("sites", {})
    ids = sorted({v.get("measurement_id") for v in sites.values() if v.get("measurement_id")})
    if len(ids) != 1:
        _die(f"INVENTORY_AMBIGUOUS: expected exactly 1 measurement_id, found {ids}. "
             "Pass --id explicitly.")
    return ids[0]


def collect_files(files, webroot):
    paths = list(files)
    if webroot:
        for root, _dirs, names in os.walk(webroot):
            paths += [os.path.join(root, n) for n in names if n.lower().endswith(".html")]
    return sorted(set(paths))


def inject_one(path, gid, dry_run):
    if not os.path.exists(path):
        return "MISSING", path
    html = open(path, encoding="utf-8").read()
    if gid in html or "googletagmanager.com/gtag" in html:
        return "SKIP-already-tagged", path
    i = html.lower().find("<head>")
    if i == -1:
        return "NO-HEAD", path
    i += len("<head>")
    new = html[:i] + "\n" + SNIP.replace("__GA__", gid) + html[i:]
    if dry_run:
        return "WOULD-INJECT", path
    open(path + ".pre-ga.bak", "w", encoding="utf-8").write(html)  # rollback backup
    open(path, "w", encoding="utf-8").write(new)
    return "INJECTED", path


def main():
    ap = argparse.ArgumentParser(description="Inject GA4 gtag snippet into static HTML.")
    ap.add_argument("--id", default="")
    ap.add_argument("--from-inventory", default="")
    ap.add_argument("--file", action="append", default=[])
    ap.add_argument("--webroot", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    gid = args.id or (id_from_inventory(args.from_inventory) if args.from_inventory else "")
    if not gid:
        _die("NO_MEASUREMENT_ID: pass --id G-XXXXXXX or --from-inventory <path>.")
    if not gid.startswith("G-"):
        _die(f"BAD_MEASUREMENT_ID '{gid}': expected a GA4 'G-...' id.")

    targets = collect_files(args.file, args.webroot)
    if not targets:
        _die("NO_TARGETS: pass --file <html> (repeatable) and/or --webroot <dir>.")

    counts = {}
    for path in targets:
        status, p = inject_one(path, gid, args.dry_run)
        counts[status] = counts.get(status, 0) + 1
        print(f"{status}\t{p}")
    print("\n# " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
