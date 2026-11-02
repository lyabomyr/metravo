# End-to-end test cases

Every case below is automated in `cypress/e2e/` and runs in CI on every push
(`.github/workflows/ci.yml` → job `e2e`). The backend runs with fake adapters
(`APP_ENV=e2e`): saved portal pages instead of live portals, a test payment
provider, a recording Telegram client. Each test signs in with a fresh email,
so tests are independent and can run in any order.

**Fixture data** — the saved results pages in `backend/tests/fixtures/pages/`:

| Portal | Id | Price | Area | Rooms | Year | Title (what the tests look for) |
|---|---|---|---|---|---|---|
| otodom | 101 | 520 000 | 45 | 2 | — | 2 pokoje przy Długiej |
| otodom | 102 | 900 000 | 80 | — | — | Penthouse |
| otodom | 103 | 480 000 | 41 | — | — | Mieszkanie TBS do wynajęcia |
| otodom | 104 | 555 000 | 50 | 3 | 2015 | 3 pokoje Wielicka |
| olx | 301 | 450 000 | 35 | — | — | Kawalerka Czyżyny |
| olx | 302 | 499 000 | 42 | — | — | 2 pokoje Bronowice |
| morizon | mzn200 | 555 000 | 50 | 3 | — | Wielicka 3 pokoje (twin of otodom 104) |
| morizon | mzn201 | 599 000 | 60 | 3 | — | Duże mieszkanie Nowa Huta |
| komornik | 9001 | 300 000 | 48.5 | — | — | Mieszkanie 48,5 m2 w Krakowie |
| otodom rent | 501 / 502 / 503 | 2 400 / 3 200 / 7 500 | 28 / 45 / 90 | | | Kawalerka z balkonem / 2 pokoje, balkon, winda / Apartament premium |
| morizon rent | mzn900 | 3 900 | 60 | 3 | | 3 pokoje Ruczaj, balkon |

The default search (buy, flat, Kraków, ≤ 600 000 zł, ≥ 40 m², otodom + olx + morizon)
matches **101, 104, 302, mzn201**.

## Landing page — `landing.cy.ts`

| Id | Case | Expected |
|---|---|---|
| LND-1 | Open `/` signed out | Hero, problem, how it works, 4 use cases with photos, features, pricing (Free and Pro), FAQ and footer credits are shown |
| LND-2 | Click a FAQ question | The answer opens |
| LND-3 | Click “Sign in” in the bar, or the final call to action | The page scrolls to the sign-in form and focuses the email field |
| LND-4 | Pick Polski, Українська, Русский in the language picker | The headline changes language; the choice survives a reload |
| LND-5 | Open `/` while signed in | Redirected to `/listings` |
| LND-6 | Pricing on the landing page | Free is 0 zł with “Start free”; Pro is 19 zł and lists the extra channels |

## Sign-in and session — `auth.cy.ts`

| Id | Case | Expected |
|---|---|---|
| AUTH-1 | New email on the landing form | Account and own database are created; goes to `/welcome` |
| AUTH-2 | Same email again | Goes to `/listings` |
| AUTH-3 | Address without a domain | Error banner, stays on the landing page |
| AUTH-4 | Sign out | Back on the landing page; `/listings` now redirects to `/` |
| AUTH-5 | Stored session token is invalid | The app forgets it and shows the landing page |
| AUTH-6 | Google button | Hidden when Firebase is not configured (e2e); shown with it — Firebase itself is checked in production (README §8) |

## First run — `onboarding.cy.ts`, `tour.cy.ts`

| Id | Case | Expected |
|---|---|---|
| ONB-1 | Save the default search, open the Telegram deep link, press Start | “All set”; Check now finds 4 listings |
| TOUR-1 | First sign-in | The tour opens at step 1 of 5 |
| TOUR-2 | Next / Back through all steps, then “Let’s go” | Titles change per step; closing hides it and it does not come back after a reload |
| TOUR-3 | Help (“?”) in the top bar | Opens the tour again |
| TOUR-4 | Skip, or Escape | Closes the tour |

## Searches — `search-form.cy.ts`

