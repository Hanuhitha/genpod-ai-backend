from typing import List

from pydantic import BaseModel, Field, field_validator


class BacklogList(BaseModel):
    backlogs: List[str] = Field(..., description="List of backlog items")

    @field_validator('backlogs')
    @classmethod
    def check_backlog_items(cls, v):
        if not isinstance(v, list):
            raise ValueError('Backlogs must be a list')
        for item in v:
            if not isinstance(item, str):
                raise ValueError('Each backlog item must be a string')
        return v

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
