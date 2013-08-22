from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

# Needs to be separate from model class defs so that Base engine can
# be set prior to loading model classes (because when the model 
# classes that inherit from Base are loaded, they require a bound
# engine)
def initialize_base(engine):
    Base.metadata.bind = engine
    # Base.metadata.create_all(engine)

def initialize_session(engine):
    print("initialize_session")
    DBSession.configure(bind=engine)

