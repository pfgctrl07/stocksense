# Run inside `odoo shell` against the stocksense database.
# Demonstrates FEFO (First-Expired-First-Out): two batches of Wood Planks
# with different expiry dates; a delivery with no lot specified should
# automatically consume the SOONER-expiring batch first.
# Usage:
#   docker compose exec -T odoo odoo shell -d stocksense --db_host=db --db_user=odoo --db_password=odoo < scripts/demo_fefo.py

from datetime import timedelta

from odoo import fields

wood = env.ref("stocksense.product_wood_planks").product_variant_id
picking_type_in = env.ref("stock.picking_type_in")
picking_type_out = env.ref("stock.picking_type_out")
supplier_loc = env.ref("stock.stock_location_suppliers")
customer_loc = env.ref("stock.stock_location_customers")
stock_loc = env.ref("stock.stock_location_stock")

lot_soon = env["stock.lot"].create({
    "name": "WPL-BATCH-SOON",
    "product_id": wood.id,
    "expiration_date": fields.Datetime.now() + timedelta(days=2),
})
lot_later = env["stock.lot"].create({
    "name": "WPL-BATCH-LATER",
    "product_id": wood.id,
    "expiration_date": fields.Datetime.now() + timedelta(days=60),
})


def receive_lot(lot, qty):
    picking = env["stock.picking"].create({
        "picking_type_id": picking_type_in.id,
        "location_id": supplier_loc.id,
        "location_dest_id": stock_loc.id,
        "move_ids": [(0, 0, {
            "name": wood.name,
            "product_id": wood.id,
            "product_uom_qty": qty,
            "product_uom": wood.uom_id.id,
            "location_id": supplier_loc.id,
            "location_dest_id": stock_loc.id,
        })],
    })
    picking.action_confirm()
    move = picking.move_ids
    if move.move_line_ids:
        move.move_line_ids[0].write({"lot_id": lot.id, "quantity": qty})
    else:
        move.move_line_ids = [(0, 0, {
            "product_id": wood.id,
            "lot_id": lot.id,
            "quantity": qty,
            "location_id": supplier_loc.id,
            "location_dest_id": stock_loc.id,
        })]
    move.picked = True
    picking.button_validate()
    return picking


print("=== Receiving two batches of Wood Planks ===")
receive_lot(lot_soon, 50)
receive_lot(lot_later, 50)


def qty_in_lot(lot):
    quants = env["stock.quant"].search([
        ("product_id", "=", wood.id),
        ("lot_id", "=", lot.id),
        ("location_id.usage", "=", "internal"),
    ])
    return sum(quants.mapped("quantity"))


print(f"Lot expiring soon ({lot_soon.expiration_date}): {qty_in_lot(lot_soon)}")
print(f"Lot expiring later ({lot_later.expiration_date}): {qty_in_lot(lot_later)}")

print("\n=== Delivering 30 units, NO lot specified (let FEFO decide) ===")
delivery = env["stock.picking"].create({
    "picking_type_id": picking_type_out.id,
    "location_id": stock_loc.id,
    "location_dest_id": customer_loc.id,
    "move_ids": [(0, 0, {
        "name": wood.name,
        "product_id": wood.id,
        "product_uom_qty": 30,
        "product_uom": wood.uom_id.id,
        "location_id": stock_loc.id,
        "location_dest_id": customer_loc.id,
    })],
})
delivery.action_confirm()
delivery.action_assign()  # triggers reservation using the category's FEFO removal strategy
print("Reserved from lots:", [(l.lot_id.name, l.quantity) for l in delivery.move_ids.move_line_ids])
delivery.move_ids.picked = True
delivery.button_validate()

print(f"\nAfter delivery: soon-expiring lot = {qty_in_lot(lot_soon)}, later lot = {qty_in_lot(lot_later)}")
print("Expected: soon-expiring lot dropped from 50 to 20 (30 consumed), later lot untouched at 50 -> FEFO worked" if qty_in_lot(lot_soon) == 20 and qty_in_lot(lot_later) == 50 else "UNEXPECTED RESULT - check removal strategy")
env.cr.commit()
