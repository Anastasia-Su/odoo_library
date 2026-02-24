from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LibraryBook(models.Model):
    _name = "library.book"
    _description = "Library Book"

    name = fields.Char(string="Book Name", required=True)
    author = fields.Char(string="Author")
    published_date = fields.Date(string="Published Date")
    is_available = fields.Boolean(string="Available", default=True)

    # New: One2many to all rents (history)
    rent_ids = fields.One2many("library.rent", "book_id", string="Rent History")

    # New: Current active renter (computed Many2one)
    current_renter_id = fields.Many2one(
        "res.partner",
        string="Current Renter",
        compute="_compute_current_renter",
        store=False,  # read-only, no need to store unless you search/group by it often
        readonly=True,
    )

    # New: Is available? Computed from open rents
    is_available = fields.Boolean(
        string="Available",
        compute="_compute_is_available",
        store=True,  # store=True so it's fast for lists/filters/search
        default=True,
        readonly=True,
    )

    @api.depends("rent_ids.return_date")
    def _compute_is_available(self):
        for book in self:
            # Book is NOT available if there's at least one rent with return_date=False
            open_rents = book.rent_ids.filtered(lambda r: not r.return_date)
            book.is_available = len(open_rents) == 0

    @api.depends("rent_ids.partner_id", "rent_ids.return_date")
    def _compute_current_renter(self):
        for book in self:
            open_rent = book.rent_ids.filtered(lambda r: not r.return_date)
            if open_rent:
                # Take the most recent open rent (sorted by rent_date desc)
                latest_open = open_rent.sorted("rent_date", reverse=True)[:1]
                book.current_renter_id = latest_open.partner_id
            else:
                book.current_renter_id = False


class LibraryRent(models.Model):
    _name = "library.rent"
    _description = "Library Rent"

    partner_id = fields.Many2one(
        "res.partner",
        string="User",
        required=True,
        domain="[('category_id.name', '=', 'Test Users')]",
        options={'no_create': True, 'no_open': True}
    )
    book_id = fields.Many2one("library.book", string="Book", required=True, domain="[('is_available', '=', True)]")
    rent_date = fields.Date(string="Rent Date", default=fields.Date.today)
    return_date = fields.Date(string="Return Date")

    def action_return_book(self):
        self.write({"return_date": fields.Date.today()})
        # is_available recomputes automatically on book
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Успіх",
                "message": "Книгу повернуто!",
                "type": "success",
            },
        }

    @api.constrains("book_id", "return_date")
    def _check_book_availability(self):
        for record in self:
            if not record.return_date:  # only check when creating/open rent
                domain = [
                    ("book_id", "=", record.book_id.id),
                    ("return_date", "=", False),
                    ("id", "!=", record.id or record._origin.id),
                ]
                if self.search_count(domain):
                    raise ValidationError("Ця книга вже видана і не повернута.")
            # if self.search([('book_id', '=', record.book_id.id), ('return_date', '=', False), ('id', '!=', record.id)]):
            #     raise ValidationError("This book is already rented and not returned.")
