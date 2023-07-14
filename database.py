from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


# Создаем строку подключения
database_url = "postgresql://postgres:0939135697@localhost:5432/newDB"

# Создаем экземпляр движка SQLAlchemy
engine = create_engine(database_url)

# Создаем базовый класс для объявления моделей
Base = declarative_base()
