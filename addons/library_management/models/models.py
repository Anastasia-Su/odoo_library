from odoo import models, fields, api
from odoo.exceptions import ValidationError
from typing import Any


class LibraryBook(models.Model):
    """
    Main model representing a book in the library.
    Contains basic book information and availability/renter fields.
    """

    _name = "library.book"
    _description = "Library Book"
    _order = "name"  # Default sorting in lists

    name = fields.Char(string="Book Name", required=True, size=50)

    # Many2one instead of Char: better data consistency, reuse of authors, autocompletio
    author_id = fields.Many2one(
        "library.author",
        string="Author",
        required=True,
        ondelete="restrict",
        # These options prevent quick-creation / quick-editing from this field
        options={"no_create": True, "no_open": True},
    )
    published_date = fields.Date(string="Published Date")
    is_available = fields.Boolean(string="Available", default=True)

    # New: One2many to all rents (history)
    rent_ids = fields.One2many(
        "library.rent",
        "book_id",
        string="Rent History",
        help="All rental records for this book (past and current)",
    )

    # New: Current active renter (computed Many2one)
    current_renter_id = fields.Many2one(
        "res.partner",
        string="Current Renter",
        compute="_compute_current_renter",
        store=False,
        readonly=True,
        help="Partner who currently rents this book (if any)",
    )

    # Stored computed field, important for fast filtering, searching
    is_available = fields.Boolean(
        string="Available",
        compute="_compute_is_available",
        store=True,  # Allows using this field in filters, domains, search views
        default=True,
        readonly=True,
    )

    # COMPUTE METHODS

    @api.depends("rent_ids.return_date")
    def _compute_is_available(self) -> None:
        """
        Book is available when it has no open (not returned) rental records.
        """

        for book in self:
            open_rents = book.rent_ids.filtered(lambda r: not r.return_date)
            book.is_available = len(open_rents) == 0

    @api.depends("rent_ids.partner_id", "rent_ids.return_date")
    def _compute_current_renter(self) -> None:
        """
        Computes the current renter of the book.
        - Looks only at open (not returned) rental records (return_date is False/None)
        - If no open rents → no renter (False)
        - If one open rent → that partner is the current renter
        - If multiple open rents exist (should never happen due to constraint) →
        takes the most recent one based on rent_date
        """

        for book in self:
            open_rents = book.rent_ids.filtered(lambda r: not r.return_date)

            if not open_rents:
                book.current_renter_id = False
                continue

            latest = open_rents.sorted(
                key=lambda r: r.rent_date or fields.Date.today(), reverse=True
            )[:1]
            book.current_renter_id = latest.partner_id

    # CONSTRAINTS

    @api.constrains("name", "author_id")
    def _check_unique_name_author(self) -> None:
        """
        Ensures that the combination of book title + author is unique.
        Case-insensitive comparison + strip whitespace.
        """

        for record in self:
            if not record.name or not record.author_id:
                continue

            duplicate = self.search(
                [
                    ("name", "=ilike", record.name.strip()),
                    ("author_id", "=", record.author_id.id),
                    ("id", "!=", record.id),
                ],
                limit=1,
            )

            if duplicate:
                raise ValidationError(
                    f"A book titled '{record.name}' by '{record.author_id.name}' already exists."
                )

    @api.constrains("published_date")
    def _check_published_date_not_future(self) -> None:
        """Published date cannot be in the future."""
        
        today = fields.Date.today()
        for record in self:
            if record.published_date and record.published_date > today:
                raise ValidationError("Published date cannot be in the future.")

    @api.constrains("name")
    def _check_name_length(self) -> None:
        """
        Validate that the book name is between 2 and 50 characters long
        after removing leading/trailing spaces.
        """
        
        for record in self:
            if not record.name:
                continue

            cleaned = record.name.strip()
            length = len(cleaned)

            if length < 2:
                raise ValidationError(
                    "Book name must be at least 2 characters long "
                    "(after removing extra spaces)."
                )
            # No need to check upper limit here — size=50 is enforced by DB


