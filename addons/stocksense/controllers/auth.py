from odoo import http
from odoo.http import request


class StockSenseAuthController(http.Controller):

    @http.route("/stocksense/forgot", type="http", auth="public", methods=["GET"], csrf=True)
    def forgot_get(self, **kw):
        return request.render("stocksense.forgot_password_page", {"step": "request"})

    @http.route("/stocksense/forgot/send", type="http", auth="public", methods=["POST"], csrf=True)
    def forgot_send(self, login=None, **kw):
        user = request.env["res.users"].sudo().search([("login", "=", login)], limit=1)
        if not user:
            return request.render("stocksense.forgot_password_page", {
                "step": "request",
                "error": "No account found with that email.",
            })
        code = request.env["stocksense.otp"].sudo()._generate(login)
        return request.render("stocksense.forgot_password_page", {
            "step": "verify",
            "login": login,
            "demo_otp": code,
        })

    @http.route("/stocksense/forgot/reset", type="http", auth="public", methods=["POST"], csrf=True)
    def forgot_reset(self, login=None, code=None, password=None, confirm_password=None, **kw):
        if password != confirm_password:
            return request.render("stocksense.forgot_password_page", {
                "step": "verify",
                "login": login,
                "error": "Passwords do not match.",
            })
        ok = request.env["stocksense.otp"].sudo()._verify(login, code)
        if not ok:
            return request.render("stocksense.forgot_password_page", {
                "step": "verify",
                "login": login,
                "error": "Invalid or expired OTP.",
            })
        user = request.env["res.users"].sudo().search([("login", "=", login)], limit=1)
        user.sudo().write({"password": password})
        return request.render("stocksense.forgot_password_page", {"step": "done"})
