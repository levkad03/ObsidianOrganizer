from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Vault(Base):
    __tablename__ = "vaults"

    thread_id = Column(String, primary_key=True)
    vault_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
