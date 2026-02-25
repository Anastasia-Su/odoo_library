from odoo import models, fields, api


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
    book_id = fields.Many2one(
        "library.book",
        string="Book",
        required=True,
        domain="[('is_available', '=', True)]",
        # Prevent quick-create and opening the book form from this field
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

        # Create the rent record
        # rent_date will use its default value (fields.Date.today)
        self.env["library.rent"].create(
            {
                "partner_id": self.partner_id.id,
                "book_id": self.book_id.id,
            }
        )

        # Show nice toast notification
        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,  # Target: current logged-in user
            "simple_notification",
            {
                "title": "Success",
                "message": f'Book "{self.book_id.name}" has been rented to {self.partner_id.name}!',
                "type": "success",
            },
        )

        # Close the popup
        return {"type": "ir.actions.act_window_close"}
