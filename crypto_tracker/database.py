from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///data/cryptodb.sqlite3', echo=True)

Session = sessionmaker(bind=engine)
session = Session()
