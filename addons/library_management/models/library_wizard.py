from odoo import models, fields
from odoo.exceptions import ValidationError


class LibraryRentWizard(models.TransientModel):
    """
    Transient wizard model used to rent out a book to a user.
    Opens as a popup form allowing quick selection of user and book,
    then creates a library.rent record on confirmation.
    """

    _name = "library.rent.wizard"
    _description = "Rent Book Wizard"

    partner_id = fields.Many2one(
        "res.partner",
        string="User",
        required=True,
        domain="[('category_id.name', '=', 'Test Users')]",
        # Prevent quick-create and opening the partner form from this field
        options={"no_create": True, "no_open": True},
    )

    def action_rent_book(self) -> dict[str, str]:
        """
        Main action triggered when user clicks "Rent Book" button.

        Responsibilities:
        - Creates a new library.rent record with selected user and book
        - Sends a success notification (toast) to the current user
        - Closes the wizard popup

        Returns:
            dict: Action to close the current wizard window
        """

        self.ensure_one()  # Safety: make sure we are working with a single wizard record

        # Retrieve the book ID from the context
        book_id = self.env.context.get("active_id")
        active_model = self.env.context.get("active_model")

        if not book_id or active_model != "library.book":
            raise ValidationError(
                "This wizard can only be opened from a book form.\n"
                "Please click the 'Rent Book' button directly on a book record."
            )

        book = self.env["library.book"].browse(book_id)
        if not book.exists():
            raise ValidationError("Book not found.")
        if not book.is_available:
            raise ValidationError(
                f"The book '{book.name}' is already rented to another user."
            )

        # Create the rental record
        rent = self.env["library.rent"].create(
            {
                "partner_id": self.partner_id.id,
                "book_id": book.id,
            }
        )

        # Show nice toast notification
        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "simple_notification",
            {
                "title": "Success",
                "message": f'Book "{book.name}" has been rented to {self.partner_id.name}.',
                "type": "success",
            },
        )

        # Close the popup
        return {"type": "ir.actions.act_window_close"}
