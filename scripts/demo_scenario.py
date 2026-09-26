# Run inside `odoo shell` against the stocksense database.
# Replays the worked example from StockSense.pdf end-to-end:
#   Receive 100kg Steel -> Internal Transfer -> Deliver 20 -> Adjust -3 (damaged)
# Usage:
#   docker compose exec -T odoo odoo shell -d stocksense --db_host=db --db_user=odoo --db_password=odoo < scripts/demo_scenario.py

steel = env.ref('stocksense.product_steel').product_variant_id

picking_type_in = env.ref('stock.picking_type_in')
picking_type_out = env.ref('stock.picking_type_out')
picking_type_internal = env.ref('stock.picking_type_internal')

supplier_loc = env.ref('stock.stock_location_suppliers')
customer_loc = env.ref('stock.stock_location_customers')
stock_loc = env.ref('stock.stock_location_stock')
rack_loc = env.ref('stocksense.location_production_rack')


def qty_at(product, location):
    quant = env['stock.quant'].search([
        ('product_id', '=', product.id),
        ('location_id', '=', location.id),
    ])
    return sum(quant.mapped('quantity'))


def make_move(picking_type, src, dst, qty):
    picking = env['stock.picking'].create({
        'picking_type_id': picking_type.id,
        'location_id': src.id,
        'location_dest_id': dst.id,
        'move_ids': [(0, 0, {
            'name': steel.name,
            'product_id': steel.id,
            'product_uom_qty': qty,
            'product_uom': steel.uom_id.id,
            'location_id': src.id,
            'location_dest_id': dst.id,
        })],
    })
    picking.action_confirm()
    picking.move_ids.write({'quantity': qty, 'picked': True})
    picking.button_validate()
    return picking


print("=== Before ===")
print("Steel at Main Store (WH/Stock):", qty_at(steel, stock_loc))
print("Steel at Production Rack:", qty_at(steel, rack_loc))

print("\n=== Step 1: Receive 100 kg Steel from vendor ===")
make_move(picking_type_in, supplier_loc, stock_loc, 100)
print("Steel at Main Store:", qty_at(steel, stock_loc))

print("\n=== Step 2: Internal Transfer Main Store -> Production Rack (50 kg) ===")
make_move(picking_type_internal, stock_loc, rack_loc, 50)
print("Steel at Main Store:", qty_at(steel, stock_loc))
print("Steel at Production Rack:", qty_at(steel, rack_loc))

print("\n=== Step 3: Deliver 20 kg Steel to customer ===")
make_move(picking_type_out, rack_loc, customer_loc, 20)
print("Steel at Production Rack:", qty_at(steel, rack_loc))

print("\n=== Step 4: Adjust -3 kg Steel (damaged) at Production Rack ===")
quant = env['stock.quant'].search([
    ('product_id', '=', steel.id),
    ('location_id', '=', rack_loc.id),
], limit=1)
current = quant.quantity
quant.inventory_quantity = current - 3
quant.action_apply_inventory()
print("Steel at Production Rack after adjustment:", qty_at(steel, rack_loc))

print("\n=== Move History (stock.move.line) for Steel ===")
lines = env['stock.move.line'].search([('product_id', '=', steel.id)], order='id')
for l in lines:
    print(f"  {l.move_id.picking_id.name or l.move_id.reference}: {l.location_id.complete_name} -> "
          f"{l.location_dest_id.complete_name}, qty={l.quantity}, state={l.state}")

print("\n=== Final expected: Main Store=50, Production Rack=27 (100-50 -20 -3=27) ===")
env.cr.commit()
