# SubFlow launch website

Date: 2026-10-03

## Scope

A static, bilingual website for the iOS/iPadOS App Store launch, hosted at
`https://bo-xing.github.io/subflow-site/`. English is the default. Simplified
Chinese has explicit `/zh-Hans/` routes; language switching preserves the page.

Pages: product home, support/FAQ/contact, privacy policy, and terms/subscription
information. Terms link to Apple's standard EULA, consistent with the app.
No account, analytics, cookies, forms, remote fonts, or third-party scripts.

## Product and privacy sources

The app repository's current `docs/PRODUCT.md`, `docs/STATUS.md`,
`docs/DESIGN.md`, `SubscriptionPrivacyView.swift`, and privacy manifest govern
claims. Do not market hidden video export, promise fixed recognition accuracy,
all-device/language support, subtitles in Picture in Picture, or uninterrupted
background transcription. Explain free first-ten-minute recognition separately
from unlimited playback. Pro monthly/yearly plans have identical benefits;
localized prices come from the App Store.

Distinguish local app processing from optional BYOK subtitle/context requests,
user-configured media servers, Apple purchases, support email, and GitHub Pages
hosting. Explain local retention, exported files, credentials, and provider
policies without claiming the website or third parties collect nothing.
Developer identity and a public support email must be supplied before release.

## Visual direction

Follow the existing app brand: cinema black `#090A0D`, warm white `#F5F2EA`,
amber `#F2B650`, restrained borders, system typography. The home page uses a
large editorial headline and a clearly labeled illustrative subtitle preview.
Legal/support pages favor readable line lengths and anchored navigation.
Use the existing app icon. UI/UX skill recommendations are subordinate to the
app's established design system. No invented screenshots or ratings.

## Architecture

Python standard-library build, shared HTML templates and CSS, separate JSON
copy for `en` and `zh-Hans`. Generate complete HTML into ignored `dist/`;
all essential content works without JavaScript. A tiny optional script switches
the illustrative subtitle preview. One config holds the site URL, developer,
contact, revision date and optional App Store URL. Asset/navigation paths must
work at a GitHub project subpath and a custom domain. Generate canonical URLs,
language alternates, a sitemap, robots.txt, and a 404 page.

GitHub Actions checks/builds the site and uploads only `dist/`, then deploys
through the official Pages actions. Deployment is available on push to main
and manual dispatch from main; other branches may only build and validate.
Repository Pages must use GitHub Actions. Never invent an
App Store ID, custom domain or contact address.

## Validation

Check both locales, generated internal links/fragments/assets and metadata,
contact/release config, no external scripts, and project-prefix/custom-domain
builds. Inspect desktop and small-phone rendering, no horizontal overflow,
language switching, keyboard focus, native FAQ disclosure, subtitle preview,
and JavaScript-disabled content. Preview GET and HEAD requests must agree on
project-path redirects, successful pages, and the custom 404. Language link
accessible names must use the language declared on those links. Record results and open release items in
`docs/STATUS.md`; provide the exact App Store URL mapping in README.
