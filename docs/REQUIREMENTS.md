# StockSense — Requirements Documentation
**Odoo Hackathon — Problem Statement: Inventory Management System (IMS)**

> Status: Draft skeleton generated from `StockSense.pdf`. Sections marked `TBD` need team input.

---

## 1. Document Info
| Field | Value |
|---|---|
| Project Name | StockSense |
| Type | Modular Inventory Management System (IMS) |
| Source | `StockSense.pdf` (Odoo Hackathon PS) |
| Mockup | https://link.excalidraw.com/l/65VNwvy7c4X/3ENvQFu9o8R |
| Version | 0.1 (draft) |
| Date | 2026-09-26 |
| Author(s) | TBD |
| Team Name | TBD |

---

## 2. Problem Statement (Summary)
Build a modular Inventory Management System that digitizes and streamlines all stock-related operations, replacing manual registers, Excel sheets, and scattered tracking with a centralized, real-time, easy-to-use app.

## 3. Objectives
- Centralize all stock movement (in / out / internal / adjustments) into one system of record.
- Give real-time visibility into stock levels, locations, and pending operations.
- Reduce manual/Excel-based tracking errors.
- Support multi-warehouse, multi-location operations out of the box.

## 4. Scope
### In Scope
- Product catalog & categories
- Stock receipts (inbound), delivery orders (outbound), internal transfers, stock adjustments
- Multi-warehouse / multi-location tracking
- Dashboard with KPIs and dynamic filters
- Low-stock alerts, reordering rules
- Auth (signup/login, OTP password reset)
- Move history / stock ledger

### Out of Scope (default — confirm with team)
- Sales/Purchase order management beyond what triggers receipts/deliveries
- Accounting / invoicing
- Multi-company / multi-currency
- Barcode scanning hardware integration *(TBD — nice-to-have?)*

## 5. Target Users & Personas
| Persona | Responsibilities |
|---|---|
| **Inventory Manager** | Manage incoming & outgoing stock, oversee reorder rules, view dashboard/KPIs |
| **Warehouse Staff** | Perform transfers, picking, shelving, physical counting |

## 6. User Roles & Permissions *(TBD — not specified in PS, needs definition)*
| Role | Products | Receipts | Deliveries | Transfers | Adjustments | Settings |
|---|---|---|---|---|---|---|
| Inventory Manager | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD |
| Warehouse Staff | Read | Update (execute) | Update (execute) | Create/Execute | Create | Read |

---

## 7. Functional Requirements

### 7.1 Authentication
- FR-1.1: User can sign up / log in.
- FR-1.2: Password reset via OTP.
- FR-1.3: On successful login, redirect to Inventory Dashboard.

### 7.2 Dashboard
- FR-2.1: Display KPIs — Total Products in Stock, Low Stock/Out of Stock Items, Pending Receipts, Pending Deliveries, Internal Transfers Scheduled.
- FR-2.2: Dynamic filters by:
  - Document type (Receipts / Delivery / Internal / Adjustments)
  - Status (Draft, Waiting, Ready, Done, Canceled)
  - Warehouse or location
  - Product category

### 7.3 Product Management
- FR-3.1: Create/update products with: Name, SKU/Code, Category, Unit of Measure, Initial stock (optional).
- FR-3.2: View stock availability per location.
- FR-3.3: Manage product categories.
- FR-3.4: Define reordering rules (min/max thresholds — *TBD exact fields*).

### 7.4 Receipts (Incoming Stock)
- FR-4.1: Create a new receipt with supplier & products.
- FR-4.2: Input quantities received.
- FR-4.3: Validate receipt → stock increases automatically.
- Example: Receive 50 units of "Steel Rods" → stock +50.

### 7.5 Delivery Orders (Outgoing Stock)
- FR-5.1: Pick items for an order.
- FR-5.2: Pack items.
- FR-5.3: Validate → stock decreases automatically.
- Example: Sales order for 10 chairs → delivery reduces chairs by 10.

### 7.6 Internal Transfers
- FR-6.1: Move stock between locations within the company (warehouse↔warehouse, rack↔rack, warehouse↔production floor).
- FR-6.2: Every movement logged in the stock ledger.
- FR-6.3: Total stock unchanged; only location updates.

### 7.7 Stock Adjustments
- FR-7.1: Select product/location, enter physically counted quantity.
- FR-7.2: System computes delta and auto-updates stock.
- FR-7.3: Adjustment logged in the ledger with reason (e.g., damage).

### 7.8 Move History / Stock Ledger
- FR-8.1: Immutable log of every stock-affecting event (receipt, delivery, transfer, adjustment) with product, quantity delta, location, timestamp, actor.

### 7.9 Alerts & Reordering
- FR-9.1: Alert when stock falls below threshold (low stock).
- FR-9.2: Reordering rules trigger indication/notification *(TBD: auto-create draft receipt? notify only?)*.

