

# from pydantic import BaseModel, Field
# from typing import List, Optional

# class UserPrompt(BaseModel):
#     user_id: str = Field(..., description="Unique identifier for the user")
#     prompt: str = Field(..., description="The user's initial prompt")

# class EnhancedPrompt(BaseModel):
#     enhanced_prompt: str = Field(..., description="The enhanced prompt after processing")
#     suggestions: List[str] = Field(..., description="List of suggestions for improvement")

# class ConfirmationResponse(BaseModel):
#     user_id: str = Field(..., description="Unique identifier for the user")
#     confirmed: bool = Field(..., description="User's confirmation status")
#     final_prompt: Optional[str] = Field(None, description="The final prompt to proceed with")