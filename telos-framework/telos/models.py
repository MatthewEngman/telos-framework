"""Pydantic **MILP** models for ``.telos`` manifests and ``TelosRuntime`` (canonical path)."""

from __future__ import annotations

from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


class Variable(BaseModel):
    name: str
    type: Literal["float", "int"] = "float"
    bounds: Tuple[Optional[float], Optional[float]]


class Memory(BaseModel):
    name: str
    init: float
    update: str


class Ontology(BaseModel):
    variables: List[Variable]
    parameters: List[str] = Field(default_factory=list)


class Teleology(BaseModel):
    direction: Literal["minimize", "maximize"]
    objective: str


class Invariant(BaseModel):
    type: Literal["eq", "ineq"]
    expression: str


class TelosSchema(BaseModel):
    ontology: Ontology
    memory: List[Memory] = Field(default_factory=list)
    teleology: Teleology
    invariants: List[Invariant]
