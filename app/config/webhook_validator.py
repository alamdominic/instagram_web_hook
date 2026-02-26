from typing import Any
from pydantic import BaseModel

"""
Modelos Pydantic del payload de Instagram
BaseModel es para validar datos que llegan en requests.
El nombre debe de representar lo que modelamos, en este 
caso un cambio en el webhook de Instagram.


Nivel 1 — `object` y `entry`.
Nivel 2 — tiene `id`, `time` y `changes`.
Nivel 3 — tiene `field` y `value`.

En Python debes definir los modelos de adentro hacia afuera,
primero el más interno porque los externos dependen de él.

"""


class Change(BaseModel):
    field: str
    value: Any


class Entry(BaseModel):
    id: str
    time: int
    changes: list[Change]


class WebhookPayload(BaseModel):
    object: str
    entry: list[Entry]
