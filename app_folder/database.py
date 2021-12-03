from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = f"postgresql://psbnevwvswrpqx:e917ea3b0f2196ae9d393f5dac5164e2a5bb9e0ec4f3de25624ae304ea79f782@ec2-34-251-245-108.eu-west-1.compute.amazonaws.com:5432/d7olmo993f2c6l"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
