from datetime import timedelta
from psycopg2.errors import UniqueViolation
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields



class TestLibraryRent(TransactionCase):
    """
    Test suite for library book and rent functionality.

    Includes tests for:
    - Unique book constraints (name + author)
    - Published date validation
    - Renting books
    - Single open rent per book
    - Rent and return date validations
    """

    @classmethod
    def setUpClass(cls):
        """Set up test data for all test methods."""
        
        super().setUpClass()

        # Create category "Test Users"
        cls.test_category = cls.env["res.partner.category"].create({
            "name": "Test Users"
        })

        # Create a test user and assign to category
        cls.user = cls.env["res.partner"].create({
            "name": "Jane Smith",
            "category_id": [(6, 0, [cls.test_category.id])]
        })
        
        cls.author_robert = cls.env["library.author"].create({
            "name": "Robert Martin"
        })
        

        # Create a test book
        cls.book = cls.env["library.book"].create({
            "name": "Clean Architecture",
            "author_id": cls.author_robert.id,
            "published_date": fields.Date.today(),
        })
        
        
    def test_unique_book_name_author(self):
        """
        Ensure that a book with the same name and author cannot be duplicated.
        """
        
        with self.assertRaises(ValidationError):
            self.env["library.book"].create({
                "name": "Clean Architecture",
                "author_id": self.author_robert.id,
                "published_date": fields.Date.today(),
            })
            
    def test_book_published_date_not_future(self):
        """
        Ensure that a book's published date cannot be set in the future.
        """
        
        future_date = fields.Date.today() + timedelta(days=1)

        with self.assertRaises(ValidationError):
            self.env["library.book"].create({
                "name": "Future Book",
                "author_id": self.author_robert.id,
                "published_date": future_date,
            })
            
    def test_rent_book_success(self):
        """
        Test that renting a book updates its availability and sets the current renter.
        """
        
        self.env["library.rent"].create({
            "partner_id": self.user.id,
            "book_id": self.book.id,
        })

        self.assertFalse(self.book.is_available, "Book should be marked as unavailable after rent.")
        self.assertEqual(self.book.current_renter_id, self.user, "Current renter should be set to the renting user.")
        
        
    def test_only_one_open_rent_per_book(self):
        """
        Ensure that a book cannot be rented by multiple users at the same time.
        """
        
        self.env["library.rent"].create({
            "partner_id": self.user.id,
            "book_id": self.book.id,
        })

        with self.assertRaises(ValidationError):
            self.env["library.rent"].create({
                "partner_id": self.user.id,
                "book_id": self.book.id,
            })
            
    def test_rent_date_not_future(self):
        """
        Ensure that a rent's start date cannot be in the future.
        """
        future_date = fields.Date.today() + timedelta(days=2)

        with self.assertRaises(ValidationError):
            self.env["library.rent"].create({
                "partner_id": self.user.id,
                "book_id": self.book.id,
                "rent_date": future_date,
            })
            
    def test_return_date_before_rent_date(self):
        """
        Ensure that a rent's return date cannot be before the rent date.
        """
        
        today = fields.Date.today()

        with self.assertRaises(ValidationError):
            self.env["library.rent"].create({
                "partner_id": self.user.id,
                "book_id": self.book.id,
                "rent_date": today,
                "return_date": today - timedelta(days=1),
            })
            
    def test_return_book(self):
        """
        Test returning a book:
        - Book becomes available
        - Current renter is cleared
        """
        
        rent = self.env["library.rent"].create({
            "partner_id": self.user.id,
            "book_id": self.book.id,
        })

        rent.action_return_book()

        self.assertTrue(self.book.is_available, "Book should be available after return.")
        self.assertFalse(self.book.current_renter_id, "Current renter should be cleared after return.")

    def test_return_book_twice_raises(self):
        """
        Test that trying to return the same book twice raises ValidationError.
        """
        
        rent = self.env["library.rent"].create({
            "partner_id": self.user.id,
            "book_id": self.book.id,
        })

        # First return works fine
        rent.action_return_book()

        # Second return should raise ValidationError
        with self.assertRaises(ValidationError):
            rent.action_return_book()
       

    def test_unique_author_name(self):
        """Check that creating two authors with the same name raises an error."""
        
        self.env['library.author'].create({'name': 'Jane Austen'})
        with self.assertRaises(UniqueViolation):
            self.env['library.author'].create({'name': 'Jane Austen'})

    def test_strip_name_uniqueness(self):
        """Check that names with leading/trailing spaces 
           or different case are considered duplicates."""
        
        self.env['library.author'].create({'name': 'Jane Austen'})

        # This should now fail due to normalized unique
        with self.assertRaises(UniqueViolation):
            self.env['library.author'].create({'name': '  jane austen  '})