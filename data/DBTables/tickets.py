from data.db_session import SqlAlchemyBase
from sqlalchemy import Column, Integer, String
from flask_login import UserMixin


class Ticket(SqlAlchemyBase, UserMixin):
    __tablename__ = 'Ticket'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, nullable=False)
    count = Column(String, nullable=False)
    id_attraction = Column(Integer, nullable=False)
    owner_id = Column(Integer, nullable=False)
    cost = Column(Integer, default=0)