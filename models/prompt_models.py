

from pydantic import BaseModel, Field
from typing import List, Optional


class Prompt_Generation(BaseModel):
    enhanced_prompt: str = Field(...,
                                 description="The enhanced prompt after processing")


class Decision_Agent(BaseModel):
    decision: str = Field(...,
                          description="The decision taken by the model. YES or NO")
