from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator

CATEGORIES = [
    "Letters", "Memories", "Promises", "Achievements I Wanted to Share",
    "Happy Moments", "Sad Moments", "Times I Missed You",
    "Vacations I Wish We Had Together", "I Really Want You Beside Me Right Now",
    "Life Updates", "Weird Dreams", "I Thought About You Again", "I Need To Move On",
]


class PromiseInput(BaseModel):
    promise: str = Field(min_length=1, max_length=10000)
    date_made: date | None = None
    status: Literal["KEPT", "BROKEN", "PARTIALLY_KEPT", "ONGOING", "UNCERTAIN"]
    context: str = Field(default="", max_length=10000)
    still_intended: bool = True
    notes: str = Field(default="", max_length=10000)


class EntryInput(BaseModel):
    category: str
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(max_length=50000)
    shared: bool = False
    occurred_on: date | None = None
    promise: PromiseInput | None = None

    @model_validator(mode="after")
    def validate_category(self):
        if self.category not in CATEGORIES:
            raise ValueError("Unknown category")
        if (self.category == "Promises") != (self.promise is not None):
            raise ValueError("Promises require promise details; other categories must omit them")
        return self


class GateOneInput(BaseModel):
    answers: dict[str, str] = Field(max_length=20)


class GateTwoInput(BaseModel):
    anniversary: str = Field(max_length=100)
    full_name: str = Field(max_length=200)


class LoginInput(BaseModel):
    username: str = Field(max_length=100)
    password: str = Field(max_length=200)
    code: str = Field(pattern=r"^\d{6}$")
