# json-schema-parser

A Python library for converting between JSON schema definitions and Pydantic models.

## Features

- Parse a JSON schema dict into a validated Pydantic model
- Generate a JSON schema dict from any Python type or Pydantic model
- Supports all common types: `integer`, `float`, `string`, `boolean`, `json`, `uuid`, `datetime`
- Supports list (`is_many`) and optional (`is_optional`) variants of every type
- Nested object schemas via `ComplexTypeInput`

## Installation

```bash
pip install json-schema-parser
```

## Usage

### Parse a JSON schema into a Pydantic model

```python
from json_schema_parser import JsonSchemaParser

schema = {
    "__config": {"field_type": "json", "is_many": False, "is_optional": False, "field_default_value": None, "description": ""},
    "name": {"field_type": "string", "is_many": False, "is_optional": False, "field_default_value": None, "description": "User name"},
    "age":  {"field_type": "integer", "is_many": False, "is_optional": True, "field_default_value": None, "description": "User age"},
}

parser = JsonSchemaParser.model_validate(schema)
Model = parser.generate_pydantic_model("User")

user = Model.model_validate({"name": "Alice", "age": 30})
```

### Generate a JSON schema from a Python type

```python
from json_schema_parser import JsonSchemaParser
from pydantic import BaseModel
from typing import Optional, List

class Address(BaseModel):
    street: str
    city: str

schema = JsonSchemaParser.generate_json_schema_from_data_type(Address)
```

## Supported field types

| `field_type` value | Python type |
|---|---|
| `"integer"` | `int` |
| `"float"` | `float` |
| `"string"` | `str` |
| `"boolean"` | `bool` |
| `"uuid"` | `UUID` |
| `"datetime"` | `datetime` |
| `"json"` | `dict` / nested model |

Set `is_many: true` to get a `List[T]`, and `is_optional: true` to get `Optional[T]`.

## License

MIT
