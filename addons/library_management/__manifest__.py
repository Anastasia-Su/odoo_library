{
    "name": "Library Management",
    "version": "1.0",
    "summary": "Manage books and rentals in a library",
    "description": """
        Custom module to manage library books and their rentals.
        Includes models for books, rents, a wizard for issuing books,
        and a simple REST API endpoint.
    """,
    "author": "Anastasia",
    "website": "https://example.com",
    "category": "Uncategorized",
    "depends": ["base", "contacts"],  # Contacts for res.partner
    "data": [
        "security/ir.model.access.csv",
        "demo/demo.xml",
        "views/library_root_menu.xml",
        "views/rent_wizard_views.xml",
        "views/library_book_views.xml",
        "views/library_rent_views.xml",
        "views/library_partner_views.xml",
        "views/library_author_views.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
