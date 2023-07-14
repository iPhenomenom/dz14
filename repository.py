from models import Note
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    birthday = Column(String)
    additional_info = Column(String)
class NoteRepository:
    def __init__(self, session: Session):
        self.session = session



    def create_contact(self, contact: Contact):
        self.session.add(contact)
        self.session.commit()
        self.session.refresh(contact)

    def create_note(self, **note_data):
        note = Note(**note_data)
        self.session.add(note)
        self.session.commit()
        return note

    def get_note_by_id(self, note_id):
        return self.session.query(Note).get(note_id)

    def create(self, note):
        self.session.add(note)
        self.session.commit()

    def read(self, note_id):
        return self.session.query(Note).get(note_id)

    def update(self, note):
        self.session.commit()

    def delete(self, note):
        self.session.delete(note)
        self.session.commit()


