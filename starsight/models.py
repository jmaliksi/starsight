from sqlalchemy import Column, String, Enum, ForeignKey, Float, Integer, Table
from sqlalchemy.dialects.sqlite import BLOB as SQLITE_BLOB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, BLOB
from starsight.database import Base
from functools import cached_property
from typing import Optional, List
import enum
import math
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


class Galaxy(Base):
    __tablename__ = 'galaxies'

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    seed = Column(GUID(), default=uuid.uuid4, nullable=False)
    name = Column(String)

    @property
    def snoise_base(self) -> int:
        return self.seed.int & 0xFFFFF


hyperlink = Table(
    'hyperlink',
    Base.metadata,
    Column('origin', ForeignKey('systems.id'), primary_key=True),
    Column('destination', ForeignKey('systems.id'), primary_key=True),
)


class System(Base):
    __tablename__ = 'systems'

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    galaxy_id = Column(GUID(), ForeignKey('galaxies.id'), nullable=False, index=True)
    name = Column(String, nullable=False)
    spobs = relationship('Spob', backref='system', remote_side=[id])
    x: Mapped[int] = mapped_column(Integer, index=True)
    y: Mapped[int] = mapped_column(Integer, index=True)
    hyperlinks: Mapped[List['System']] = relationship(
        'System',
        secondary=hyperlink,
        primaryjoin=id == hyperlink.c.origin,
        secondaryjoin=id == hyperlink.c.destination,
    )

    def are_neighbors(self, other: 'System', distance: float) -> bool:
        return (distance * distance) > (((self.x - other.x) ** 2) + ((self.y - other.y) ** 2))

    def bucket(self, chunk_size) -> tuple[int, int]:
        return int(self.x / chunk_size), int(self.y / chunk_size)


class SpobType(enum.Enum):
    BARYCENTER = "barycenter"
    STAR = "star"
    PLANET = "planet"
    MOON = "moon"


class Spob(Base):
    __tablename__ = 'spobs'

    id: Mapped[GUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)
    type = Column(Enum(SpobType, native_enum=False), nullable=False)
    system_id = Column(GUID(), ForeignKey('systems.id'), nullable=False, index=True)
    parent_id: Mapped[GUID] = mapped_column(GUID(), ForeignKey('spobs.id'), nullable=True)
    children = relationship('Spob', backref='parent', remote_side=[id])
    description = Column(String, nullable=True)
    mass: Mapped[float] = mapped_column(Float, default=0.0)
    semi_major_axis: Mapped[float] = mapped_column(Float, default=0.0)
    eccentricity: Mapped[float] = mapped_column(Float, default= 0.0)
    anomaly: Mapped[float] = mapped_column(Float, default=0.0)
    radius: Mapped[float] = mapped_column(Float, default=1)

    @cached_property
    def semi_minor_axis(self) -> float:
        return self.semi_major_axis * ((1.0 - (self.eccentricity**2))**0.5)

    @cached_property
    def roche_limit(self) -> float:
        return self.radius * 1.26  # TODO constants

    @cached_property
    def hill_radius(self) -> float:
        main_mass = 0.0
        if self.parent_id:
            main_mass = self.parent.mass
        return self.semi_major * math.pow(self.mass / (3 * self.mass + main_mass), 1/3)

    @cached_property
    def period(self) -> float:
        G = 6.6743e-11
        return 2 * math.pi * math.sqrt(self.semi_major_axis ** 3 / (G * self.parent.mass))

    def position(self, t: float) -> tuple[float, float]:
        tuning = 0.8
        period = self.period
        theta = 2 * math.pi * ((t % period) / period) ** tuning
        return self.semi_major_axis * math.cos(theta), self.semi_minor_axis * math.sin(theta)
