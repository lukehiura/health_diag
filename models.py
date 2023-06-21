from sqlalchemy import Column, Integer, Boolean, BigInteger, JSON, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user_data'

    id = Column(BigInteger, primary_key=True)
    data = Column(JSON)
    first_name = Column(String)
    last_name = Column(String)

    def __repr__(self):
        return f"<User(id={self.id}, data={self.data}, first_name={self.first_name}, last_name={self.last_name})>"
