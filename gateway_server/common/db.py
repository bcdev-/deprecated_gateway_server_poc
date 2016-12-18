from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .settings import db_url

engine = create_engine(db_url, convert_unicode=True)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
from . import models
Base.metadata.create_all(bind=engine)
