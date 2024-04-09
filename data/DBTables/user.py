from data.db_session import SqlAlchemyBase
from sqlalchemy import Column, Integer, String
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    balance = Column(Integer, default=0)