from odoo import models, fields, api


class LibraryRentWizard(models.TransientModel):
    _name = "library.rent.wizard"
    _description = "Rent Book Wizard"

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
        options={'no_create': True, 'no_open': True},
    )

    def action_rent_book(self):
        self.ensure_one()
        # Create rent record (rent_date defaults to today)
        self.env["library.rent"].create(
            {
                "partner_id": self.partner_id.id,
                "book_id": self.book_id.id,
            }
        )
        
        # Show nice toast notification
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': 'Успіх',
                'message': f'Книгу "{self.book_id.name}" видано {self.partner_id.name}!',
                'type': 'success',
            }
        )

        # Close the popup
        return {'type': 'ir.actions.act_window_close'}
        # No need to set is_available=False anymore — compute will handle it!

        # Optional: success message + close wizard
        # return {
        #     "type": "ir.actions.client",
        #     "tag": "display_notification",
        #     "params": {
        #         "title": "Успіх",
        #         "message": f'Книгу "{self.book_id.name}" видано {self.partner_id.name}!',
        #         "type": "success",
        #         "sticky": False,
        #     },
        # }
        
        # return {
        #     'type': 'ir.actions.act_window_close',
        # }
