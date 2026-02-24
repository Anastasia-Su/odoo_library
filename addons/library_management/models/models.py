from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LibraryBook(models.Model):
    _name = "library.book"
    _description = "Library Book"

    name = fields.Char(string="Book Name", required=True)
    author = fields.Char(string="Author")
    published_date = fields.Date(string="Published Date")
    is_available = fields.Boolean(string="Available", default=True)
    
    
class LibraryRent(models.Model):
    _name = "library.rent"
    _description = "Library Rent"

    partner_id = fields.Many2one('res.partner', string="User", required=True)
    book_id = fields.Many2one('library.book', string="Book", required=True)
    rent_date = fields.Date(string="Rent Date", default=fields.Date.today)
    return_date = fields.Date(string="Return Date")

    @api.constrains('book_id', 'return_date')
    def _check_book_availability(self):
        for record in self:
            if self.search([('book_id', '=', record.book_id.id), ('return_date', '=', False), ('id', '!=', record.id)]):
                raise ValidationError("This book is already rented and not returned.")
            
           
