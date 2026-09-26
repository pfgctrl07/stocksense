from odoo import api, models

LOW_STOCK_THRESHOLD = 10


class StockSenseDashboard(models.AbstractModel):
    _name = "stocksense.dashboard"
    _description = "StockSense Dashboard Data Provider"

    @api.model
    def get_kpis(self):
        Picking = self.env["stock.picking"]
        Quant = self.env["stock.quant"]

        in_stock_quants = Quant.search([
            ("quantity", ">", 0),
            ("location_id.usage", "=", "internal"),
        ])
        total_products_in_stock = len(in_stock_quants.mapped("product_id"))

        storable_products = self.env["product.product"].search([("type", "=", "product")])
        low_or_out = storable_products.filtered(lambda p: p.qty_available <= LOW_STOCK_THRESHOLD)

        def pending_count(picking_type_code):
            return Picking.search_count([
                ("picking_type_id.code", "=", picking_type_code),
                ("state", "not in", ["done", "cancel"]),
            ])

        return {
            "total_products_in_stock": total_products_in_stock,
            "low_stock_count": len(low_or_out),
            "pending_receipts": pending_count("incoming"),
            "pending_deliveries": pending_count("outgoing"),
            "internal_transfers": pending_count("internal"),
        }

    @api.model
    def get_filter_options(self):
        warehouses = self.env["stock.warehouse"].search([])
        categories = self.env["product.category"].search([])
        return {
            "warehouses": [{"id": w.id, "name": w.name} for w in warehouses],
            "categories": [{"id": c.id, "name": c.name} for c in categories],
        }

    @api.model
    def get_documents(self, filters=None):
        filters = filters or {}
        domain = []

        doc_type = filters.get("doc_type")
        if doc_type and doc_type != "all":
            domain.append(("picking_type_id.code", "=", doc_type))

        status = filters.get("status")
        if status and status != "all":
            domain.append(("state", "=", status))

        warehouse_id = filters.get("warehouse_id")
        if warehouse_id:
            domain.append(("picking_type_id.warehouse_id", "=", warehouse_id))

        category_id = filters.get("category_id")
        if category_id:
            domain.append(("move_ids.product_id.categ_id", "=", category_id))

        pickings = self.env["stock.picking"].search(domain, limit=50, order="id desc")
        return [{
            "id": p.id,
            "name": p.name,
            "type": p.picking_type_id.code,
            "state": p.state,
            "warehouse": p.picking_type_id.warehouse_id.name,
            "scheduled_date": p.scheduled_date and p.scheduled_date.strftime("%Y-%m-%d %H:%M") or "",
        } for p in pickings]
