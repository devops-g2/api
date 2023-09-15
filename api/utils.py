from typing import Union, TypeVar, Type, Any, Optional
from pydantic import BaseModel
from fastapi import Depends, Query


FILTER = dict[str, Union[int, float, str, bool, None]]
SORT = dict[str, str]

PYDANTIC_SCHEMA = BaseModel

T = TypeVar("T", bound=PYDANTIC_SCHEMA)
FILTER_MAPPING = {
    "int": int,
    "float": float,
    "bool": bool,
    "str": str,
    "ConstrainedStrValue": str,
}


def query_factory(schema: Type[T]) -> Any:
    """
    Dynamically builds a Fastapi query dependency based on all available field in the
    """

    _str = "{}: Optional[{}] = Query(None)"
    args_str = ", ".join(
        [
            _str.format(name, FILTER_MAPPING[field.type_.__name__].__name__)
            for name, field in schema.__fields__.items()
            if field.type_.__name__ in FILTER_MAPPING
        ]
    )

    _str = "{}={}"
    return_str = ", ".join(
        [
            _str.format(name, field.name)
            for name, field in schema.__fields__.items()
            if field.type_.__name__ in FILTER_MAPPING
        ]
    )

    filter_func_src = f"""
def filter_func({args_str}) -> FILTER:
    ret = dict({return_str})
    return {{k:v for k, v in ret.items() if v is not None}}
"""

    exec(filter_func_src, globals(), locals())
    return Depends(locals().get("filter_func"))


def sort_factory(schema: Type[T]) -> Any:
    fields = [field.name for field in schema.__fields__.values()]

    def sort_func(
        sort_: str = Query(None, alias="sort", enum=fields),
        direction: str = Query(None, enum=["asc", "desc"]),
    ) -> SORT:
        ret = {"sort": sort_, "reverse": direction == "desc"}
        return {k: v for k, v in ret.items() if v}  # type: ignore

    return Depends(sort_func)