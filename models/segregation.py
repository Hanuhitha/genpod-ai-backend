from pydantic import BaseModel, Field
from typing_extensions import ClassVar


class Segregation(BaseModel):
    """
    """
    
    taskType: bool= Field(
        description="""
        This field holds the boolean value that specifies "True" if the given task involves funciton creation" or  "False" if the give task does not involves funciton.
        """, required=True
    )

    reason_for_classification: str =Field(
        description="""
        This field contains the reason for the classification"""
    )

