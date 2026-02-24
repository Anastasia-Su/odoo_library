from odoo import http
from odoo.http import request


class LibraryController(http.Controller):
    """
    Controller for the library_management module REST API.
    Provides access to library book information in JSON format.
    """

    @http.route("/library/books", auth="public", type="json")
    def get_books(self):
        books = request.env["library.book"].sudo().search([])
        return [
            {"name": b.name, "author": b.author, "available": b.is_available}
            for b in books
        ]
