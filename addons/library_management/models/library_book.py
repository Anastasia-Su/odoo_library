from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LibraryBook(models.Model):
    """
    Main model representing a book in the library.
    Contains basic book information and availability/renter fields.
    """

    _name = "library.book"
    _description = "Library Book"
    _order = "name"  # Default sorting in lists

    name = fields.Char(string="Book Name", required=True, size=50)

    # To ensure better data quality, prevent typos, enable autocomplete/dropdown selection,
    # and allow future extensions (e.g. author bio, books count),
    # this implementation uses a Many2one relation to a separate 'library.author' model.
    # This is a conscious design improvement over the literal Char requirement.
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

    @api.depends("rent_ids", "rent_ids.return_date")
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
