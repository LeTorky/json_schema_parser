from datetime import datetime
from typing import Any, Dict, Tuple, Type, Union, Literal, Optional, List, cast, get_args, get_origin
from functools import singledispatchmethod
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator, create_model
from pydantic_core import PydanticUndefined
from pydantic.fields import FieldInfo

from json_schema_parser.data_types import (
    PRIMITIVE_TO_DATA_TYPE_LOOKUP,
    DataType,
    PYTHON_TYPES_DICT,
    is_default_value_valid,
    get_default_value
)

# Type alias for Pydantic model types
PydanticModelType = Type[RootModel]
PydanticModel = BaseModel


class SimpleTypeInput(BaseModel):
    """
    this class represents the simple type structure of the json schema input
    """
    model_config = ConfigDict(
        extra='forbid'
    )

    field_type: Literal[
        DataType.INTEGER,
        DataType.STRING,
        DataType.BOOLEAN,
        DataType.FLOAT,
        DataType.JSON,
        DataType.DATETIME,
        DataType.UUID
    ]
    is_many: bool = False
    is_optional: bool = False
    field_default_value: Any = None
    description: str = ""

    @field_validator('field_type', mode='before')
    def validate_field_type(cls, value):
        return DataType(value)

    @model_validator(mode='after')
    def validate_field_default_value(self):
        if not is_default_value_valid(self.default_value, self.data_type):
            raise Exception(
                f"Default value {self.default_value} is invalid for {self.field_type}.")
        return self

    @property
    def primitive_type(self) -> Type:
        python_type = PYTHON_TYPES_DICT[self.data_type]
        return python_type

    @property
    def data_type(self) -> DataType:
        field_type = self.field_type
        field_type_value = field_type.value

        if self.is_many:
            field_type_value += '[]'
        if self.is_optional:
            field_type_value += '?'

        data_type = DataType(field_type_value)

        return data_type

    @property
    def default_value(self):
        default_value = get_default_value(
            self.data_type, self.field_default_value)
        return default_value

    @property
    def pydantic_field(self) -> Tuple[Type, FieldInfo]:
        return (self.primitive_type, Field(self.default_value, description=self.description))


class ComplexTypeInput(
    RootModel[
        Dict[
            str,
            Union[
                'ComplexTypeInput',
                'SimpleTypeInput'
            ]
        ]
    ]
):
    """
    this class represents the complex type structure of the json input
    which is a dictionary that map the name of the property and the type of it.
    the type of the property could be SimpleTypeInput or ComplexTypeInput
    The Request Body will look like so:
        {
            "optional_string_list": {
                "field_type": "string",
                "is_many": True,
                "is_optional": True,
                "field_default_value": [],
                "description": "Optional string list"
            },
            "required_integer": {
                "field_type": "integer",
                "is_many": False,
                "is_optional": False,
                "field_default_value": None,
                "description": "Required integer"
            },
            "nested_object": {
                "__config": {
                    "field_type": "json",
                    "is_many": False,
                    "is_optional": False,
                    "field_default_value": None,
                    "description": "Nested object"
                },
                "nested_string": {
                    "field_type": "string",
                    "is_many": False,
                    "is_optional": False,
                    "field_default_value": None,
                    "description": "nested string",
                }
            },
            "nested_object_list": {
                "__config": {
                    "field_type": "json",
                    "is_many": True,
                    "is_optional": False,
                    "field_default_value": None,
                    "description": "Nested object"
                },
                "nested_string": {
                    "field_type": "string",
                    "is_many": False,
                    "is_optional": False,
                    "field_default_value": None,
                    "description": "nested string",
                }
            },
            "__config": {
                "field_type": "json",
                "is_many": False,
                "is_optional": False,
                "field_default_value": None,
                "description": "key description"
            }
        }
    """

    @property
    def config(self) -> SimpleTypeInput:
        return cast(SimpleTypeInput, self.root['__config'])


