from pydantic import BaseModel


class PointSchema(BaseModel):
    x: int
    y: int
    size: int


class LineSchema(BaseModel):
    x: int
    y: int
    size: int
    color: str
    points: list[PointSchema] = []