| Id | Case | Expected |
|---|---|---|
| FORM-1 | New search defaults | Buy, Flat, Kraków, once a day, otodom + olx + morizon on |
| FORM-2 | Switch to Rent | Budget becomes 4 000 zł/month; komornik is disabled |
| FORM-3 | Check rate on Free | Only “Once a day” can be picked; faster ones say Pro and are disabled |
| FORM-4 | Check rate on Pro | “Every hour” can be saved and shows on the card |
| FORM-5 | Invalid combinations: max area < min area, min price > budget, rooms to < rooms from, no portal | A translated error banner each time, nothing saved |
| FORM-6 | Edit a search, then delete it | The card shows the change; after confirming, it is gone |
| FORM-7 | Second search on Free | “allows 1 search” with an upgrade link |
| FORM-8 | komornik on Free | Pro badge on the portal; saving is refused with the portal named |

## Filters — `filters.cy.ts` (each through the form, then “Check now”)

| Id | Filter | Expected listings |
|---|---|---|
| FLT-1 | none (defaults) | 101, 104, 302, mzn201 — never 102 (budget), 103 (TBS), 301 (area), mzn200 (duplicate) |
| FLT-2 | Budget 520 000 | 101, 302 |
| FLT-3 | Min price 550 000 | 104, mzn201 |
| FLT-4 | Min area 50 | 104, mzn201 |
| FLT-5 | Max area 45 | 101, 302 |
| FLT-6 | Rooms from 3 | 104, mzn201, 302 (rooms unknown are kept) |
| FLT-7 | Rooms up to 2 | 101, 302 |
| FLT-8 | Max 11 000 zł/m² | mzn201 |
| FLT-9 | Built after 2020 | 101, 302, mzn201 and **mzn200** — the Otodom copy (2015) is dropped, its Morizon twin (year unknown) takes its place |
| FLT-10 | Must mention “Bronowice” | 302 |
| FLT-11 | Only olx | 302 |
| FLT-12 | Pro with komornik | the 4 defaults + 9001 |
| FLT-13 | Rent ≤ 4 000, must mention “winda” | 502 |

## Listings — `listings.cy.ts`, `rental-search.cy.ts`

| Id | Case | Expected |
|---|---|---|
| LST-1 | No search yet | Empty state with a link to Searches |
| LST-2 | Check now | Report “4 new”; cards show price, area, rooms, price per m², portal and open the ad in a new tab |
| LST-3 | Check now again at once | “Nothing to check right now” — the daily schedule holds |
| LST-4 | Rental search with “balkon” | 3 rentals, prices per month |

## Alerts — `alerts.cy.ts`

| Id | Case | Expected |
|---|---|---|
| ALR-1 | Connect Telegram from the Alerts page | The chat appears by itself; Disconnect removes it |
| ALR-2 | Extra channels on Free | Email, WhatsApp, Viber, Signal are shown, locked, with a Pro badge |
| ALR-3 | WhatsApp on Pro | Switch on, enter a phone, saved; reload keeps it |
| ALR-4 | Email on Pro | Address defaults to the account email |
| ALR-5 | Old `/telegram` link | Redirects to `/alerts` |

## Plan, data, admin — `billing-and-own-database.cy.ts`, `data-export.cy.ts`, `admin.cy.ts`

| Id | Case | Expected |
|---|---|---|
| PLAN-1 | Free → test checkout → Pro → credentials → cancel → Free | Badge and access follow the plan |
| DATA-1 | Downloads | A real SQLite file and a CSV with header + matches |
| ADM-1 | Regular user opens `/admin` | Redirected; no Admin tab |
| ADM-2 | Admin changes a user's plan | The table shows the new plan |
| ADM-3 | Admin opens System | Memory, CPU, last scan, active alerts and recent warnings are shown |

## Languages — `i18n.cy.ts`

| Id | Case | Expected |
|---|---|---|
| I18N-1 | Switch to each language inside the app | Navigation is translated; the account's language (used by Telegram) follows |
| I18N-2 | An API error in Polish | The banner text comes back in Polish from the backend |

## Phones — `mobile.cy.ts` (375 × 812)

| Id | Case | Expected |
|---|---|---|
| MOB-1 | Signed in | The tab bar is at the bottom and switches pages |
| MOB-2 | Every page | No horizontal scrolling |
| MOB-3 | Landing | Section links are hidden, the sign-in form fits the screen |
