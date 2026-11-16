from sqlalchemy import BigInteger, Boolean, Column, Date, Integer, String

from ..database import Base


class Entidad(Base):
    """Tabla plana del Data Warehouse: personajes de la Dragon Ball API."""

    __tablename__ = "personajes_master"
    __table_args__ = {"mysql_charset": "utf8mb4"}

    # PK = mismo ID (y mismo tipo) que el _id de Mongo. NO autoincremental.
    id_personaje = Column(Integer, primary_key=True, autoincrement=False)
    nombre = Column(String(150), nullable=False)
    raza = Column(String(100))
    genero = Column(String(50))
    afiliacion = Column(String(100))
    ki_base = Column(BigInteger)
    ki_maximo = Column(String(100))
    planeta_origen = Column(String(150))
    planeta_destruido = Column(Boolean)
    total_transformaciones = Column(Integer)
    fecha_extraccion = Column(Date)