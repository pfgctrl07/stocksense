{
    "name": "StockSense",
    "version": "17.0.1.0.0",
    "summary": "Modular Inventory Management System — Odoo x NMIT Bangalore Hackathon '26",
    "category": "Inventory/Inventory",
    "author": "Team StockSense",
    "depends": ["stock", "product", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/dashboard_views.xml",
        "views/menu_views.xml",
        "data/demo_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "stocksense/static/src/js/dashboard.js",
            "stocksense/static/src/xml/dashboard.xml",
            "stocksense/static/src/scss/dashboard.scss",
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
