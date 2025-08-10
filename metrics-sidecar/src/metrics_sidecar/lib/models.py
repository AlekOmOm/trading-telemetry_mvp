from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class TradeMsg(BaseModel):
    type: Literal["trade"] = "trade"
    side: Literal["buy", "sell"]
    qty: float = Field(ge=0)
    ts: float  # unix epoch seconds (float)

    @field_validator("qty")
    @classmethod
    def _qty_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("qty must be >= 0")
        return v
