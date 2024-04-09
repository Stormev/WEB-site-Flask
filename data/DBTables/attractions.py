from data.db_session import SqlAlchemyBase
from sqlalchemy import Column, Integer, String, BOOLEAN
from flask_login import UserMixin


class Attractions(SqlAlchemyBase, UserMixin):
    __tablename__ = 'Attraction'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, unique=True, nullable=False)
    image_path = Column(String, nullable=False)
    cost = Column(Integer, default=0, nullable=False)
    description = Column(String, nullable=False)
    is_work = Column(BOOLEAN, nullable=False)