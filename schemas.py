from enum import Enum
from typing import List
from pydantic import BaseModel, Field, field_validator


class NivelCriticidad(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class ExtraccionTecnica(BaseModel):
    tecnologias: List[str] = Field(
        description="Lista de tecnologías, frameworks o herramientas mencionadas en el texto"
    )
    nivel_de_criticidad: NivelCriticidad = Field(
        description="Nivel de criticidad del problema o arquitectura descrita"
    )
    resumen_tecnico: str = Field(
        description="Resumen técnico breve del texto analizado"
    )

    @field_validator("tecnologias")
    @classmethod
    def tecnologias_no_vacia(cls, v):
        if not v:
            raise ValueError("La lista de tecnologías no puede estar vacía")
        return v