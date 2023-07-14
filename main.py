from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from sqlalchemy import Column, Integer, String, Boolean, Date, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm import declarative_base
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime, timedelta
import uvicorn
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
from sqlalchemy.testing import db

from mail import send_verification_email
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import cloudinary
import cloudinary.uploader


Base = declarative_base()

# Определение разрешенных источников для CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    # Добавьте дополнительные разрешенные источники (origins) при необходимости
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Настройка Cloudinary
cloudinary.config(
    cloud_name="your_cloud_name",
    api_key="your_api_key",
    api_secret="your_api_secret"
)


@app.put("/users/{user_id}/avatar")
def update_user_avatar(user_id: int, avatar: UploadFile = File(...)):
    """
    Обновляет аватар пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        avatar (UploadFile): Загруженное изображение аватара.

    Returns:
        dict: Словарь с сообщением об успешном обновлении аватара.
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Загрузите аватар на Cloudinary
    upload_result = cloudinary.uploader.upload(avatar.file)

    # Обновите информацию об аватаре пользователя в базе данных
    user.avatar_url = upload_result["secure_url"]
    db.commit()

    return {"message": "Avatar updated successfully"}


# SQLAlchemy model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)


# Pydantic models
class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str

    class Config:
        orm_mode = True


SQLALCHEMY_DATABASE_URL = "postgresql://postgres:0939135697@localhost:5432/newDB"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    birthday = Column(Date)
    additional_info = Column(String)


Base.metadata.create_all(bind=engine)


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date
    additional_info: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    email: Optional[EmailStr] = Field(None)
    phone: Optional[str] = Field(None)
    birthday: Optional[date] = Field(None)
    additional_info: Optional[str] = Field(None)


class ContactInDB(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date
    additional_info: Optional[str] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


def get_db():
    """
    Создает новое подключение к базе данных и возвращает сессию.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/contacts/", response_model=ContactInDB, status_code=status.HTTP_201_CREATED)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """
    Создает новый контакт.

    Args:
        contact (ContactCreate): Данные для создания контакта.
        db (Session, optional): Сессия базы данных. Defaults to Depends(get_db).

    Returns:
        ContactInDB: Созданный контакт.
    """
    db_contact = db.query(Contact).filter(Contact.email == contact.email).first()
    if db_contact:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact



@app.get("/contacts/", response_model=List[ContactInDB])
def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Возвращает список контактов.

    Args:
        skip (int, optional): Количество пропущенных контактов. Defaults to 0.
        limit (int, optional): Максимальное количество возвращаемых контактов. Defaults to 100.
        db (Session, optional): Сессия базы данных. Defaults to Depends(get_db).

    Returns:
        List[ContactInDB]: Список контактов.
    """
    contacts = db.query(Contact).offset(skip).limit(limit).all()
    return contacts


@app.get("/contacts/{contact_id}", response_model=ContactInDB)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Возвращает контакт по его идентификатору.

    Args:
        contact_id (int): Идентификатор контакта.
        db (Session, optional): Сессия базы данных. Defaults to Depends(get_db).

    Returns:
        ContactInDB: Контакт.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact


@app.put("/contacts/{contact_id}", response_model=ContactInDB)
def update_contact(contact_id: int, contact: ContactUpdate, db: Session = Depends(get_db)):
    """
    Обновляет информацию о контакте.

    Args:
        contact_id (int): Идентификатор контакта.
        contact (ContactUpdate): Обновленные данные контакта.
        db (Session, optional): Сессия базы данных. Defaults to Depends(get_db).

    Returns:
        ContactInDB: Обновленный контакт.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in contact.dict(exclude_unset=True).items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@app.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Удаляет контакт.

    Args:
        contact_id (int): Идентификатор контакта.
        db (Session, optional): Сессия базы данных. Defaults to Depends(get_db).

    Returns:
        dict: Словарь с сообщением об успешном удалении контакта.
    """
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(db_contact)
    db.commit()
    return {"detail": "Contact deleted"}, 204


@app.get("/contacts/search/", response_model=List[ContactInDB])
def search_contacts(query: str, db: Session = Depends(get_db)):
    """
    Выполняет поиск контактов по запросу.

    Args:
        query (str): Запрос для поиска контактов.
        db (Session, optional): Сессия базы данных. Defaults to Depends(get_db).

    Returns:
        List[ContactInDB]: Список найденных контактов.
    """
    contacts = db.query(Contact).filter(
        (Contact.first_name.ilike(f"%{query}%")) |
        (Contact.last_name.ilike(f"%{query}%")) |
        (Contact.email.ilike(f"%{query}%"))
    ).all()
    return contacts


