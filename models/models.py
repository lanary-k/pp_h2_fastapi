from datetime import datetime
from sqlalchemy import MetaData, Table, Column, Integer, String, TIMESTAMP, ForeignKey, JSON, Boolean

metadata = MetaData()

role = Table(
    "role", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("permissions", JSON),
)

user = Table(
    "user", metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, nullable=False),
    Column("username", String, nullable=False),
    Column("hashed_password", String, nullable=False),
    Column("registered_at", TIMESTAMP, default=datetime.utcnow),
    Column("role_id", Integer, ForeignKey("role.id")),
    Column("is_active", Boolean, default=True, nullable=False),
    Column("is_superuser", Boolean, default=True, nullable=False),
    Column("is_verified", Boolean, default=True, nullable=False),
)

link = Table(
    "link", metadata,
    Column("id", Integer, primary_key=True),
    Column("original_url", String, nullable=False),
    Column("short_code", String, unique=True, nullable=False),
    Column("create_date", TIMESTAMP(timezone=True), default=datetime.utcnow),
    Column("last_used_date", TIMESTAMP(timezone=True), nullable=True),
    Column("last_date", TIMESTAMP(timezone=True), nullable=True),
    Column("clicks", Integer, default=0, nullable=False),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=True),
)
