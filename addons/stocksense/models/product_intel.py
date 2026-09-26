from datetime import timedelta

from odoo import api, fields, models

REORDER_WINDOW_DAYS = 30
LEAD_TIME_DAYS = 14
LOW_DAYS_THRESHOLD = 7
STALE_DAYS_THRESHOLD = 14


class StockSenseProductIntel(models.AbstractModel):
    _name = "stocksense.product_intel"
    _description = "StockSense Product Intelligence (search, timeline, quick actions, reorder signal)"

    @api.model
    def _reorder_signal(self, product):
        """Velocity-based reorder signal: real math over actual move history,
        not a fixed threshold. avg_daily_outflow = outgoing qty over the last
        REORDER_WINDOW_DAYS / REORDER_WINDOW_DAYS."""
        since = fields.Datetime.now() - timedelta(days=REORDER_WINDOW_DAYS)
        lines = self.env["stock.move.line"].search([
            ("product_id", "=", product.id),
            ("state", "=", "done"),
            ("picking_id.picking_type_id.code", "=", "outgoing"),
            ("date", ">=", since),
        ])
        total_out = sum(lines.mapped("quantity"))
        avg_daily = total_out / REORDER_WINDOW_DAYS if REORDER_WINDOW_DAYS else 0.0
        qty_available = product.qty_available

        if avg_daily > 0:
            days_left = qty_available / avg_daily
            suggested_qty = max(0.0, (avg_daily * LEAD_TIME_DAYS) - qty_available)
            alert = days_left < LOW_DAYS_THRESHOLD
        else:
            days_left = None
            suggested_qty = 0.0
            alert = qty_available <= 0

        return {
            "avg_daily_outflow": round(avg_daily, 2),
            "days_left": round(days_left, 1) if days_left is not None else None,
            "suggested_reorder_qty": round(suggested_qty, 1),
            "alert": alert,
        }

    @api.model
    def _expiry_info(self, product):
        """Nearest-expiring in-stock batch for this product, or '-' if the
        product isn't lot/expiry-tracked or has no batches on hand."""
        if not product.use_expiration_date:
            return {"nearest_expiry": "-", "is_expired": False, "lot_name": None}

        quants = self.env["stock.quant"].search([
            ("product_id", "=", product.id),
            ("quantity", ">", 0),
            ("location_id.usage", "=", "internal"),
            ("lot_id", "!=", False),
        ])
        lots_with_stock = quants.mapped("lot_id").filtered("expiration_date")
        if not lots_with_stock:
            return {"nearest_expiry": "-", "is_expired": False, "lot_name": None}

        nearest = min(lots_with_stock, key=lambda l: l.expiration_date)
        is_expired = nearest.expiration_date <= fields.Datetime.now()
        return {
            "nearest_expiry": nearest.expiration_date.strftime("%Y-%m-%d"),
            "is_expired": is_expired,
            "lot_name": nearest.name,
        }

    @api.model
    def _movement_info(self, product):
        """Days since this product last moved (receipt/delivery/transfer/
        adjustment). None ever moved -> flagged as stale with no date."""
        last_line = self.env["stock.move.line"].search([
            ("product_id", "=", product.id),
            ("state", "=", "done"),
        ], order="date desc", limit=1)

        if not last_line:
            return {"last_movement": None, "days_idle": None, "stale": True}

        days_idle = (fields.Datetime.now() - last_line.date).days
        return {
            "last_movement": last_line.date.strftime("%Y-%m-%d"),
            "days_idle": days_idle,
            "stale": days_idle >= STALE_DAYS_THRESHOLD,
        }

    @api.model
    def _product_row(self, p):
        quants = self.env["stock.quant"].search([
            ("product_id", "=", p.id),
            ("quantity", ">", 0),
            ("location_id.usage", "=", "internal"),
        ])
        locations = quants.mapped("location_id.complete_name")
        primary_location = self._get_primary_location(p)
        return {
            "id": p.id,
            "name": p.name,
            "sku": p.default_code or "",
            "barcode": p.barcode or "",
            "category": p.categ_id.name,
            "locations": ", ".join(locations) if locations else "—",
            "qty_available": p.qty_available,
            "uom": p.uom_id.name,
            "reorder": self._reorder_signal(p),
            "primary_location_id": primary_location.id,
            "primary_location_name": primary_location.complete_name,
            "expiry": self._expiry_info(p),
            "movement": self._movement_info(p),
        }

    @api.model
    def search_products(self, query=None, category_id=None):
        domain = [("type", "=", "product")]
        if category_id:
            domain.append(("categ_id", "=", category_id))

        products = self.env["product.product"].search(domain)

        if query:
            q = query.lower().strip()

            def matches(p):
                if q in (p.name or "").lower():
                    return True
                if q in (p.default_code or "").lower():
                    return True
                if q in (p.barcode or "").lower():
                    return True
                if q in (p.categ_id.name or "").lower():
                    return True
                quants = self.env["stock.quant"].search([
                    ("product_id", "=", p.id),
                    ("quantity", ">", 0),
                ])
                return any(q in (loc.complete_name or "").lower() for loc in quants.mapped("location_id"))

            products = products.filtered(matches)

        return [self._product_row(p) for p in products]

    @api.model
    def lookup_by_barcode(self, barcode):
        """Used by the camera/barcode scanner: exact match on the product's
        barcode field. Returns None if nothing matches."""
        product = self.env["product.product"].search([("barcode", "=", barcode)], limit=1)
        if not product:
            return None
        return self._product_row(product)

    @api.model
    def get_product_timeline(self, product_id):
        lines = self.env["stock.move.line"].search([
            ("product_id", "=", product_id),
            ("state", "=", "done"),
        ], order="date desc", limit=50)
        return [{
            "date": l.date and l.date.strftime("%Y-%m-%d %H:%M") or "",
            "reference": l.move_id.picking_id.name or l.move_id.reference or "Adjustment",
            "from_location": l.location_id.complete_name,
            "to_location": l.location_dest_id.complete_name,
            "qty": l.quantity,
        } for l in lines]

    @api.model
    def _get_primary_location(self, product):
        quant = self.env["stock.quant"].search([
            ("product_id", "=", product.id),
            ("location_id.usage", "=", "internal"),
            ("quantity", ">", 0),
        ], order="quantity desc", limit=1)
        if quant:
            return quant.location_id
        return self.env.ref("stock.stock_location_stock")

    @api.model
    def quick_adjust(self, product_id, delta):
        """One-tap stock update / damage-wastage button both call this:
        positive delta = quick add, negative delta = quick remove or damage."""
        product = self.env["product.product"].browse(product_id)
        location = self._get_primary_location(product)
        quant = self.env["stock.quant"]._gather(product, location, strict=True)
        if not quant:
            quant = self.env["stock.quant"].create({
                "product_id": product.id,
                "location_id": location.id,
            })
        else:
            quant = quant[:1]
        new_qty = max(0.0, quant.quantity + delta)
        quant.inventory_quantity = new_qty
        quant.action_apply_inventory()
        return {"new_qty": product.qty_available}

    @api.model
    def apply_physical_count(self, product_id, location_id, counted_qty):
        """Mismatch detection: compares system quantity vs a physical count
        the user enters, then commits the adjustment."""
        product = self.env["product.product"].browse(product_id)
        location = self.env["stock.location"].browse(location_id)
        quant = self.env["stock.quant"]._gather(product, location, strict=True)
        if not quant:
            quant = self.env["stock.quant"].create({
                "product_id": product.id,
                "location_id": location.id,
            })
        else:
            quant = quant[:1]
        system_qty = quant.quantity
        diff = counted_qty - system_qty
        quant.inventory_quantity = counted_qty
        quant.action_apply_inventory()
        return {"system_qty": system_qty, "counted_qty": counted_qty, "diff": diff}

    @api.model
    def get_daily_summary(self):
        """End-of-day report: what came in, what went out, what's stale,
        product by product."""
        today_start = fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        products = self.env["product.product"].search([("type", "=", "product")])

        rows = []
        total_in = 0.0
        total_out = 0.0
        for p in products:
            lines_today = self.env["stock.move.line"].search([
                ("product_id", "=", p.id),
                ("state", "=", "done"),
                ("date", ">=", today_start),
            ])
            received = sum(lines_today.filtered(
                lambda l: l.picking_id.picking_type_id.code == "incoming"
            ).mapped("quantity"))
            delivered = sum(lines_today.filtered(
                lambda l: l.picking_id.picking_type_id.code == "outgoing"
            ).mapped("quantity"))
            movement = self._movement_info(p)
            rows.append({
                "name": p.name,
                "received_today": received,
                "delivered_today": delivered,
                "current_qty": p.qty_available,
                "stale": movement["stale"],
                "days_idle": movement["days_idle"],
            })
            total_in += received
            total_out += delivered

        return {
            "date": fields.Date.today().strftime("%Y-%m-%d"),
            "total_received_today": total_in,
            "total_delivered_today": total_out,
            "products": rows,
        }

    @api.model
    def get_transfer_suggestions(self):
        """Simple, explainable heuristic: if one internal location holds
        most of a product's stock (>=75%) while another holds very little
        (<=25%), suggest rebalancing. Not a real optimizer — a starting
        signal, deliberately scoped down given time constraints."""
        products = self.env["product.product"].search([("type", "=", "product")])
        suggestions = []
        for p in products:
            quants = self.env["stock.quant"].search([
                ("product_id", "=", p.id),
                ("quantity", ">", 0),
                ("location_id.usage", "=", "internal"),
            ])
            by_location = {}
            for q in quants:
                by_location[q.location_id] = by_location.get(q.location_id, 0.0) + q.quantity
            if len(by_location) < 2:
                continue

            max_loc = max(by_location, key=by_location.get)
            min_loc = min(by_location, key=by_location.get)
            max_qty = by_location[max_loc]
            min_qty = by_location[min_loc]
            total = sum(by_location.values())

            if total and max_qty >= total * 0.75 and min_qty <= total * 0.25:
                move_qty = round((max_qty - min_qty) / 2, 1)
                if move_qty > 0:
                    suggestions.append({
                        "product": p.name,
                        "from_location": max_loc.complete_name,
                        "to_location": min_loc.complete_name,
                        "suggested_qty": move_qty,
                        "reason": (
                            f"{max_loc.complete_name} holds {max_qty:g} vs "
                            f"{min_qty:g} at {min_loc.complete_name} — rebalance to "
                            "reduce stockout risk at the smaller location."
                        ),
                    })
        return suggestions

    @api.model
    def get_warehouse_layout(self):
        """All addressable storage slots with their (x, y, z) Cartesian
        address and whatever product currently occupies them, if any."""
        slots = self.env["stock.location"].search([("ss_is_slot", "=", True)])
        rows = []
        for loc in slots:
            quants = self.env["stock.quant"].search([
                ("location_id", "=", loc.id),
                ("quantity", ">", 0),
            ], limit=1)
            rows.append({
                "location_id": loc.id,
                "name": loc.name,
                "x": loc.ss_x,
                "y": loc.ss_y,
                "z": loc.ss_z,
                "occupant": quants.product_id.name if quants else None,
            })
        rows.sort(key=lambda r: (r["z"], r["x"] + r["y"]))
        return rows

    @api.model
    def get_optimization_suggestions(self):
        """Space optimization: highest-velocity products should sit in the
        most accessible slots (low height first, then closest to origin).
        This is an explainable ranking heuristic, not a real bin-packing
        optimizer — it reuses the same velocity math as the reorder signal."""
        products = self.env["product.product"].search([("type", "=", "product")])
        products_with_stock = products.filtered(lambda p: p.qty_available > 0)

        ranked_products = sorted(
            products_with_stock,
            key=lambda p: self._reorder_signal(p)["avg_daily_outflow"],
            reverse=True,
        )

        slots = self.env["stock.location"].search([("ss_is_slot", "=", True)])
        ranked_slots = sorted(slots, key=lambda l: (l.ss_z, l.ss_x + l.ss_y))

        suggestions = []
        for product, slot in zip(ranked_products, ranked_slots):
            velocity = self._reorder_signal(product)["avg_daily_outflow"]
            current = self._get_primary_location(product)
            if velocity > 0:
                reason = (
                    f"High-velocity item ({velocity:g}/day) — placed at height "
                    f"{slot.ss_z} for fast access."
                )
            else:
                reason = "Low/no recent movement — placed further from the access point to free up prime slots."
            suggestions.append({
                "product": product.name,
                "velocity": velocity,
                "current_location": current.complete_name,
                "suggested_slot": slot.name,
                "suggested_coordinate": f"({slot.ss_x}, {slot.ss_y}, {slot.ss_z})",
                "reason": reason,
            })
        return suggestions
