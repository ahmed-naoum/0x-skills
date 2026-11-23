# Open-source licenses and third-party IP

Read this when: adding a dependency whose license is not plainly permissive; preparing a
release, app-store build or container image that ships third-party code; using fonts, images,
icons, datasets, APIs or scraped data; choosing a license for the product's own code; accepting
outside contributions; or relying on AI-generated code or assets.

## The question that decides most cases: is it distributed?

Most open-source obligations attach when the software is conveyed to someone else, not when it
is run.

| How the code reaches others | Distribution? |
|---|---|
| Runs only on the company's servers behind a SaaS | No, for GPL and LGPL. Yes in effect for AGPL and other network-clause licenses |
| JavaScript, CSS, WebAssembly and fonts sent to browsers | Yes |
| Mobile and desktop apps, CLIs, SDKs, browser extensions | Yes |
| Container images, VM images, self-hosted or on-premises editions given to customers | Yes, including the base image's system packages |
| Code handed to a client under a contract | Yes |

## Dependency licenses

| Family | Examples | Obligation | Policy for a closed-source product |
|---|---|---|---|
| Permissive | MIT, ISC, BSD-2-Clause, BSD-3-Clause, Apache-2.0, Zlib, 0BSD | Keep the copyright and license text with distributed copies; Apache-2.0 also requires carrying any NOTICE file and stating changes, and grants a patent license | Allow |
| Public-domain style | CC0-1.0, Unlicense | None in practice | Allow |
| File-level or library copyleft | MPL-2.0, LGPL-2.1, LGPL-3.0, EPL-2.0 | Changes to the licensed files or library must be shared; LGPL also requires that the user can replace the library | Allow unmodified use on the server. Review before modifying it, bundling it into front-end or mobile code, or statically linking it |
| Strong copyleft | GPL-2.0, GPL-3.0 | A distributed work that incorporates it must be offered under the GPL with source | Server-side and build-time use is fine; never link it into anything distributed. Running a GPL program as a separate process (a CLI tool, a database) does not affect the calling code |
| Network copyleft | AGPL-3.0 | Users interacting with a modified version over a network must be offered its source; how far that reaches into code combined with it is contested | Deny by default as a linked library. Using an unmodified AGPL service as a separate process is commonly accepted, but customers' procurement and acquirers' diligence often object: decide deliberately |
| Source-available | SSPL, Business Source License, Elastic License, Functional Source License, Commons Clause, "sustainable use" licenses | Not open source. Typically forbid offering the software as a competing hosted service, or production use above a threshold | Read the specific grant; usually fine for internal use, not fine for reselling as a service |
| No license, or custom terms | A repository without a license file, code from a forum answer or blog | No rights granted by default | Do not copy; ask the author or reimplement |
| Non-software licenses on code or assets | CC BY-NC (no commercial use), CC BY-ND, CC BY-SA (share-alike) | As named | Deny NC and ND for product use; SA only for content the company is willing to share alike |

