# prompt_loader.py

from typing import List, Dict, Any
import yaml
from pydantic import BaseModel, Field, ValidationError
from typing import Dict
# from prompt_loader.model import Config
from utils.logs.logging_utils import logger
from langchain_core.prompts import PromptTemplate


class PromptAgentTemplateModel(BaseModel):
    template: str = Field(..., min_length=10)
    input_variables: list[str] = Field(...)
    partial_variables: Dict[str, str] = Field(default_factory=dict)


class PartialVariable(BaseModel):
    # 'class' is a reserved keyword in Python
    class_: str = Field(..., alias='class')
    pydantic_object: str


class PromptTemplateModel(BaseModel):
    template: str
    input_variables: List[str]
    partial_variables: Dict[str, str]


class Prompts(BaseModel):
    prompt_generation_prompt: PromptTemplateModel
    decision_agent_prompt: PromptTemplateModel


def load_prompts_from_yaml(file_path: str) -> Prompts:
    """
    Loads prompt configurations from a YAML file and validates them against the Prompts model.

    Args:
        file_path (str): Path to the YAML configuration file.

    Returns:
        Prompts: An instance of the Prompts model containing all prompt configurations.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            yaml_data = yaml.safe_load(file)
            prompt_prompts = yaml_data.get('prompt_prompts', {})
            prompts = Prompts(**prompt_prompts)
            logger.info("Prompts loaded and validated successfully.")
            return prompts
    except FileNotFoundError:
        logger.error(f"YAML file not found at {file_path}")
        raise
    except ValidationError as ve:
        logger.error(f"Validation error while loading prompts: {ve}")
        raise
    except Exception as e:
        logger.error(f"Error loading prompts: {e}")
        raise

# prompt_loader.py

# import yaml
# from pydantic import BaseModel, Field, ValidationError
# from utils.logs.logging_utils import logger
# from langchain_core.prompts import PromptTemplate
# from typing import List, Dict, Any


# class PartialVariable(BaseModel):
#     # 'class' is a reserved keyword in Python
#     class_: str = Field(..., alias='class')
#     pydantic_object: str


# class PromptTemplateModel(BaseModel):
#     template: str
#     input_variables: List[str]
#     partial_variables: Dict[str, PartialVariable]


# class Prompts(BaseModel):
#     prompt_generation_prompt: PromptTemplateModel
#     decision_agent_prompt: PromptTemplateModel


# def load_prompts_from_yaml(file_path: str) -> Prompts:
#     """
#     Loads prompt configurations from a YAML file and validates them against the Config model.

#     Args:
#         file_path (str): Path to the YAML configuration file.

#     Returns:
#         Config: An instance of the Config model containing all prompt configurations.
#     """

#     try:
#         with open(file_path, 'r', encoding='utf-8') as file:
#             yaml_data = yaml.safe_load(file)
#             prompt_prompts = yaml_data.get('prompt_prompts', {})
#             prompts = Prompts(**prompt_prompts)
#             logger.info("Prompts loaded and validated successfully.")
#             return prompts
#     except FileNotFoundError:
#         logger.error(f"YAML file not found at {file_path}")
#         raise
#     except ValidationError as ve:
#         logger.error(f"Validation error while loading prompts: {ve}")
#         raise
#     except Exception as e:
#         logger.error(f"Error loading prompts: {e}")
#         raise


# def load_prompts_from_yaml(file_path: str) -> Prompts:
#     """
#     Loads prompt configurations from a YAML file and validates them against the Config model.

#     Args:
#         file_path (str): Path to the YAML configuration file.

#     Returns:
#         Config: An instance of the Config model containing all prompt configurations.
#     """

#     try:
#         with open(file_path, 'r', encoding='utf-8') as file:
#             yaml_data = yaml.safe_load(file)
#             config = Config(**yaml_data)
#             logger.info("Prompts loaded and validated successfully.")
#             return config
#     except FileNotFoundError:
#         logger.error(f"YAML file not found at {file_path}")
#         raise
#     except ValidationError as ve:
#         logger.error(f"Validation error while loading prompts: {ve}")
#         raise
#     except Exception as e:
#         logger.error(f"Error loading prompts: {e}")
#         raise

# prompt_loader.py

# import yaml
# from pydantic import BaseModel, Field, ValidationError
# from utils.logs.logging_utils import logger
# from typing import List, Dict, Any
# from models import Prompts, PartialVariable
# from object_instantiator import instantiate_object

# def load_prompts_from_yaml(file_path: str) -> Prompts:
#     """
#     Loads prompt configurations from a YAML file and validates them against the Prompts model.

#     Args:
#         file_path (str): Path to the YAML configuration file.

#     Returns:
#         Prompts: An instance of the Prompts model containing all prompt configurations.
#     """
#     try:
#         with open(file_path, 'r', encoding='utf-8') as file:
#             yaml_data = yaml.safe_load(file)
#             prompt_prompts = yaml_data.get('prompt_prompts', {})
#             prompts = Prompts(**prompt_prompts)
#             logger.info("Prompts loaded and validated successfully.")
#             return prompts
#     except FileNotFoundError:
#         logger.error(f"YAML file not found at {file_path}")
#         raise
#     except ValidationError as ve:
#         logger.error(f"Validation error while loading prompts: {ve}")
#         raise
#     except Exception as e:
#         logger.error(f"Error loading prompts: {e}")
#         raise
