{
    "name": "Library Management",
    "version": "0.1",
    "summary": "Manage books and rentals in a library",
    "description": """
        Custom module to manage library books and their rentals.
        Includes models for books, rents, a wizard for issuing books,
        and a simple REST API endpoint.
    """,
    "author": "Anastasia",
    "website": "https://example.com",
    "category": "Uncategorized",
    "depends": ["base", "contacts"],  # contacts for res.partner
    "data": [
        "security/ir.model.access.csv",
        "demo/demo.xml",
        "views/rent_wizard_views.xml",
        "views/library_book_views.xml",
        "views/library_rent_views.xml",
        "views/library_menu.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
