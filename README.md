# StockSense

Modular Inventory Management System — built for the **Odoo x NMIT Bangalore Hackathon '26**.

Digitizes stock operations (receipts, deliveries, internal transfers, adjustments) that are normally tracked in manual registers or spreadsheets, into one real-time system.

## Architecture

Built as a custom Odoo 17 addon (`addons/stocksense`) on top of Odoo's native `stock` and `product_expiry` apps — not a from-scratch reimplementation.

**Reused from Odoo core** (configured, not rewritten):
- Products, warehouses, locations, stock moves/pickings, quants
- Receipts, delivery orders, internal transfers, inventory adjustments
- Lot/expiry tracking and FEFO (First-Expired-First-Out) removal strategy

**Custom, written for this project** (`addons/stocksense/`):
- **Dashboard** (`models/dashboard.py` + OWL component `static/src/js/dashboard.js`) — live KPIs (products in stock, low/out of stock, pending receipts/deliveries/transfers) with filters by document type, status, warehouse, category
- **Product Intelligence** (`models/product_intel.py` + `static/src/js/products.js`) — one screen combining:
  - Smart search (name, SKU, category, or location)
  - Full movement timeline per product
  - One-tap stock adjust and damage/wastage reporting
  - Velocity-based reorder suggestions (real math over 30-day move history, not a fixed threshold)
  - Physical-count vs system-count mismatch detection, applied live
  - Stale/idle stock flagging (no movement in 14+ days, or never moved)
  - End-of-day summary (received/delivered today, current qty, idle status, per product)
  - Simple location-imbalance transfer suggestions (explainable heuristic, not a full optimizer)
- **OTP password reset** (`models/otp.py` + `controllers/auth.py` + `views/auth_templates.xml`) — real 6-digit OTP generation, single-use, 10-minute expiry, hooked into the actual login page's "Reset Password" link. OTP delivery is simulated (shown on-screen, labeled "demo mode") since no SMS/email provider is configured — the OTP logic itself is real.

## Running locally

```bash
docker compose up -d
```

Then create the database and install the app:

```bash
docker compose exec odoo odoo -d stocksense -i stocksense --without-demo=all \
  --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo --stop-after-init
docker compose up -d
```

Open http://localhost:8069, log in with `admin` / `admin`.

To load the worked-example scenario (matches the problem statement's own example: receive 100kg steel → transfer → deliver 20kg → adjust 3kg damaged) and the FEFO demo (two expiry batches, oldest consumed first):

```bash
docker compose exec -T odoo odoo shell -d stocksense --db_host=db --db_user=odoo --db_password=odoo < scripts/demo_scenario.py
docker compose exec -T odoo odoo shell -d stocksense --db_host=db --db_user=odoo --db_password=odoo < scripts/demo_fefo.py
```

## What's demonstrated vs. what's roadmap

Built and working: everything listed under "Custom" above, plus the full native Odoo inventory flow.

Deliberately not built, given the time constraint of this build (documented honestly rather than silently dropped):
- Barcode/camera-based scanning
- Warehouse digital map / visual product locator
- A real transfer-optimization engine (the current version is a simple explainable heuristic)

## Problem Statement

See `StockSense.pdf`. Full requirements breakdown in `docs/REQUIREMENTS.md`, build log in `docs/BUILD_PLAN.md`.