### 7.10 Settings
- FR-10.1: Warehouse management (create/edit warehouses & locations).

### 7.11 Navigation / IA (from PS)
```
Products
  ├─ Create/update products
  ├─ Stock availability per location
  ├─ Product categories
  └─ Reordering rules
Operations
  ├─ Receipts (Incoming Stock)
  ├─ Delivery Orders (Outgoing Stock)
  ├─ Inventory Adjustment
  ├─ Move History
  ├─ Dashboard
  └─ Settings → Warehouse
Profile Menu (sidebar)
  ├─ My Profile
  └─ Logout
```

---

## 8. Non-Functional Requirements
| Category | Requirement | Notes |
|---|---|---|
| Performance | Dashboard KPIs load in real time / near-real-time | Define target latency — TBD |
| Usability | Replace Excel/manual registers → must be simpler than a spreadsheet | Core value prop |
| Scalability | Multi-warehouse support from day one | |
| Reliability | Stock counts must never go negative/inconsistent | Needs transactional integrity on validate actions |
| Security | OTP-based reset, role-based access | Auth details TBD |
| Auditability | Every stock movement traceable in ledger | FR-8.1 |

## 9. Data Model (Draft Entities)
- **User** (id, name, email, role, password_hash)
- **Product** (id, name, sku, category_id, uom, reorder_min, reorder_max)
- **ProductCategory** (id, name)
- **Warehouse** (id, name)
- **Location** (id, warehouse_id, name, parent_location_id)
- **StockQuant** (product_id, location_id, quantity) — current stock per product per location
- **StockMove / Ledger Entry** (id, product_id, from_location_id, to_location_id, quantity, type[receipt/delivery/internal/adjustment], status, timestamp, actor_id, reference_doc_id)
- **Receipt** (id, supplier, lines[product, qty], status, warehouse/location)
- **DeliveryOrder** (id, customer/reference, lines[product, qty], status)
- **InternalTransfer** (id, from_location, to_location, lines[product, qty], status)
- **StockAdjustment** (id, product_id, location_id, counted_qty, system_qty, delta, reason)

> Relationship: Receipt/Delivery/Transfer/Adjustment are all "documents" that, upon validation, generate one or more StockMove ledger entries and mutate StockQuant.

## 10. Core Workflows

### 10.1 Standard document lifecycle
`Draft → Waiting → Ready → Done` (or `Canceled` at any point before Done)

### 10.2 End-to-end example (from PS)
1. **Receive**: 100 kg Steel from vendor → Stock +100 (Main Store)
2. **Internal Transfer**: Main Store → Production Rack → total unchanged, location updated
3. **Deliver**: 20 (finished goods using steel) → Stock −20
4. **Adjust**: 3 kg steel found damaged → Stock −3
5. All 4 events appear in the Stock Ledger.

## 11. UI/UX References
- Mockup (Excalidraw): https://link.excalidraw.com/l/65VNwvy7c4X/3ENvQFu9o8R
- Follow navigation structure in §7.11 (left sidebar: Products, Operations, Settings, Profile).

## 12. Tech Stack *(TBD — team decision)*
- Backend framework: TBD (native Odoo module vs. custom stack built "Odoo-style")
- Frontend: TBD
- Database: TBD
- Auth/OTP provider: TBD

## 13. Acceptance Criteria (sample — expand per feature)
- [ ] User can sign up, log in, and reset password via OTP.
- [ ] Creating and validating a Receipt increases stock for the correct product/location.
- [ ] Creating and validating a Delivery decreases stock correctly and blocks over-delivery beyond available stock *(confirm rule)*.
- [ ] Internal Transfer moves quantity between locations without changing total stock.
- [ ] Stock Adjustment correctly computes and logs the delta.
- [ ] Dashboard KPIs and filters reflect live data.
- [ ] Low-stock alert fires when quantity crosses threshold.
- [ ] Every stock-affecting action appears in Move History.

## 14. Assumptions & Constraints
- Single company / single currency (assumed, not stated).
- No barcode/hardware scanning required unless added as stretch goal.
- OTP delivery channel (email/SMS) — TBD.

## 15. Milestones & Timeline *(TBD — fill in for hackathon schedule)*
| Milestone | Target Date | Owner |
|---|---|---|
| Requirements finalized | | |
| Data model + auth done | | |
| Core ops (Receipt/Delivery/Transfer/Adjustment) | | |
| Dashboard + alerts | | |
| Polish + demo prep | | |

## 16. Team & Roles *(TBD)*
| Name | Role |
|---|---|
| | |

## 17. Open Questions / Risks
- Exact reordering-rule behavior (auto vs. manual reorder trigger)?
- Delivery over-stock policy — block, warn, or allow negative stock?
- Multi-user concurrency on same stock quant — locking strategy?
- Is this meant to run as a genuine Odoo module (leveraging Odoo's `stock` app) or a standalone app inspired by Odoo's UX? This materially changes the tech stack and effort.