class JsonSchemaParser(RootModel[
    Union[
        SimpleTypeInput,
        ComplexTypeInput
    ]
]):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    __is_simple_type: Optional[bool] = None  # type: ignore
    __pydantic_model: Optional[PydanticModelType] = None  # type: ignore

    # this function will be automaticaly executed after pydantic finishing the class initialization
    def model_post_init(self, __context: dict) -> None:
        self.__is_simple_type = isinstance(self.root, SimpleTypeInput)

    @property
    def is_simple_type(self) -> bool:
        if self.__is_simple_type is None:
            raise Exception("The model post init hasn't been executed yet.")
        return self.__is_simple_type

    @property
    def simple_type(self) -> Type:
        if self.__is_simple_type is False:
            raise Exception(
                "The generated model doesn't represent a simple type")
        return cast(SimpleTypeInput, self.root).primitive_type

    @singledispatchmethod
    def __generate_pydantic_model(self, schema, model_name: str) -> PydanticModelType:
        raise NotImplementedError(
            f"No overloaded method defined for {type(schema)}")

    @__generate_pydantic_model.register(SimpleTypeInput)
    def _(self, schema: SimpleTypeInput, model_name: str) -> PydanticModelType:
        schema_type = schema.primitive_type
        return RootModel[schema_type]

    @__generate_pydantic_model.register(ComplexTypeInput)
    def _(self, schema: ComplexTypeInput, model_name: str) -> PydanticModelType:
        fields = {}
        config = schema.config

        for key, value in schema.root.items():
            if key == '__config':
                continue

            inner_model = self.__generate_pydantic_model(value, key)
            default_value = (
                value.default_value if isinstance(value, SimpleTypeInput)
                else value.config.default_value
            )
            is_optional = (
                value.is_optional if isinstance(value, SimpleTypeInput)
                else value.config.is_optional
            )

            fields[key] = (
                inner_model,
                ... if not is_optional else default_value
            )

        created_model = create_model(model_name, **fields)

        if config.is_many:
            created_model = List[created_model]
        if config.is_optional:
            created_model = Optional[created_model]

        created_model = RootModel[created_model]

        return created_model

    def generate_pydantic_model(self, model_name: str) -> PydanticModelType:
        if self.__pydantic_model is None:
            created_model = self.__generate_pydantic_model(
                self.root, model_name)
            self.__pydantic_model = created_model
        return self.__pydantic_model

    @staticmethod
    def __json_schema_parse_default_values(value: Any) -> Any:
        value = value() if callable(value) else value

        is_list = isinstance(value, list)
        values = value if is_list else [value]

        if values and isinstance(values[0], (datetime, UUID)):
            values = [
                str(entry)
                for entry in values
            ]

        if is_list:
            return values

        return values[0]

    @staticmethod
    def __generate_json_schema_from_data_type(
            primitive_type: Type,
            description: str = "",
            field_default_value: Any = None
    ) -> Dict[str, Any]:

        config = {
            "field_type": None,
            "is_many": False,
            "is_optional": False,
            "description": description,
            "field_default_value": field_default_value
        }

        is_primitive_type_nested = True
        while is_primitive_type_nested:
            typing_wrapper = get_origin(primitive_type)
            if typing_wrapper:
                is_primitive_type_nested = True
                if typing_wrapper == Union:
                    config["is_optional"] = True
                elif typing_wrapper == list:
                    config["is_many"] = True
                primitive_type = get_args(primitive_type)[0]
            else:
                is_primitive_type_nested = False
        try:
            simple_data_type = PRIMITIVE_TO_DATA_TYPE_LOOKUP.get(
                primitive_type)
        except Exception:
            simple_data_type = None

        # Simple types.
        if simple_data_type:
            config["field_type"] = simple_data_type.value

        # Complex types.
        else:
            config["field_type"] = DataType.JSON.value
            config = {
                "__config": config
            }
            for key, value in primitive_type.__fields__.items():
                config[key] = JsonSchemaParser.__generate_json_schema_from_data_type(
                    value.annotation,
                    value.description,
                    None if value.default == PydanticUndefined else
                    JsonSchemaParser.__json_schema_parse_default_values(
                        value.default)
                )

        return config

    @staticmethod
    def generate_json_schema_from_data_type(primitive_type: Type) -> Dict[str, Any]:
        """
        Generates a JSON schema representation from a given primitive data type.
        This function converts a Python primitive type or a Pydantic model into a JSON schema
        string that describes the data structure and its properties.
        Args:
            primitive_type (Type): The primitive type or Pydantic model to convert to JSON schema.
                Can be a basic Python type (str, int, etc.) or a Pydantic model class.
        Returns:
            str: A JSON string representing the schema of the input type, including:
                - field_type: The base data type
                - is_many: Boolean indicating if it's a collection
                - is_optional: Boolean indicating if the field is optional
                - description: Field description string
                - field_default_value: Default value if any
                For Pydantic models, returns nested schema with __config and field definitions.
        Example:
            >>> generate_json_schema_from_data_type(str)
            {
                "field_type": "STRING",
                "is_many": false,
                "is_optional": false,
                "description": "",
                "field_default_value": null
            }
        """
        return JsonSchemaParser.__generate_json_schema_from_data_type(primitive_type)

    def is_empty(self) -> bool:
        """Checks if the JSON schema represents an empty structure (i.e., no fields defined).
        """
        if self.is_simple_type:
            return False
        else:
            complex_root = cast(ComplexTypeInput, self.root)
            return complex_root.root == {}
