import json
from odoo import http
from odoo.http import request, Response


class LibraryController(http.Controller):
    """
    Controller for the library_management module REST API.
    Provides access to library book information in JSON format.
    """

    @http.route("/library/books", auth="public", type="http", methods=["GET"])
    def get_books(self) -> Response:
        books = request.env["library.book"].sudo().search([], order="id asc")
        data = [
            {
                "id": b.id,
                "name": b.name,
                "author_id": b.author_id.name if b.author_id else None,
                "available": b.is_available,
            }
            for b in books
        ]

        # Check Accept header to decide response format
        accept = request.httprequest.headers.get("Accept", "").lower()

        # Return proper JSON API response
        if "application/json" in accept or not accept or "json" in accept:
            return request.make_json_response(data)

        # Otherwise, return simple HTML page for browser
        return request.make_response(
            f"<pre>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>",
            headers={"Content-Type": "text/html"},
        )
