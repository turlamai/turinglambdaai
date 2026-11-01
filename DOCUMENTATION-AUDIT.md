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


## Follow-up validation — 2026-11-01 (second pass)

### Repository-wide README scan

- Enumerated all **100 owner-visible repositories** and attempted a targeted source-text scan of each root `README.md` for legacy GitHub owner URLs, obvious unsolicited competitor-promotion phrases and embedded UI screenshot references.
- **94 root READMEs were readable**. Six returned `NOT_FOUND` for the root file: `apply`, `graphics`, `hackdigest-server`, `racket-base64`, `racket-binary-search`, `racket-checkers`. Missing root READMEs do not imply missing documentation elsewhere.
- The scan detected legacy owner URLs in **four archived repositories**: `deployer`, `makefile-template`, `octocrawler`, `simple`. `simple` also contains an archived theme screenshot. These are documented archival exceptions, **not** evidence that all history should be rewritten. No newly flagged unnecessary competitor pitch appeared in the targeted root-README patterns.
- This was a **pattern-based scan**, not human semantic proofreading of all 100 repositories, and does not cover non-README files throughout all project trees.

### Navigation and local resources

- Reviewed homepage local resource references for **19 first-party site entry points**, attempting to resolve **37** HTML/CSS/JavaScript/image paths: **34 text resources were retrieved**, **two binary images** (`booklight/docs/assets/favicon.png`, `syncpilot/docs/icon.png`) could not be decoded by the text-only GitHub file reader, and one missing HTML manual target was confirmed. The binary decode failures are **not** proof of missing assets.
- Fixed the missing FlashPilot navigation destination in [flashpilot#24](https://github.com/turlamai/flashpilot/pull/24): `site/guide.html` did not exist, so the nav now routes to verified English/Chinese `docs/USER-GUIDE` files according to language choice.
- Checked cross-page `index.html#fragment` links from **12 detailed HTML manuals** to their parent homepages. Fixed a broken Taskly manual `#download` target in [taskly#97](https://github.com/turlamai/taskly/pull/97), linking to the existing `#release` section instead. No other missing cross-page fragment targets were found in that checked set.
- Removed the remaining obsolete Payback homepage screenshot in [payback#46](https://github.com/turlamai/payback/pull/46), replacing it with a bilingual add-device/save/reopen verification flow.
- The three fixes above were merged and inspected on source branches, but live deployment was **not confirmed**.

### Remaining gates from this pass

- **Live pages:** The public `*.jrtx.site` endpoints were not accessible through the available web fetcher or container network; this is a connectivity limitation, not proof of a deployment failure. Browser interaction in the actual deployed sites is still required.
- **Images and downloads:** Binary image existence, all static assets, GitHub Release artifact aliases, redirect chains and HTTP status codes require independent validation. GitHub source files alone cannot prove the links work after deployment.
- **Applications:** Actual desktop installation, current UI, permissions, backup, update and failure/recovery walkthroughs remain untested here.
- **Documentation drift:** Repeat link verification after landing page redesign or locale changes, particularly site/manual paths and `index.html#...` references.

## Automated source-link regression check

The first-party site/source inventory lives in [docs/product-sites.json](docs/product-sites.json).
The standard-library-only [audit script](scripts/audit_product_docs.py) checks declared
`docs/index.html` / `site/index.html` and detailed HTML guide pages for:

- relative `href` / `src` assets and local CSS `url(...)` font/image assets referenced by inline styles or linked stylesheets that do not exist in the repository tree;
- local and cross-page `#fragment` anchors that do not exist in the target HTML;
- the legacy GitHub owner URL in these checked HTML documents.

Run `python3 -m unittest discover -s tests -p 'test_docs_audit.py' -v` for
offline unit tests, then `python3 scripts/audit_product_docs.py` for the
current checked-in source. The scheduled [GitHub Actions workflow](.github/workflows/docs-audit.yml)
runs weekly, on relevant PRs and on changes to its own inputs, and also supports
manual dispatch. The script is read-only and checks only declared first-party
public site source paths; it does not scan entire repository histories.

**Do not mistake a green source-link check for a deployed site acceptance.**
Remote URLs, published release aliases, images in CSS, JavaScript-generated links,
binary-content validity, i18n interactions, native UI behavior and recovery all
need separate verification. A GitHub Action schedule is subject to the repository
being enabled, workflow permissions and GitHub scheduler behavior.

## Maintenance rule

For every future product documentation change: run semantic editorial review under the policy, inspect the actual site/guide paths, verify both languages and navigation, check links, and test at least one observable user task. Treat this document as an audit ledger; append dated evidence instead of retroactively changing historical results.