class LibraryRent(models.Model):
    """
    Rental / borrowing record.
    One record = one borrowing event (can be open or already returned).
    """

    _name = "library.rent"
    _description = "Library Rent"
    _order = "rent_date desc"

    partner_id = fields.Many2one(
        "res.partner",
        string="User",
        required=True,
        domain="[('category_id.name', '=', 'Test Users')]",
        options={"no_create": True, "no_open": True},
        help="Person who borrowed the book. Only partners from 'Test Users' category.",
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

    def action_return_book(self) -> dict[str, Any]:
        """
        Marks the rental as returned (sets return_date = today).
        Prevents double-return and refreshes the form view.
        """

        if self.return_date:
            raise ValidationError("This book was already returned.")

        self.write({"return_date": fields.Date.today()})

        # Return action to reload current form view (makes "Return" button disappear)
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
            "flags": {"reload": True},
        }

    # CONSTRAINTS

    @api.constrains("book_id", "return_date")
    def _check_only_one_open_rent_per_book(self) -> None:
        """Only one active (open) rental is allowed per book at any time."""

        for record in self:
            if record.return_date:
                continue  # Already returned - skip

            other_open = self.search(
                [
                    ("book_id", "=", record.book_id.id),
                    ("return_date", "=", False),
                    ("id", "!=", record.id),
                ],
                limit=1,
            )

            if other_open:
                raise ValidationError(
                    f"This book is already rented and not returned "
                    f"(current renter: {record.book_id.current_renter_id.name or 'unknown'})."
                )

    @api.constrains("rent_date", "return_date")
    def _check_rent_dates_validity(self) -> None:
        """
        Date consistency rules:
        - rent_date cannot be future
        - return_date cannot be before rent_date
        - return_date cannot be in future (if set)
        """

        today = fields.Date.today()
        for record in self:
            if record.rent_date > today:
                raise ValidationError("Rent date cannot be in the future.")

            if record.return_date and record.return_date < record.rent_date:
                raise ValidationError("Return date cannot be earlier than rent date.")

            if record.return_date and record.return_date > today:
                raise ValidationError("Return date cannot be in the future.")


class LibraryAuthor(models.Model):
    """
    Simple model for authors.
    Mainly used to avoid duplicating author names and enable selection from dropdown.
    """

    _name = "library.author"
    _description = "Library Author"
    _order = "name"

    name = fields.Char(
        string="Author Name",
        required=True,
        size=100,
    )

    @api.constrains("name")
    def _check_unique_name_normalized(self) -> None:
        """
        Ensure author names are unique when compared case-insensitively
        and ignoring leading/trailing spaces.

        This constraint searches using case-insensitive match on the original name
        field to avoid timing issues with the stored computed field.
        """

        for record in self:
            if not record.name:
                continue
            normalized = record.name.strip().lower()
            if not normalized:
                continue

            # Search for duplicates using case-insensitive exact match
            duplicate = self.with_context(active_test=False).search(
                [
                    ("name", "=ilike", normalized),
                    ("id", "!=", record.id),
                ],
                limit=1,
            )

            if duplicate:
                raise ValidationError(
                    f"Author '{record.name}' already exists "
                    "(names are compared case-insensitive, ignoring extra spaces)."
                )

    @api.constrains("name")
    def _check_name_length(self) -> None:
        """
        Validate that the author name is between 2 and 100 characters long
        after removing leading/trailing spaces.
        """
        for record in self:
            if not record.name:
                continue

            cleaned = record.name.strip()
            length = len(cleaned)

            if length < 2:
                raise ValidationError(
                    "Author name must be at least 2 characters long "
                    "(after removing extra spaces)."
                )
            # No need to check upper limit here — size=100 is enforced by DB
