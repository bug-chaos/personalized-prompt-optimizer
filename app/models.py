from pydantic import BaseModel, Field


class OptimizeRequest(BaseModel):
    original_question: str = Field(
        ..., min_length=1, description="用户的原始问题"
    )
    user_profile: str = Field(
        ..., min_length=1, description="用户画像（背景、经验、约束条件）"
    )
    preferences: str = Field(
        ..., min_length=1, description="用户偏好（回答风格偏好、关注点）"
    )
    exclusions: str = Field(
        ..., min_length=1, description="排除项（用户不希望看到的内容）"
    )
    answer_style: str = Field(
        ..., min_length=1, description="回答风格（冷静、理性等）"
    )


class ScoreItem(BaseModel):
    relevance: float = Field(..., ge=1, le=10)
    personalization: float = Field(..., ge=1, le=10)
    specificity: float = Field(..., ge=1, le=10)
    actionability: float = Field(..., ge=1, le=10)
    non_generic: float = Field(..., ge=1, le=10)
    constraint_following: float = Field(..., ge=1, le=10)
    total_score: float = Field(..., ge=1, le=10)


class JudgeResult(BaseModel):
    best_answer_id: str = Field(..., pattern=r"^[ABC]$")
    scores: dict[str, ScoreItem]
    comparison_summary: str
    main_weaknesses: dict[str, str]
    prompt_improvement_suggestions: list[str]


class OptimizeResponse(BaseModel):
    prompt_candidates: dict[str, str]
    answers: dict[str, str]
    judge_result: JudgeResult
    best_prompt: str
    best_answer: str
    critique_report: str
    next_iteration_prompt: str
