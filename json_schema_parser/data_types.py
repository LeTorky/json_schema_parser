import datetime
from enum import Enum
from typing import Any, List, Optional, Type, Union, get_args
from uuid import UUID


class DataType(str, Enum):
    INTEGER = "integer"
    LIST_INTEGER = "integer[]"
    OPTIONAL_INTEGER = "integer?"
    OPTIONAL_LIST_INTEGER = "integer[]?"

    FLOAT = "float"
    LIST_FLOAT = "float[]"
    OPTIONAL_FLOAT = "float?"
    OPTIONAL_LIST_FLOAT = "float[]?"

    STRING = "string"
    LIST_STRING = "string[]"
    OPTIONAL_STRING = "string?"
    OPTIONAL_LIST_STRING = "string[]?"

    BOOLEAN = "boolean"
    LIST_BOOLEAN = "boolean[]"
    OPTIONAL_BOOLEAN = "boolean?"
    OPTIONAL_LIST_BOOLEAN = "boolean[]?"

    JSON = "json"
    LIST_JSON = "json[]"
    OPTIONAL_JSON = "json?"
    OPTIONAL_LIST_JSON = "json[]?"

    UUID = "uuid"
    LIST_UUID = "uuid[]"
    OPTIONAL_UUID = "uuid?"
    OPTIONAL_LIST_UUID = "uuid[]?"

    DATETIME = "datetime"
    LIST_DATETIME = "datetime[]"
    OPTIONAL_DATETIME = "datetime?"
    OPTIONAL_LIST_DATETIME = "datetime[]?"

    @property
    def is_many(self) -> bool:
        return "[]" in self.value

    @property
    def is_optional(self) -> bool:
        return "?" in self.value


PRIMITIVE_TYPES_DICT = {
    DataType.INTEGER: int,
    DataType.OPTIONAL_INTEGER: Optional[int],
    DataType.FLOAT: float,
    DataType.OPTIONAL_FLOAT: Optional[float],
    DataType.STRING: str,
    DataType.OPTIONAL_STRING: Optional[str],
    DataType.BOOLEAN: bool,
    DataType.OPTIONAL_BOOLEAN: Optional[bool],
    DataType.DATETIME: datetime.datetime,
    DataType.OPTIONAL_DATETIME: Optional[datetime.datetime],
    DataType.UUID: UUID,
    DataType.OPTIONAL_UUID: Optional[UUID]
}

ITERABLE_PRIMITIVE_TYPES_DICT = {
    DataType.LIST_INTEGER: List[int],
    DataType.OPTIONAL_LIST_INTEGER: Optional[List[int]],
    DataType.LIST_FLOAT: List[float],
    DataType.OPTIONAL_LIST_FLOAT: Optional[List[float]],
    DataType.LIST_STRING: List[str],
    DataType.OPTIONAL_LIST_STRING: Optional[List[str]],
    DataType.LIST_BOOLEAN: List[bool],
    DataType.OPTIONAL_LIST_BOOLEAN: Optional[List[bool]],
    DataType.LIST_DATETIME: List[datetime.datetime],
    DataType.OPTIONAL_LIST_DATETIME: Optional[List[datetime.datetime]],
    DataType.LIST_UUID: List[UUID],
    DataType.OPTIONAL_LIST_UUID: Optional[List[UUID]],
}

COMPLEX_TYPES_DICT = {
    DataType.JSON: dict,
    DataType.LIST_JSON: List[dict],
    DataType.OPTIONAL_JSON: Optional[dict],
    DataType.OPTIONAL_LIST_JSON: Optional[List[dict]],
}

FULL_PRIMITIVE_TYPES_DICT = {
    **PRIMITIVE_TYPES_DICT,
    **ITERABLE_PRIMITIVE_TYPES_DICT,
}

PYTHON_TYPES_DICT = {
    **FULL_PRIMITIVE_TYPES_DICT,
    **COMPLEX_TYPES_DICT,
}

PRIMITIVE_TO_DATA_TYPE_LOOKUP = {
    value: key
    for key, value in PYTHON_TYPES_DICT.items()
}


def __extract_primitive_type(typing: Type | Union[Type, None]) -> Type | Union[Type, None]:

    extracted_args = get_args(typing)
    extracted_arg = extracted_args[0] if extracted_args else None

    return typing if not extracted_arg else __extract_primitive_type(extracted_arg)


def extract_primitive_type(data_type: DataType) -> Any:
    typing = PYTHON_TYPES_DICT[data_type]
    return __extract_primitive_type(typing)


def is_default_value_valid(value: Any, data_type: DataType) -> bool:
    if value is ...:  # Ellipsis means "required / no default" — always valid
        return True
    PrimitiveType = extract_primitive_type(data_type)
    if data_type.is_many:
        # if value is list of JSON then optional value should be list or None.
        if data_type == DataType.OPTIONAL_LIST_JSON:
            return (isinstance(value, list) and len(value) == 0) or value is None

        return isinstance(value, list) and all(
            isinstance(item, (PrimitiveType, type(None))) for item in value
        )
    else:
        # if value is JSON then optional value should be None.
        if data_type == DataType.OPTIONAL_JSON:
            return value is None

        return isinstance(value, (PrimitiveType, type(None)))


def get_default_value(data_type: DataType, default_value: Any) -> Any:
    # TODO: Adjust flow for validation before getting default value.
    if default_value is None:
        return None if data_type.is_optional else ...

    PrimitiveType = extract_primitive_type(data_type)

    data_type_coersion_constructor_lookup = {
        datetime.datetime: datetime.datetime.fromisoformat,
        UUID: UUID,
    }

    if PrimitiveType in data_type_coersion_constructor_lookup:
        Constructor = data_type_coersion_constructor_lookup[PrimitiveType]
        if data_type.is_many:
            return [
                Constructor(item) if item is not None else None
                for item in default_value
            ]
        return Constructor(default_value)

    return default_value
