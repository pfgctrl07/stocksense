from datetime import timedelta

from odoo import api, fields, models

REORDER_WINDOW_DAYS = 30
LEAD_TIME_DAYS = 14
LOW_DAYS_THRESHOLD = 7


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
                if q in (p.categ_id.name or "").lower():
                    return True
                quants = self.env["stock.quant"].search([
                    ("product_id", "=", p.id),
                    ("quantity", ">", 0),
                ])
                return any(q in (loc.complete_name or "").lower() for loc in quants.mapped("location_id"))

            products = products.filtered(matches)

        result = []
        for p in products:
            quants = self.env["stock.quant"].search([
                ("product_id", "=", p.id),
                ("quantity", ">", 0),
                ("location_id.usage", "=", "internal"),
            ])
            locations = quants.mapped("location_id.complete_name")
            signal = self._reorder_signal(p)
            primary_location = self._get_primary_location(p)
            result.append({
                "id": p.id,
                "name": p.name,
                "sku": p.default_code or "",
                "category": p.categ_id.name,
                "locations": ", ".join(locations) if locations else "—",
                "qty_available": p.qty_available,
                "uom": p.uom_id.name,
                "reorder": signal,
                "primary_location_id": primary_location.id,
                "primary_location_name": primary_location.complete_name,
            })
        return result

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
