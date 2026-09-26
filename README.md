# StockSense

Modular Inventory Management System — built for the **Odoo x NMIT Bangalore Hackathon '26**.

Digitizes stock operations (receipts, deliveries, internal transfers, adjustments) that are normally tracked in manual registers or spreadsheets, into one real-time system.

## Status
Work in progress — Round 1 submission.

## Architecture
- Built as a custom Odoo 17 addon (`addons/stocksense`) on top of Odoo's native `stock` app.
- Reused from Odoo core: products, warehouses, locations, stock moves/pickings, quants.
- Custom, written by us: StockSense dashboard (KPIs + filters), OTP-based password reset, [more as built].

## Running locally
```bash
docker compose up
```
Then open http://localhost:8069, create a database, and install the **StockSense** app.

## Problem Statement
See `StockSense.pdf`. Full requirements breakdown in `docs/REQUIREMENTS.md`, build plan in `docs/BUILD_PLAN.md`.
