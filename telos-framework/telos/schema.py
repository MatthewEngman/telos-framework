from pydantic import BaseModel, Field
from typing import List, Literal, Tuple, Optional


class Ontology(BaseModel):
    variables: List[str] = Field(description="List of domain variables")
    bounds: List[Tuple[Optional[float], Optional[float]]] = Field(
        description="Min and max limits for each variable"
    )
    parameters: List[str] = Field(
        default_factory=list,
        description="Symbols substituted from context each tick (not optimized)",
    )


class Teleology(BaseModel):
    direction: Literal["maximize", "minimize"]
    objective: str = Field(description="Mathematical expression representing the goal")


class Invariant(BaseModel):
    type: Literal["eq", "ineq"] = Field(
        description="'eq' for == 0, 'ineq' for >= 0"
    )
    expression: str = Field(description="Mathematical constraint expression")


class TIRSchema(BaseModel):
    ontology: Ontology
    teleology: Teleology
    invariants: List[Invariant]
