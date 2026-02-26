from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
