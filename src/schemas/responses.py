from pydantic import BaseModel, Field


class UserRequest(BaseModel):
    """Minimal schema for validating incoming user input."""

    message: str = Field(..., description="The user's prompt or message.")


class AIResponse(BaseModel):
    """Minimal schema for structured response output from the AI service layer."""

    content: str = Field(..., description="The generated response text or user-friendly error message.")
    success: bool = Field(True, description="Flag indicating if the operation succeeded.")
    error_message: str | None = Field(None, description="Detailed error description if success is False.")

class RecipePick(BaseModel):
    """One recipe chosen by the model from the retrieved recipes."""

    recipe_name: str = Field(..., min_length=1, description="Exact name of a recipe from the given list.")
    reason: str = Field(..., min_length=1, max_length=400, description="Why this recipe fits the user.")


class RecipeRecommendation(BaseModel):
    """Structured recommendation returned by the model."""

    picks: list[RecipePick] = Field(default_factory=list, max_length=3)
    note: str | None = Field(None, description="Short note, e.g. if no recipe fits well.")