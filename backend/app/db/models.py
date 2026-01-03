import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import enum

class AccountRoleEnum(str, enum.Enum):
    admin = "admin"
    corporate_admin = "corporate_admin"
    end_user = "end_user"

class JobRoleEnum(str, enum.Enum):
    manager = "manager"
    developer = "developer"

class StatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String)
    role = Column(SQLEnum(JobRoleEnum), nullable=True)  # manager, developer
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.active)  # active, inactive
    account_role = Column(SQLEnum(AccountRoleEnum), default=AccountRoleEnum.end_user)  # admin, corporate_admin, end_user
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

