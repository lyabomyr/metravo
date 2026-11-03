# End-to-end test cases

Every case below is automated in `cypress/e2e/` and runs in CI on every push
(`.github/workflows/ci.yml` → job `e2e`). The backend runs with fake adapters
(`APP_ENV=e2e`): saved portal pages instead of live portals, a test payment
provider, a recording Telegram client and a recording mailer. Each test signs
in with a fresh email, so tests are independent and can run in any order. The
test name starts with the case id, so a failure in CI points to a row here.

Run them: `make api` and `make web` in two terminals, then `make e2e`.

Contents: [Landing](#landing-page--landingcyts) · [Sign-in](#sign-in-and-session--authcyts) ·
[First run](#first-run--onboardingcyts-tourcyts) · [Navigation](#navigation--navigationcyts) ·
[Searches](#searches--search-formcyts) · [Filters](#filters--filterscyts-each-through-the-form-then-check-now) ·
[Listings](#listings--listingscyts-rental-searchcyts) · [Alerts](#alerts--alertscyts) ·
[Plan, data, admin](#plan-data-admin--billingcyts-data-exportcyts-admincyts) ·
[Languages](#languages--i18ncyts) · [Phones](#phones--mobilecyts-375--812) ·
[Every button](#every-button-and-the-case-that-presses-it) · [Below the UI](#below-the-ui--backend-unit-tests)

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

A new search has no price or area limits (FLT-14). The filter cases start from the
**fixture search** (buy, flat, Kraków, ≤ 600 000 zł, ≥ 40 m², otodom + olx + morizon),
which matches **101, 104, 302, mzn201**.

## Landing page — `landing.cy.ts`

| Id | Case | Expected |
|---|---|---|
| LND-1 | Open `/` signed out | No menu; hero, problem, how it works, 4 use cases with photos, features, pricing (Free and Pro), FAQ and footer credits are shown |
| LND-2 | Click a FAQ question | The answer opens |
| LND-3 | Click “Sign in” in the bar, or the final call to action | The page scrolls to the sign-in form and focuses the email field |
| LND-4 | Pick Polski, Українська, Русский in the language picker | The headline changes language; the choice survives a reload |
| LND-5 | Open `/` while signed in | Redirected to `/listings` |
| LND-6 | Pricing on the landing page | Free is $0 with “Start free”; Pro is $15 and lists the extra channels |

## Sign-in and session — `auth.cy.ts`

| Id | Case | Expected |
|---|---|---|
| AUTH-1 | New email on the landing form | A Free account is created; goes to `/welcome` |
| AUTH-2 | Same email again, setup finished (search + Telegram) | Goes to `/listings` |
| AUTH-3 | Address without a domain | Error banner, stays on the landing page |
| AUTH-4 | Sign out | Back on the landing page; `/listings` now redirects to `/` |
| AUTH-5 | Stored session token is invalid | The app forgets it and shows the landing page |
| AUTH-6 | Google button | Hidden when Firebase is not configured (e2e); shown with it — Firebase itself is checked in production (README §8) |

## First run — `onboarding.cy.ts`, `tour.cy.ts`

| Id | Case | Expected |
|---|---|---|
| ONB-1 | Save the default search, open the Telegram deep link, press Start | Telegram is one row of the channel list (email etc. alongside); before connecting, a note says the 20 newest arrive at once; “All set”; the scan starts by itself: the 6 Kraków listings are on the page without pressing anything, and Telegram gets them |
| ONB-2 | Sign in to an account that has a search but no Telegram | Back on `/welcome`: step 1 shown as done, step 2 (Telegram) is what is left |
| TOUR-1 | First sign-in | The tour opens at step 1 of 5 |
| TOUR-2 | Next / Back through all steps, then “Let’s go” | Titles change per step; closing hides it and it does not come back after a reload |
| TOUR-3 | Help (“?”) in the top bar | Opens the tour again |
| TOUR-4 | Skip, or Escape | Closes the tour |

## Navigation — `navigation.cy.ts`

| Id | Case | Expected |
|---|---|---|
| NAV-1 | Click every tab: Searches, Alerts, My data, Plan, Listings | Each opens its page, is marked active and shows the page title |
| NAV-2 | Sign out, then open `/searches` | Back on the landing page; the app is closed until signing in again |

## Searches — `search-form.cy.ts`

| Id | Case | Expected |
|---|---|---|
| FORM-1 | New search defaults | Buy, Flat, no place yet (map of Poland, Save disabled with “Choose a place”), only the place itself, once a day, no price or area limits, “must mention” empty, “must not mention” prefilled (TBS, …) and editable, every portal of the plan on |
| FORM-2 | Switch to Rent and back | A price of the wrong size is cleared; komornik is disabled for rent |
| FORM-3 | Check rate on Free | Only “Once a day” can be picked; faster ones say Pro and are disabled |
| FORM-4 | Check rate on Pro | “Every hour” can be saved and shows on the card |
| FORM-5 | Invalid combinations: max area < min area, price from > price up to, rooms to < rooms from, no portal | A translated error banner each time, nothing saved |
| FORM-6 | Edit a search, then delete it | The card shows the change; after confirming, it is gone |
| FORM-7 | Second search on Free | “allows 1 search” with an upgrade link |
| FORM-8 | komornik on Free | Pro badge on the portal; saving is refused with the portal named |
| FORM-9 | House instead of flat | Saved as a house; the card says House |
| FORM-10 | “Create your first search” on the empty page, and “New search” | Both open the form |
| FORM-11 | Type part of a village's name, pick the suggestion, +15 km | The card shows “Zabierzów +15 km”; saved with its voivodeship/county/municipality path and the radius |
| FORM-12 | A name that matches nothing; a click on the map | “Nothing found”; the click picks the place at that point |
| FORM-13 | The name field | Empty with “Named after the place”, then the chosen place, as a hint, so typing needs no deleting; saved empty, the search is named after its place |
| FORM-14 | Type “k”, then “kato”; press Enter | Nothing asked for one letter; a spinner while places load; one request for the word; Enter picks the first suggestion (Katowice) |
| FORM-15 | Focus an empty field | Its placeholder disappears at once, before typing |
| FORM-16 | The prefilled “must not mention” words | Grey with a note that they stay; typing in the field makes them normal text and hides the note |

## Filters — `filters.cy.ts` (each through the form, then “Check now”)

| Id | Filter | Expected listings |
|---|---|---|
| FLT-1 | none (defaults) | 101, 104, 302, mzn201 — never 102 (price), 103 (TBS), 301 (area), mzn200 (duplicate) |
| FLT-2 | Price up to 520 000 | 101, 302 |
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
| FLT-14 | A new search, no limits | the 4 defaults + Penthouse (102) + Kawalerka (301); still no TBS, no duplicate |
| FLT-15 | “Must not mention” emptied | the TBS listing (103) comes back |

## Listings — `listings.cy.ts`, `rental-search.cy.ts`

| Id | Case | Expected |
|---|---|---|
| LST-1 | No search yet | Empty state with a link to Searches |
| LST-2 | Check now | Report “4 new”; cards show price, area, rooms, price per m², portal and open the ad in a new tab |
| LST-3 | Check now again at once | “Nothing to check right now” — the daily schedule holds |
| LST-4 | Rental search with “balkon” | 3 rentals, prices per month |
| LST-5 | Delete a search after a scan | Its listings are gone from the page and the API |

## Alerts — `alerts.cy.ts`

| Id | Case | Expected |
|---|---|---|
| ALR-1 | Connect Telegram from the Alerts page, then Disconnect | The chat appears by itself; Disconnect removes it on the server too, the test button goes, and the “not connected” reminder is back |
| ALR-2 | Extra channels on Free | Email, WhatsApp, Viber, Signal are shown, locked, with a Pro badge |
| ALR-3 | WhatsApp on Pro | Switch on, enter a phone, saved; reload keeps it |
| ALR-4 | Email on Pro | Address defaults to the account email |
| ALR-5 | Old `/telegram` link | Redirects to `/alerts` |
| ALR-6 | Signed in without Telegram | Every page shows “Alerts are not connected” with a button to setup; gone once a chat is connected |
| ALR-7 | “Send a test message” for Telegram | “Sent” is shown; the bot posts a short message to the chat |
| ALR-8 | Email on Pro: switch on, send a test, type a wrong address, switch off | Email is live (no “soon”); the test is sent; a wrong address is refused with a message; switched off, the test button goes, it stays off after a reload, and the server refuses a test |

## Plan, data, admin — `billing.cy.ts`, `data-export.cy.ts`, `admin.cy.ts`

| Id | Case | Expected |
|---|---|---|
| PLAN-1 | Free → test checkout ($15) → Pro → cancel → Free | Badge follows the plan |
| PLAN-2 | Cancel on the checkout page | Back on Plan with “Payment cancelled”; still Free |
| PLAN-3 | Manage subscription → Back | Back on Plan; still Pro |
| PLAN-4 | A new Free account | “Free week: 7 day(s) left” on every page, “Free for 7 days” on the plan; gone on Pro. The end of the week (checks, alerts and new searches pause) is proven in `billing/test_free_week.py` with a fixed clock |
| DATA-1 | “My data” → CSV | A CSV with a header and one row per match, named after the search |
| DATA-2 | Another user's export, searches and listings | Empty: everyone shares one database, nobody sees anyone else's rows |
| ADM-1 | Regular user opens `/admin` | Redirected; no Admin tab |
| ADM-2 | Admin changes a user's plan | The table shows the new plan |
| ADM-3 | Admin opens System | Memory, CPU, last scan, active alerts and recent warnings are shown |
| ADM-4 | Refresh, then “Run scan for everyone” | Health reloads; a report of searches, page fetches and new listings appears |

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
| MOB-3 | Landing | The sign-in form fits the screen, nothing scrolls sideways |

## Every button and the case that presses it

| Page | Element (`data-cy`) | Case |
|---|---|---|
| Landing | Sign in (`landing-sign-in`), final call to action (`cta`), FAQ, language picker | LND-2, LND-3, LND-4 |
| Landing | Email + Sign in (`email`, `sign-in`) — local and test runs only; production shows Google alone | AUTH-1 … AUTH-3, ONB-1 |
| Landing | Continue with Google (`google`), Copy link in an app's browser (`copy-link`) | AUTH-6 (shown only with Firebase; the in-app browser check has a unit spec) |
| Top bar | Tabs (`nav-*`), Help (`help`), language (`language`), Sign out (`sign-out`) | NAV-1, TOUR-3, I18N-1, NAV-2 |
| Every page | Reminder → Connect Telegram (`connect-reminder-action`) | ALR-6 |
| Tour | Next, Back, Skip, Let’s go (`tour-*`) | TOUR-1 … TOUR-4 |
| Welcome | Save and continue (`search-save`), Open Telegram (`telegram-open`), See your listings (`onboarding-listings`) | ONB-1, ONB-2 |
| Listings | Check now (`scan-now`), open an ad | LST-2, LST-3 |
| Searches | New search, Create your first search, Edit, Delete (`new-search`, `create-first-search`, `search-edit`, `search-delete`) | FORM-10, FORM-6 |
| Search form | Buy/Rent, Flat/House, place autocomplete, spinner, results, map, radius, every field and portal switch, Save | FORM-1 … FORM-16, FLT-1 … FLT-13 |
| Alerts | Open Telegram, Add to a group (link checked), Disconnect, Send a test (`test-telegram`) | ALR-1, ALR-7 |
| Alerts | Channel switches, addresses, Send a test (`channel-toggle-*`, `channel-address-*`, `test-email`) | ALR-2, ALR-3, ALR-4, ALR-8 |
| My data | Download listings (.csv) (`download-csv`) | DATA-1 |
| Plan | Upgrade, Manage subscription; test checkout Pay / Cancel; test portal Cancel subscription / Back | PLAN-1 … PLAN-3 |
| Admin | Make pro / Make free, Refresh, Run scan for everyone | ADM-2, ADM-4 |

## Below the UI — backend unit tests

`backend/tests/unit/` (pytest, `make test`) checks what the browser cannot see:

| Area | File | What it proves |
|---|---|---|
| Isolation | `searches/test_isolation.py`, `export/test_export_service.py` | One user never reads, changes, deletes or exports another's rows |
| One copy per offer | `listings/test_shared_catalog.py` | Two users matching the same offers store them once; a price drop reaches both; old tables are migrated |
| Telegram | `telegram/test_two_click_setup.py` | Start links the chat once; connecting sends what was found and scans at once; `/pause`, `/disconnect` stop messages |
| Email | `notifications/test_email.py` | Listings arrive by email in the user's language with an unsubscribe link; wrong addresses are refused; switched off means nothing is sent; the test message |
| Channels | `notifications/test_channels.py` | Plan rules for Pro channels; a downgrade stops them |
| Scanning | `scanning/test_scan_service.py`, `test_scheduler.py` | Due searches, plan floors, price changes, the schedule |
| Filters | `scanning/test_listing_filter.py` | Every filter rule |
| Errors | `core/test_http.py` | A crash still answers the site with a readable message |
| Places | `places/test_places.py`, `connectors/test_parsers.py` | OpenStreetMap answers become the portals' paths; cities with county rights; caching; points on the map; each portal's URL for a village with a radius; old `city` searches still read |
