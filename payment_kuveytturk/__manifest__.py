{
    "name": "KuveytTürk Payment Acquirer",
    "summary": """Integrating KuveytTürk Payment Gateway service with Odoo. The module allows the customers to make payments for their ecommerce orders using KuveytTürk Payment Gateway service.""",
    "description": """KuveytTürk Payment Gateway Payment Acquirer""",
    "version": "14.0.1.0.0",
    "author": "Boraq-Group",
    "website": "https://boraq-group.com",
    "category": "Ecommerce",
    "depends": ["payment"],
    "data":  [
        "views/payment_acquirer.xml",
        "views/payment_kuveytturk_templates.xml",
        "data/kuveytturk_payment_data.xml",
    ],
    "assets": {
    "web.assets_backend": ["/payment_kuveytturk/static/src/js/cardjs.js","/payment_kuveytturk/static/src/js/kuveytturk.js"],
    "web.assets_qweb": ["path to .xml, like /module_name/static/src/...",...],
     },
    "images": ['static/description/banner.png'],
    "application": True,
    "installable": True,
    "price": 199.0,
    "currency": "EUR",
    "pre_init_hook": "pre_init_check",
}
