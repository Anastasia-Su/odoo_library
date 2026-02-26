from odoo import models, fields, api
from odoo.exceptions import ValidationError
from typing import Any


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
