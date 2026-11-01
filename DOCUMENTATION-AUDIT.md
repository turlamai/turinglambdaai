# Product documentation audit — 2026-11-01

This is a **point-in-time source audit**, not a claim of live-website deployment, clean-machine acceptance, or feature completeness. Apply [DOCUMENTATION-POLICY.md](DOCUMENTATION-POLICY.md) for editorial decisions.

## Scope and interpretation

- The GitHub owner listing contains 100 repositories, including libraries, forks/upstream projects, configuration, historical code and archived projects. Do **not** rewrite unrelated upstream documentation or remove required attribution merely because a third-party name appears.
- First-party product READMEs and their available Chinese counterparts were examined in batches. Some repositories have no root README. Technical platform/dependency references and factual integrations remain necessary.
- The public website source is split between `docs/index.html` and `site/index.html`, depending on the product. Detailed manuals likewise exist in `docs/manual.html`, `docs/guide.html` and `site/guide.html`. A missing file at one path does **not** prove the site or guide does not exist.
- Only the main public entry points listed below underwent systematic source-level checks for link-owner migration, screenshot dependence, fragment navigation and (where applicable) inline JavaScript syntax. The full repository tree and every deployment endpoint were **not** exhaustively crawled.

## Principal public pages reviewed

| Site source path | Products |
| --- | --- |
| `docs/index.html` | Taskly, Booklight, MoveBit, Autarx, RegexMate, SyncPilot, Glaze, HackDigest, gPTP Studio, Publy |
| `site/index.html` | Fulcrum, PodLens, Payback, Permit, Flashpilot, RelayPilot, Keel, Pitboard, Keyward, Threadly |
| `docs/manual.html` | Taskly, MoveBit |
| `docs/guide.html` | Booklight, SyncPilot, HackDigest, Autarx, RegexMate |
| `site/guide.html` | Fulcrum, PodLens, Payback, Keyward, Threadly |

Other repositories assessed at README level include Rivet, Commerce, Shuttle, FileBoundary, Sonar, Switchboard and embedded/Racket libraries. Their documentation should retain names required for standards, supported third-party integrations, build instructions and licenses.

## Changes implemented

- Replace unnecessary competitor comparison tables and nonessential promotion with product purpose, architecture, shipped behavior and known limitations.
- Replace dated screenshots in the main guides/pages with task-focused instructions, observable expected results and troubleshooting.
- Preserve actual tool integrations, necessary ownership statements and technical screenshot **capture** APIs used for automated testing.
- Repair obsolete owner URLs in primary public docs after the GitHub username migration.
- Fix missing Chinese and English MoveBit guide strings for cancellation during update download.
- Keep code-oriented diagrams, logos, release badges and security warnings where helpful; a ban on all images or brand names would be counterproductive.

## Source-only checks performed

- HTML section opening/closing counts and local `#anchor` link targets were checked in the principal pages.
- Inline executable JavaScript in 12 primary public pages and 11 detailed HTML guides compiled without syntax errors when skipping JSON-LD and other non-executable script types. This is a **syntax** check only, not a browser runtime test.
- Taskly's separately loaded `docs/script.js` dictionary contains the homepage's statically referenced `data-i18n` keys in both languages.
- Remaining image references in detailed guides were assessed by purpose; for example, a favicon is not an obsolete UI screenshot.

## Pending acceptance — DO NOT mark complete without evidence

1. **Deployed website:** Open each actual public URL in a browser and verify both languages, responsive layout, in-page navigation, download/help links and that published content corresponds to main. Website access was unavailable in the audit environment; source changes and merged PRs alone do not verify Pages deployment.
2. **Product behavior:** Test user-guide tasks against the released application for each supported OS and installation shape, including failure/recovery behavior. A text-first guide can still be wrong even when no screenshots remain.
3. **Link targets:** Crawl all relative/absolute documentation links, images, and downloadable assets across the site trees; root entry points and sampled links do not constitute an exhaustive crawler.
4. **CI/release evidence:** Check each change's required GitHub Actions results and any Pages deployment logs before certifying site health. A successful GitHub merge is not itself a release or publishing guarantee.
5. **Future drift:** When UI workflows change, update stable labels, expected outcomes, accessibility terms, platform notes, bilingual copy, and recovery instructions together. Review genuine dependencies individually rather than automatically deleting brand names.

## Maintenance rule

For every future product documentation change: run semantic editorial review under the policy, inspect the actual site/guide paths, verify both languages and navigation, check links, and test at least one observable user task. Treat this document as an audit ledger; append dated evidence instead of retroactively changing historical results.
