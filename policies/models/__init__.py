"""
This package contains the Pydantic models and Enum classes used in the project.

Each file in this package represents a different domain model or Enum class. 
These models are used to enforce type checking, data validation, serialization,
and other features provided by the Pydantic library.

Note: 
- A Pydantic model is a class that inherits from `pydantic.BaseModel`.
- An Enum class is a class that inherits from `enum.Enum` or `enum.IntEnum`.

Please refer to the individual files for more details about each model or Enum
class.
"""
from .constants import Status
from .models import Task

__all__ = ['Status', 'Task']
