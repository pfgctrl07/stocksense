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

### 0:00–0:30 — Setup
- [ ] Install/run Odoo (Docker is fastest: `docker run` odoo + postgres, or local pip env if already set up)
- [ ] Scaffold custom addon: `odoo-bin scaffold stocksense addons/`
- [ ] `git init`, first commit (empty scaffold), push to GitHub immediately — repo must exist early
- [ ] Write a 5-line README stub (fill in properly at the end)

### 0:30–1:30 — Demo data & core config
- [ ] Enable `stock` app, create 1–2 warehouses, 2–3 locations (Main Store, Production Rack)
- [ ] Create 8–10 demo products with categories, SKU, UoM (via UI or a data XML/CSV so it's reproducible)
- [ ] Set initial stock for a few products (so dashboard isn't empty)
- [ ] Commit: "demo data + warehouse config"

### 1:30–2:30 — Core flows (walk the PS's own example scenario)
Replay the PDF's worked example exactly — it becomes your demo script:
- [ ] Receipt: receive 100 kg Steel → validate → stock +100
- [ ] Internal Transfer: Main Store → Production Rack
- [ ] Delivery: deliver 20 (finished goods) → validate → stock −20
- [ ] Adjustment: 3 kg steel damaged → adjust → stock −3
- [ ] Verify all 4 show up in Move History / stock ledger
- [ ] Commit: "core inventory flows verified"

### 2:30–3:30 — Custom Dashboard (the one real custom-code piece)
- [ ] Build a dashboard view (simplest viable: QWeb template + a controller/model method computing counts) with KPIs:
  Total Products in Stock, Low/Out of Stock, Pending Receipts, Pending Deliveries, Internal Transfers Scheduled
- [ ] Add filters: document type, status (Draft/Waiting/Ready/Done/Canceled), warehouse/location, category
  - If time-boxed: ship 2 of the 4 filters, note the rest as "next"
- [ ] Commit: "custom StockSense dashboard"

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
