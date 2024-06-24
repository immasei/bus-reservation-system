import inspect
from typing import List, Annotated, Any, Dict

from fastapi import Form
from pydantic import BaseModel, Json, model_validator, root_validator, field_validator

def as_form(cls):
    # https://stackoverflow.com/questions/60127234/how-to-use-a-pydantic-model-with-form-data-in-fastapi/77113651#77113651
    new_params = [
        inspect.Parameter(
            field_name,
            inspect.Parameter.POSITIONAL_ONLY,
            default=model_field.default,
            annotation=Annotated[model_field.annotation, *model_field.metadata, Form()],
        )
        for field_name, model_field in cls.model_fields.items()
    ]

    cls.__signature__ = cls.__signature__.replace(parameters=new_params)

    return cls

# https://fastapi.tiangolo.com/tutorial/body-nested-models/

class Stop(BaseModel):
    stop_id: str
    name: str
    location: List[float]

class Tour(BaseModel):
    id: str
    name: str
    duration: str
    routes: List[Stop]

@as_form
class Booking(BaseModel):
    # https://github.com/tiangolo/fastapi/issues/5588
    email: str
    telephone: int
    seats: List[str] = []

    @field_validator('seats', mode='before')
    def split_str(cls, v):
        return v[0].split('|')

