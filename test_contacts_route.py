import pytest
from fastapi.testclient import TestClient
from main import app
from repository import NoteRepository
from models import Contact
from database import engine, Base
from sqlalchemy.orm import Session

Base.metadata.create_all(bind=engine)
client = TestClient(app)


@pytest.fixture(scope="module")
def test_db():
    connection = engine.connect()
    transaction = connection.begin()

    # Создаем сессию базы данных
    session = Session(bind=connection)

    # Создаем репозиторий контактов
    contact_repository = NoteRepository(session)

    yield contact_repository

    # Откатываем транзакцию после завершения тестов
    transaction.rollback()
    connection.close()


def test_create_contact(test_db):
    # Создаем тестовые данные
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe2@example.com",  # Уникальный email
        "phone": "123456789",
        "birthday": "2000-01-01",
        "additional_info": "Test contact",
    }

    # Вызываем маршрут создания контакта
    response = client.post("/contacts/", json=contact_data)

    # Проверяем, что запрос возвращает статус код 201 (Created)
    assert response.status_code == 201




def test_read_contact(test_db):
    # Создаем тестовый контакт
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="123456789",
        birthday="2000-01-01",
        additional_info="Test contact",
    )
    test_db.create(contact)

    # Вызываем маршрут получения контакта по его идентификатору
    response = client.get(f"/contacts/{contact.id}")

    # Проверяем, что запрос успешен и статус код 200 (OK)
    assert response.status_code == 200

    # Проверяем, что полученный контакт соответствует созданному контакту
    retrieved_contact = response.json()
    assert retrieved_contact["first_name"] == contact.first_name
    assert retrieved_contact["last_name"] == contact.last_name
    assert retrieved_contact["email"] == contact.email
    assert retrieved_contact["phone"] == contact.phone
    assert retrieved_contact["birthday"] == contact.birthday
    assert retrieved_contact["additional_info"] == contact.additional_info





def test_read_contact(test_db):
    # Создаем тестовый контакт
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="123456789",
        birthday="2000-01-01",
        additional_info="Test contact",
    )
    test_db.create_contact(contact)

    # Вызываем маршрут получения контакта по его идентификатору
    response = client.get(f"/contacts/{contact.id}")

    # Проверяем, что запрос успешен и статус код 200 (OK)
    assert response.status_code == 200

    # Проверяем, что полученный контакт соответствует созданному контакту
    retrieved_contact = response.json()
    assert retrieved_contact["first_name"] == contact.first_name
    assert retrieved_contact["last_name"] == contact.last_name
    assert retrieved_contact["email"] == contact.email
    assert retrieved_contact["phone"] == contact.phone
    assert retrieved_contact["birthday"] == contact.birthday
    assert retrieved_contact["additional_info"] == contact.additional_info
