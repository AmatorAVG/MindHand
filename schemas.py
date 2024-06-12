from pydantic import BaseModel

# from main import Pens


class PointSchema(BaseModel):
    x: int
    y: int
    size: int


class LineSchema(BaseModel):
    # model_config = ConfigDict(arbitrary_types_allowed=True)

    x: int
    y: int
    size: int
    color: str
    pen: str
    points: list[PointSchema] = []
