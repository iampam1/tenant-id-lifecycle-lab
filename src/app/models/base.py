from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column # For newer SQLAlchemy type hints
from sqlalchemy import MetaData

# Optional: Define a naming convention for constraints if you want Alembic
# to generate consistent names for indexes, unique constraints, etc.
# See SQLAlchemy documentation for 'convention' parameter in MetaData.
# Example:
# convention = {
#     "ix": "ix_%(column_0_label)s",
#     "uq": "uq_%(table_name)s_%(column_0_name)s",
#     "ck": "ck_%(table_name)s_%(constraint_name)s",
#     "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
#     "pk": "pk_%(table_name)s"
# }
# metadata_obj = MetaData(naming_convention=convention)
# Base = declarative_base(metadata=metadata_obj)

# Standard declarative base
Base = declarative_base()

# Example of a common base class for all models if you need shared columns like id, created_at, updated_at
# class BaseModel(Base):
#     __abstract__ = True # This means SQLAlchemy won't create a table for BaseModel
#
#     id: Mapped[int] = mapped_column(primary_key=True, index=True)
#     created_at: Mapped[datetime] = mapped_column(server_default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