@app.get("/contacts/upcoming_birthdays", response_model=List[ContactInDB])
def get_upcoming_birthdays(db: Session = Depends(get_db)):
    """
    Возвращает список контактов с предстоящими днями рождения.

    Args:
        db (Session, optional): Сессия базы данных. Defaults to Depends(get_db).

    Returns:
        List[ContactInDB]: Список контактов с предстоящими днями рождения.
    """
    today = date.today()
    next_week = today + timedelta(days=7)
    contacts = db.query(Contact).filter(
        (Contact.birthday >= today) & (Contact.birthday <= next_week)
    ).all()
    return contacts


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """
    Проверяет соответствие пароля хэшу.

    Args:
        plain_password (str): Пароль в виде строки.
        hashed_password (str): Хэшированный пароль.

    Returns:
        bool: True, если пароль соответствует хэшу, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Возвращает хэш пароля.

    Args:
        password (str): Пароль в виде строки.

    Returns:
        str: Хэш пароля.
    """
    return pwd_context.hash(password)


def get_user_by_email(db: Session, email: str):
    """
    Возвращает пользователя по его email.

    Args:
        db (Session): Сессия базы данных.
        email (str): Email пользователя.

    Returns:
        User: Пользователь.
    """
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    """
    Создает нового пользователя.

    Args:
        db (Session): Сессия базы данных.
        user (UserCreate): Данные для создания пользователя.

    Returns:
        User: Созданный пользователь.
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    """
    Проверяет аутентификацию пользователя.

    Args:
        db (Session): Сессия базы данных.
        email (str): Email пользователя.
        password (str): Пароль пользователя.

    Returns:
        User: Пользователь, если аутентификация успешна, иначе None.
    """
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_user(db: Session, user_id: int):
    """
    Возвращает пользователя по его идентификатору.

    Args:
        db (Session): Сессия базы данных.
        user_id (int): Идентификатор пользователя.

    Returns:
        User: Пользователь.
    """
    return db.query(User).filter(User.id == user_id).first()


SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Возвращает текущего аутентифицированного пользователя.

    Args:
        token (str, optional): Токен доступа. Defaults to Depends(oauth2_scheme).
        db (Session, optional): Сессия базы данных. Defaults to Depends(get_db).

    Raises:
        HTTPException: Если аутентификация не удалась.

    Returns:
        User: Текущий пользователь.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user


@app.post("/users/", response_model=UserInDB, status_code=201)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    """
    Создает нового пользователя.

    Args:
        user (UserCreate): Данные для создания пользователя.
        db (Session, optional): Сессия базы данных. Defaults to Depends(get_db).

    Raises:
        HTTPException: Если пользователь с таким email уже существует.

    Returns:
        UserInDB: Созданный пользователь.
    """
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Создайте нового пользователя
    new_user = create_user(db=db, user=user)

    # Отправьте письмо с подтверждением регистрации
    send_verification_email(new_user.email)

    return new_user


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Создает токен доступа для аутентификации пользователя.

    Args:
        form_data (OAuth2PasswordRequestForm, optional): Данные формы для аутентификации.
            Defaults to Depends().

    Raises:
        HTTPException: Если аутентификация не удалась.

    Returns:
        Token: Токен доступа.
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


def create_access_token(*, data: dict, expires_delta: timedelta = None):
    """
    Создает токен доступа.

    Args:
        data (dict): Данные, которые будут закодированы в токене.
        expires_delta (timedelta, optional): Временной интервал действия токена.
            Defaults to None.

    Returns:
        str: Токен доступа.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM).decode("utf-8")
    return encoded_jwt


@app.post("/users/verify-email/")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Подтверждает адрес электронной почты пользователя.

    Args:
        token (str): Токен подтверждения.
        db (Session, optional): Сессия базы данных. Defaults to Depends(get_db).

    Raises:
        HTTPException: Если пользователь не найден или токен недействителен.

    Returns:
        dict: Словарь с сообщением об успешном подтверждении адреса электронной почты.
    """
    user = get_user_by_email(db, email=user.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверьте, что токен действителен и соответствует пользователю
    if not is_valid_token(token, user):
        raise HTTPException(status_code=400, detail="Invalid token")

    # Обновите статус is_verified пользователя
    user.is_verified = True
    db.commit()

    return {"message": "Email verification successful"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
