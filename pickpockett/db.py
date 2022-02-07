from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine(f"sqlite:///{__name__}")
Session = sessionmaker(bind=engine)


class Config(Base):
    __tablename__ = "config"

    name = Column(Text, primary_key=True)
    value = Column(Text)


class Source(Base):
    __tablename__ = "sources"

    tvdb_id = Column(Integer, primary_key=True, autoincrement=False)
    season = Column(
        Integer, primary_key=True, autoincrement=False, nullable=True
    )
    link = Column(Text, nullable=False, server_default="")
    cookies = Column(Text, nullable=False, server_default="")
    hash = Column(String(40), nullable=False, server_default="")
    timestamp = Column(Integer, nullable=False, server_default="0")
