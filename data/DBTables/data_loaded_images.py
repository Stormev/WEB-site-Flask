from data.db_session import SqlAlchemyBase
from sqlalchemy import Column, Integer, String
from flask_login import UserMixin


class DLI(SqlAlchemyBase, UserMixin):
    __tablename__ = 'data_loaded_images'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, unique=True, nullable=False)
    details = Column(Integer, nullable=False)
    image_path = Column(String, nullable=False)
    owner_id = Column(Integer, nullable=False)
