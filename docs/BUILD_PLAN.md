# StockSense — 5-Hour Build Plan (Round 1: GitHub repo + demo video)

**Strategy:** Build as a custom Odoo addon on top of Odoo's native `stock` app (products, warehouses, locations, pickings, quants). This gives receipts, deliveries, internal transfers, adjustments, reordering rules, and multi-warehouse support for free — we only build a custom dashboard + branding + light auth flow on top. Do NOT build inventory logic from scratch.

Confirmed from the official participant guide: there is **no tech-stack mandate** — Odoo is a strategic choice (speed + platform fit for an Odoo-run hackathon), not a hard requirement.

## Confirmed submission rules (from the participant guide video)
- Team leader submits a **public GitHub repo link**; a video-submission button appears after that, for the solution video link (submit after coding period ends).
- Both links can be edited via "update submission" until the deadline — no need to rush a final push.
- **Q&A round is generated from the code YOU personally committed, tied to your GitHub account linked to your profile.** This is the highest-leverage constraint in the whole plan:
  - Every commit you push must be code you can explain fluently — favor fewer features you deeply understand over more features copy-pasted from Odoo internals you can't defend live.
  - On a team, commits must be attributed honestly per person — one person committing everything means teammates face Q&A on code they didn't write.
  - **Check right now that your GitHub account is correctly linked to your hackathon profile** — before spending build time, not after.
- Repo must stay public throughout (troubleshooting note: unlinked/private repo breaks the Q&A queue).

## Hard rule: commit to GitHub every ~30 min
Round 1 judges may check commit history for authenticity — don't do one giant commit at hour 5. On top of that, commits are now also literally the Q&A question bank, so commit in small, explainable chunks per person, not one dump.

