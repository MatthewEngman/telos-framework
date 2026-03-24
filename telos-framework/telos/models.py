"""Pydantic **MILP** models for ``.telos`` manifests and ``TelosRuntime`` (canonical path)."""

from __future__ import annotations

from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


class TelosTemplate(BaseModel):
    """
    Optional catalog / submission metadata. Ignored by ``TelosCompiler`` and solvers;
    safe for GitHub template issues, registries, and docs generators.
    """

    name: Optional[str] = None
    category: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    actuators: List[str] = Field(default_factory=list)


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
    template: Optional[TelosTemplate] = None