Compatibility traps: Apache-2.0 code cannot be combined into a GPL-2.0-only work, while it can
with GPL-3.0. A package's license can change between versions, so pin and re-check on major
upgrades. The manifest's license field can disagree with the repository's license file, and
transitive dependencies matter as much as direct ones. Dual-licensed packages ("GPL or
commercial") require buying the commercial license for closed distribution. Dev-only tooling
that never ships does not impose distribution obligations.

Enforce it mechanically. Keep an allowlist of SPDX identifiers and fail CI on anything else:

```bash
pnpm licenses list --prod --json > licenses.json
```

Parse the output in a small script that exits non-zero when a license outside the allowlist
appears, with a reviewed exceptions file (package, version, license, reason, approver). For
other ecosystems use the equivalent license reporter, or a scanner that reads the lockfile and
produces an SBOM. Dependency security scanning is `0x:web-security` (`supply-chain.md`).

## License inventory and attribution for a release

Whenever something is distributed (see the first table), ship the notices.

1. Generate the inventory of production dependencies with name, version, license identifier
   and license text, from the lockfile at the release commit.
2. Web bundles: minifiers strip license comments. Configure the bundler's license plugin to
   emit a third-party notices file and link it from the app (an "Open-source licenses" page or
   `/licenses.txt`).
3. Mobile and desktop apps: include an acknowledgments screen or bundled notices file; the
   platform dependency managers have generators for it.
4. Container and on-premises deliveries: include notices for application dependencies and
   point to the base image's package licenses; if any GPL or LGPL component is shipped, include
   its source or a written offer as the license requires.
5. Apache-2.0 dependencies: reproduce their NOTICE contents.
6. Store the inventory with the release artifact. An SBOM in SPDX or CycloneDX format serves
   as the inventory and is increasingly requested by enterprise buyers and by EU product law.

A pure SaaS with no downloadable component still distributes its browser bundle, so step 2
applies from Launch.

## Fonts, images, icons and data

| Asset | What to check | Common trap |
|---|---|---|
| Fonts | The license type bought: desktop, web (often capped by monthly page views), app embedding and server-side rendering (PDF or image generation) are separate licenses at most foundries | A desktop license used on the website; self-hosting a font from a subscription library whose terms require its own delivery. Fonts under the SIL Open Font License can be self-hosted, embedded and modified, but not sold on their own |
| Stock photos, illustrations, video, audio | Commercial use allowed; limits on use in logos, templates, merchandise or resale; "editorial use only" items cannot be used in marketing | Assuming free stock sites grant model, property or trademark releases: they do not |
| Icon sets and UI kits | Most popular sets are MIT, ISC or Apache; some free tiers require attribution or split licenses across icons, fonts and code | Paid kit licenses are often per seat or per project |
| Images of people and brands | A person's likeness in advertising needs a release; customer logos and testimonials need written permission | A logo wall built from a list of signups |
| Screenshots, maps, charts | Map tiles and data carry attribution and usage terms; screenshots of others' products are usually tolerated for commentary, not as product assets | Removing the map attribution to tidy the design |
| Datasets | Copyright, database rights (the EU protects substantial investment in a database even when the facts are free), contract terms, personal data | Share-alike data licenses such as ODbL require attribution and sharing of derived databases; "open data" does not always permit commercial use |
| Music and video in marketing | Synchronization rights; platform libraries license use only on that platform | Reusing a social platform's audio in a paid ad |

Keep an asset register: item, source URL, license, proof of purchase or a saved copy of the
license terms as of the download date, where it is used. Free-license terms change, and the
saved copy is the evidence. Design and marketing contractors must assign their work and
warrant the origin of what they deliver; company-level IP assignment is `0x:company-building`.

## APIs, scraping and data sources

Read the terms of every API and data source before building on it; they are a contract, and
the usual way to lose a product is a revoked key.

| Clause to look for | Effect on design |
|---|---|
| Caching and storage limits | May forbid storing results beyond a short period or building a database from them (map, search and social APIs commonly do) |
| Display and attribution requirements | Logos, links, or display only alongside the provider's own product |
| Prohibited uses | Competing products, benchmarking, model training, resale, surveillance |
| User-data policies for OAuth scopes | Limited-use rules, mandatory privacy disclosures, security assessments for sensitive scopes, and verification delays to plan for before launch |
| Rate limits, commercial tiers, change and termination rights | Free tiers often exclude commercial use; providers reserve the right to change terms on short notice |

Scraping risk, by layer:

1. Contract: terms accepted through an account or a clear click bind the scraper; scraping
   while logged in is the highest-risk form. Terms merely posted on a public site are harder to
   enforce but are still cited.
2. Unauthorized access laws: US courts have been reluctant to treat scraping of genuinely
   public pages as hacking, but circumventing technical barriers (logins, IP blocks, CAPTCHAs)
   after being told to stop changes the analysis.
3. Copyright and database rights: facts are free, expression and (in the EU) substantial
   extractions from databases are not. EU law lets rights holders opt out of text and data
   mining in machine-readable form; honor `robots.txt` and similar signals.
4. Privacy law: publicly visible personal data is still personal data. Collecting profiles at
   scale has drawn large fines; a lawful basis and notice duties apply.
5. Operational: rate-limit, identify the crawler honestly, and stop on request.

Default: use an official API or licensed feed; scrape only public, non-personal, factual data,
at polite rates, with the source's signals respected, and get advice before a product depends
on it.

## AI-generated code and assets

Two separate exposures: whether the output infringes someone else's rights, and whether the
company owns it.

- **Infringement.** Models can reproduce training material. For code, turn on the assistant's
  filter for matches to public code where one exists, be suspicious of long, idiosyncratic or
  license-headered output, and never ask for a reproduction of a named project's
  implementation. For images, audio and text, do not prompt with living artists' names, brand
  characters, logos or real people's likenesses, and run a reverse image search on anything
  used as brand or product identity.
- **Provider terms.** Use paid commercial plans whose terms assign or license output to the
  customer and include an intellectual-property indemnity; read the conditions (filters left
  on, no knowingly infringing prompts, unmodified service). Free and consumer tiers often
  lack both, and may use inputs for training. Record which tool and plan produced material
  assets.
- **Ownership.** In the US, material generated by AI without sufficient human authorship is not
  protected by copyright; human selection, arrangement and modification are. Other
  jurisdictions differ. Consequences: a purely generated logo or illustration may be
  unprotectable against copying (trademark registration still works if it is distinctive);
  for code, protection rests on the human-authored structure and edits plus trade secrecy and
  contract. Keep meaningful human authorship in anything the business depends on owning.
- **Disclosure duties.** Investors, acquirers and enterprise customers ask whether AI tools
  were used and under what terms; some customer contracts restrict it for deliverables.
  Answer from the record. Do not claim copyright registration over purely generated material
  without disclosing its origin.
- **Inputs.** Pasting third-party confidential code or customer data into a tool can breach an
  NDA or DPA regardless of the output.

## Licensing the product's own code

| Goal | Choice | Consequence |
|---|---|---|
| Closed SaaS (the default) | Proprietary; no license file in public; terms of service govern use | Nothing to manage |
| Adoption of an SDK, client library or developer tool | Apache-2.0 (explicit patent grant) or MIT | Anyone may use, fork and sell it; the moat is elsewhere |
| Open-core product, wanting improvements shared and closed forks deterred | AGPL-3.0 for the core, with a commercial license sold alongside | Some companies ban AGPL adoption; dual licensing requires owning or having broad rights to all contributions |
| Visible source, no competing hosted offering | A source-available license: Business Source License with a change date, or Functional Source License converting to a permissive license after a fixed period | Not open source, and must not be called that; excluded from some distributions and procurement lists |
| Documentation and content | CC BY-4.0 or all rights reserved | Do not use Creative Commons licenses for code |

Relicensing later requires the agreement of every copyright holder, so the contribution model
must be decided before the first outside pull request. A later move from open source to a
restrictive license is legally possible only with those rights and has reliably cost community
trust and prompted forks. The name and logo are protected by trademark, not by the code
license: publish a short trademark policy and register the mark once the name matters.

## Outside contributions: CLA or DCO

| | DCO | CLA |
|---|---|---|
| What it is | A per-commit certification by the contributor that they have the right to submit the work, expressed as a sign-off line | A signed agreement granting the project owner a broad license (or assignment) over contributions |
| Friction | Low | Higher; some contributors and employers refuse |
| Lets the owner relicense or dual-license | No: contributions come in under the project's license only | Yes, if the grant is drafted for it |
| Enforcement | A CI check that every commit carries the sign-off | A bot that blocks merging until the contributor has signed |

```bash
git commit -s -m "Fix pagination cursor"   # adds: Signed-off-by: Name <email>
```

Choose a CLA when the business model depends on selling commercial licenses or keeping the
option to relicense; choose the DCO for a permissively licensed library where neither is
planned. Either way, contributors employed elsewhere may not own what they write: a corporate
CLA or the employer's sign-off covers that. Record signatures durably, outside the bot's
vendor.

## Ask the user

- **Is anything shipped to customers beyond the web app (mobile app, CLI, SDK, self-hosted
  edition, container image)?** It decides whether copyleft and notice duties bite. Default:
  SaaS plus browser bundle; notices file for the bundle.
- **Is AGPL or source-available software acceptable as a service dependency?** A risk and
  sales-diligence decision. Default: not as a linked library; as a separate unmodified service
  only with the user's explicit approval.
- **Should any of the product's code be open, and is selling a commercial license part of the
  model?** Decides the license and the CLA. Default: proprietary; Apache-2.0 for SDKs.
- **Where did the fonts, images and icons come from, and are the licenses on file?** Default:
  open-licensed, self-hosted fonts and icons; an asset register started at Launch.
- **Does the product depend on scraped data or one provider's API?** It is a continuity and
  legal risk to raise before building. Default: official APIs within their terms.