## Cut list (drop these FIRST if behind schedule, in this order)
1. Real OTP (fake it — log OTP to console/UI, or fall back to Odoo's native email reset link)
2. Reordering-rule automation (just show the config field; manual trigger only)
3. Multi-warehouse (collapse to 1 warehouse, 2 locations — still satisfies "internal transfer" demo)
4. Fancy OWL dashboard → fallback to a static QWeb template with server-computed counts
5. Product category management UI (use Odoo's default category tree as-is)

Never cut: Receipt → Delivery → Internal Transfer → Adjustment core loop. That's the entire PS.

---

## Timeline

### 0:00–0:30 — Setup ✅ DONE
- [x] Odoo 17 + Postgres 15 via `docker-compose.yml`
- [x] Scaffolded custom addon `addons/stocksense`
- [x] `git init`, first commit, pushed to GitHub: https://github.com/pfgctrl07/stocksense
- [x] README with architecture + run instructions

### 0:30–1:30 — Demo data & core config ✅ DONE
- [x] `stock` app installed via addon dependency; default warehouse (WH) + new "Production Rack" location
- [x] 5 demo products (Steel Rods, Chairs, Wood Planks, Screws, Tables) with categories/SKU/UoM via `data/demo_data.xml` (reproducible, not manual clicks)
- [x] Initial stock set on 3 products
- [x] Commit: "demo data + warehouse config"
- Bug caught & fixed: products defaulted to `type='consu'` (untracked) instead of `type='product'` (tracked) — silently produced zero stock everywhere until caught by scripting the scenario and checking actual quant rows, not just move state.

### 1:30–2:30 — Core flows (walk the PS's own example scenario) ✅ DONE
Replayed the PDF's worked example via `scripts/demo_scenario.py` (Odoo ORM), verified against real quant values, not just "no error thrown":
- [x] Receipt: receive 100 kg Steel → validate → stock +100 (confirmed: 100.0)
- [x] Internal Transfer: Main Store → Production Rack (50kg) → confirmed both sides (50.0 / 50.0)
- [x] Delivery: deliver 20 → validate → stock −20 (confirmed: 30.0)
- [x] Adjustment: 3 kg steel damaged → adjust → stock −3 (confirmed: 27.0)
- [x] All 4 show up in Move History with correct locations/qty/state=done
- [x] Commit: "core inventory flows verified"

### 2:30–3:30 — Custom Dashboard (the one real custom-code piece) ✅ DONE
- [x] Built as a real OWL component (`static/src/js/dashboard.js`) + backend model (`models/dashboard.py`), not native Odoo views — genuinely custom code, verified live in a browser (not just "compiles")
- [x] KPIs: Total Products in Stock, Low/Out of Stock, Pending Receipts, Pending Deliveries, Internal Transfers Scheduled — all wired to real data, confirmed correct values on screen
- [x] All 4 filters implemented and confirmed interactive: document type, status, warehouse, category
- [x] Commit: "custom StockSense dashboard"
- Verification method: used Chrome automation to actually log in, open the dashboard, and change a filter — confirmed correct KPI numbers, correct filtered table, zero console errors. Not just "no exception in the server log."

### Phase 4.5 — Innovation features (Product Intelligence) ✅ DONE
User requested 10 "innovation" ideas. Brutal scoping call made and stated upfront: built 7, deferred 3 to roadmap.
- [x] Smart search — by product name, SKU, category, or location (verified: "rack" correctly finds only Steel Rods)
- [x] Movement timeline — full chronological history per product, verified live
- [x] One-tap stock update — qty input + / − buttons, verified live
- [x] Damage/wastage button — same mechanism, semantically labeled
- [x] Smart reorder suggestion — real velocity math (avg daily outflow over 30d → days-of-stock-left → suggested qty), not a fixed threshold. Verified: Steel Rods correctly shows 115.5 days left from 0.67/day outflow.
- [x] Mismatch detection — physical count vs system qty, live diff calc in the browser (typed 70 against 77 → correctly showed "Diff: -7")
- [x] Auto stock alerts — delivered as red row highlighting on this screen, not a separate notification system (explicit scope cut, stated upfront)
- Deferred to roadmap, NOT built (stated upfront, not silently dropped): barcode/camera scanner, warehouse digital map + product locator, auto transfer suggestions between locations — all high-effort/high-demo-risk for time remaining
- Commit: `1d2a4be`

### 3:30–4:00 — Auth flow
- [ ] Confirm signup/login works (Odoo native)
- [ ] Add password reset — real OTP if time allows (simple model: generate code, show in a controller/log for demo, verify, reset password); otherwise fall back to Odoo's built-in email reset and say "OTP" in the video is the code emailed
- [ ] Commit: "auth + password reset"

### 4:00–4:30 — Branding & polish
- [ ] Relabel menus to match PS navigation: Products / Operations (Receipts, Delivery, Adjustment, Move History, Dashboard) / Settings → Warehouse / Profile
- [ ] Add StockSense name/logo/color in the app header (`web.assets_backend` tweak or module icon)
- [ ] Sanity pass: click every menu item once, fix anything broken/ugly
- [ ] Commit: "branding + navigation cleanup"

### 4:30–5:00 — Demo video + README + final push
- [ ] Record 2–3 min video: login → dashboard KPIs → create product → receipt → transfer → delivery → adjustment → dashboard updates live → low-stock alert
- [ ] Finish README: problem statement summary, architecture (Odoo addon, models reused vs. custom), setup instructions, screenshots, link to video
- [ ] Final commit + tag (e.g. `v0.1-round1`)
- [ ] Push, double check GitHub repo is public/accessible to judges

---

## What "qualifying" likely means here
Judges in Round 1 are almost never grading feature completeness — they're grading: does the core loop work, is it demoable, is the repo real (commits, README), and does the idea make sense. The worked example in the PS (receive → transfer → deliver → adjust, all in the ledger) is your entire demo script. Nail that end-to-end and the KPI dashboard, and everything else (OTP, multi-warehouse, reordering automation) is bonus polish, not a blocker.
