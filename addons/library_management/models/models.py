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
                
                
    # ==================== CONSTRAINTS - LIBRARY BOOK ====================

    @api.constrains("name", "author")
    def _check_unique_name_author(self):
        """Book name + author combination must be unique."""
        for record in self:
            if not record.name or not record.author:
                continue

            duplicate = self.search([
                ("name", "=ilike", record.name.strip()),
                ("author", "=ilike", record.author.strip()),
                ("id", "!=", record.id),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    f"A book titled '{record.name}' by '{record.author}' already exists."
                )

    @api.constrains("published_date")
    def _check_published_date_not_future(self):
        """Published date cannot be in the future."""
        today = fields.Date.today()
        for record in self:
            if record.published_date and record.published_date > today:
                raise ValidationError(
                    "Published date cannot be in the future."
                )
                
    
class LibraryRent(models.Model):
    _name = "library.rent"
    _description = "Library Rent"

    partner_id = fields.Many2one(
        "res.partner",
        string="User",
        required=True,
        domain="[('category_id.name', '=', 'Test Users')]",
        options={"no_create": True, "no_open": True},
    )
    book_id = fields.Many2one(
        "library.book",
        string="Book",
        required=True,
        domain="[('is_available', '=', True)]",
        options={"no_create": True, "no_open": True},
    )
    rent_date = fields.Date(string="Rent Date", default=fields.Date.today)
    return_date = fields.Date(string="Return Date")
    

    def action_return_book(self):
        if self.return_date:
            raise ValidationError("This book was already returned.")
    
        self.write({"return_date": fields.Date.today()})
        
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
            "flags": {"reload": True},
        }

    # ==================== CONSTRAINTS - LIBRARY RENT ====================

    @api.constrains("book_id", "return_date")
    def _check_only_one_open_rent_per_book(self):
        """Only one active (open) rental is allowed per book at any time."""
        for record in self:
            if record.return_date:
                continue  # already returned → no need to check

            other_open = self.search([
                ("book_id", "=", record.book_id.id),
                ("return_date", "=", False),
                ("id", "!=", record.id),
            ], limit=1)

            if other_open:
                raise ValidationError(
                    f"This book is already rented and not returned "
                    f"(current renter: {record.book_id.current_renter_id.name or 'unknown'})."
                )

    @api.constrains("rent_date", "return_date")
    def _check_rent_dates_validity(self):
        """Validate logical rules for rent and return dates."""
        today = fields.Date.today()
        for record in self:
            # Rent date cannot be in the future
            if record.rent_date > today:
                raise ValidationError("Rent date cannot be in the future.")

            # Return date cannot be earlier than rent date
            if record.return_date and record.return_date < record.rent_date:
                raise ValidationError("Return date cannot be earlier than rent date.")

            # Return date cannot be in the future (if set)
            if record.return_date and record.return_date > today:
                raise ValidationError("Return date cannot be in the future.")
            