import json
from odoo import http
from odoo.http import request


class LibraryController(http.Controller):
    """
    Controller for the library_management module REST API.
    Provides access to library book information in JSON format.
    """

    @http.route("/library/books", auth="public", type="http", methods=["GET"])
    def get_books(self):
        books = request.env["library.book"].sudo().search([])
        data = [
            {
                "id": b.id,
                "name": b.name,
                "author_id": b.author_id.name if b.author_id else None,
                "available": b.is_available,
            }
            for b in books
        ]

        # Return JSON
        accept = request.httprequest.headers.get("Accept", "").lower()
        if "application/json" in accept or not accept or "json" in accept:
            return request.make_json_response(data)

        # Otherwise, return simple HTML page for browser
        return request.make_response(
            f"<pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>",
            headers={"Content-Type": "text/html"},
        )
