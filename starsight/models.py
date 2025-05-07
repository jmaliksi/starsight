from sqlalchemy import Column, String, Enum, ForeignKey, Float
from sqlalchemy.dialects.sqlite import BLOB as SQLITE_BLOB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, BLOB
from starsight.database import Base
from typing import Optional
import enum
import uuid


class GUID(TypeDecorator):
    impl = BLOB

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(SQLITE_BLOB())

    def process_bind_param(self, value, dialect) -> Optional[bytes]:
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value).bytes
        return value.bytes

    def process_result_value(self, value, dialect) -> Optional[uuid.UUID]:
        if value is None:
            return value
        return uuid.UUID(bytes=value)


class System(Base):
    __tablename__ = 'systems'

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, nullable=False)
    spobs = relationship('Spob', backref='system', remote_side=[id])


class SpobType(enum.Enum):
    BARYCENTER = "barycenter"
    STAR = "star"
    PLANET = "planet"
    MOON = "moon"


class Spob(Base):
    __tablename__ = 'spobs'

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, nullable=True)
    type = Column(Enum(SpobType, native_enum=False), nullable=False)
    system_id = Column(GUID(), ForeignKey('systems.id'), nullable=False)
    parent_id = Column(GUID(), ForeignKey('spobs.id'), nullable=True)
    children = relationship('Spob', backref='parent', remote_side=[id])
    description = Column(String, nullable=True)
    mass: Mapped[float] = mapped_column(Float, default=0.0)
    semi_major_axis: Mapped[float] = mapped_column(Float, default=0.0)
    eccentricity: Mapped[float] = mapped_column(Float, default= 0.0)
    anomaly: Mapped[float] = mapped_column(Float, default=0.0)

    @property
    def semi_minor_axis(self) -> float:
        return self.semi_major_axis * ((1.0 - (self.eccentricity**2))**0.5)
