"""根据 Judge 结果生成 critique report 和 next_iteration_prompt"""

from app.models import OptimizeRequest
from app.llm_client import LLMClient

REFINER_SYSTEM_PROMPT = (
    "你是一个提示词优化专家。你的任务是根据评估结果，"
    "生成总结性批判报告和下一轮优化后的提示词。"
)

REFINER_USER_PROMPT_TEMPLATE = """## 原始问题
{original_question}

## 用户画像
{user_profile}

## 用户偏好
{preferences}

## 排除项
{exclusions}

## 回答风格要求
{answer_style}

---
## 最佳回答（{best_answer_id}）
{best_answer}

## 评分详情
{scores_detail}

## 各回答主要问题
{weaknesses_detail}

## 改进建议
{improvement_suggestions}

---
请基于以上信息，完成以下任务：

### 1. 总结性批判报告
用中文写一段 200-300 字的总结性批判报告，内容包括：
- 本轮优化中各个回答的表现
- 最佳回答为什么最佳
- 仍然存在的不足

### 2. 下一轮优化后的提示词
基于最佳回答和评估反馈，生成一个优化后的完整提示词。这个提示词应该：
- 保留最佳回答策略的优势
- 针对性地改进发现的不足
- 保持对用户画像、偏好、排除项的遵守
- 包含具体的回答要求

请按以下格式输出：
```
## Critique Report
<批判报告内容>

## Next Iteration Prompt
<优化后的提示词>
```
"""


def _format_scores_detail(judge_result: dict) -> str:
    """格式化评分详情"""
    lines = []
    for aid in ["A", "B", "C"]:
        score = judge_result.get("scores", {}).get(aid, {})
        lines.append(
            f"回答 {aid}: "
            f"relevance={score.get('relevance', 'N/A')}, "
            f"personalization={score.get('personalization', 'N/A')}, "
            f"specificity={score.get('specificity', 'N/A')}, "
            f"actionability={score.get('actionability', 'N/A')}, "
            f"non_generic={score.get('non_generic', 'N/A')}, "
            f"constraint_following={score.get('constraint_following', 'N/A')}, "
            f"total={score.get('total_score', 'N/A')}"
        )
    return "\n".join(lines)


def _format_weaknesses_detail(judge_result: dict) -> str:
    """格式化弱点详情"""
    weaknesses = judge_result.get("main_weaknesses", {})
    lines = []
    for aid in ["A", "B", "C"]:
        w = weaknesses.get(aid, "无")
        lines.append(f"回答 {aid}: {w}")
    return "\n".join(lines)


def _format_improvement_suggestions(judge_result: dict) -> str:
    """格式化改进建议"""
    suggestions = judge_result.get("prompt_improvement_suggestions", [])
    if not suggestions:
        return "暂无建议"
    return "\n".join(f"- {s}" for s in suggestions)


def generate_critique_report(
    client: LLMClient,
    req: OptimizeRequest,
    judge_result: dict,
    best_answer_id: str,
    best_answer: str,
) -> dict[str, str]:
    """生成批判报告和下一轮提示词"""
    scores_detail = _format_scores_detail(judge_result)
    weaknesses_detail = _format_weaknesses_detail(judge_result)
    improvement_suggestions = _format_improvement_suggestions(judge_result)

    user_prompt = REFINER_USER_PROMPT_TEMPLATE.format(
        original_question=req.original_question,
        user_profile=req.user_profile,
        preferences=req.preferences,
        exclusions=req.exclusions,
        answer_style=req.answer_style,
        best_answer_id=best_answer_id,
        best_answer=best_answer,
        scores_detail=scores_detail,
        weaknesses_detail=weaknesses_detail,
        improvement_suggestions=improvement_suggestions,
    )

    try:
        raw_response = client.generate(
            system_prompt=REFINER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=4096,
        )
    except Exception as e:
        raise RuntimeError(f"Refiner 调用失败: {e}") from e

    # 解析输出
    critique_report = ""
    next_prompt = ""

    if "## Critique Report" in raw_response:
        parts = raw_response.split("## Next Iteration Prompt")
        report_part = parts[0].replace("## Critique Report", "").strip()
        critique_report = report_part.strip()

        if len(parts) > 1:
            next_prompt = parts[1].strip()
    else:
        # 如果格式不符合预期，直接使用完整响应
        critique_report = raw_response
        next_prompt = raw_response

    return {
        "critique_report": critique_report,
        "next_iteration_prompt": next_prompt,
    }
