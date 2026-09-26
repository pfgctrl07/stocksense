from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    ss_x = fields.Integer(string="Floor X", help="Cartesian floor position (X). Part of the 3-number slot address.")
    ss_y = fields.Integer(string="Floor Y", help="Cartesian floor position (Y). Part of the 3-number slot address.")
    ss_z = fields.Integer(string="Height Level", help="Shelf/rack height level. 3rd number of the slot address.")
    ss_is_slot = fields.Boolean(string="Storage Slot", help="Marks this location as an addressable storage slot for the layout optimizer.")

    def ss_coordinate_label(self):
        self.ensure_one()
        return f"({self.ss_x}, {self.ss_y}, {self.ss_z})"
