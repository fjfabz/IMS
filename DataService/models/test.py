from . import Base, engine
from sqlalchemy.types import  String, Text, TIMESTAMP, PickleType, Integer, Boolean
from sqlalchemy.orm import  relationship
from sqlalchemy import Column, ForeignKey

class Test(Base):
    __tablename__ = 'test'

    code = Column(Integer, primary_key=True, autoincrement=False) # 二进制位表示
    description = Column(String(64))