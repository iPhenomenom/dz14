import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app, get_db
from models import Contact


class TestContactAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = Session()

    def tearDown(self):
        self.db.close()

    def test_create_contact(self):
        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com",
            "phone": "1234567890",
            "birthday": "1990-01-01",
            "additional_info": "Additional information",
        }

        response = self.client.post("/contacts/", json=contact_data)
        self.assertEqual(response.status_code, 201)  # Изменено на 201

        created_contact = response.json()
        self.assertEqual(created_contact["first_name"], contact_data["first_name"])
        self.assertEqual(created_contact["last_name"], contact_data["last_name"])
        self.assertEqual(created_contact["email"], contact_data["email"])
        self.assertEqual(created_contact["phone"], contact_data["phone"])
        self.assertEqual(created_contact["birthday"], contact_data["birthday"])
        self.assertEqual(created_contact["additional_info"], contact_data["additional_info"])


if __name__ == "__main__":
    unittest.main()
