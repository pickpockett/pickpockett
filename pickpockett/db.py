from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine(f"sqlite:///{__name__}", echo=True)
Session = sessionmaker(bind=engine)


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    season = Column(Integer)
    link = Column(Text, nullable=False, server_default="")
    cookies = Column(Text)
    hash = Column(String(40))
    timestamp = Column(Integer)
