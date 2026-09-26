import random
from datetime import timedelta

from odoo import api, fields, models

OTP_VALID_MINUTES = 10


class StockSenseOtp(models.Model):
    _name = "stocksense.otp"
    _description = "StockSense OTP (password reset)"

    login = fields.Char(required=True, index=True)
    code = fields.Char(required=True)
    used = fields.Boolean(default=False)

    @api.model
    def _generate(self, login):
        code = "%06d" % random.randint(0, 999999)
        self.create({"login": login, "code": code})
        return code

    @api.model
    def _verify(self, login, code):
        since = fields.Datetime.now() - timedelta(minutes=OTP_VALID_MINUTES)
        otp = self.search([
            ("login", "=", login),
            ("code", "=", code),
            ("used", "=", False),
            ("create_date", ">=", since),
        ], limit=1, order="create_date desc")
        if otp:
            otp.used = True
            return True
        return False
