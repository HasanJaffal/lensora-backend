from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for every DTO exposed across the API boundary.

    Serializes to camelCase JSON (the TS frontend contract) while still accepting the
    snake_case field names internally.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
