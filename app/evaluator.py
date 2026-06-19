"""LLM Judge 模块：对回答进行评分和比较"""

import json
import re
from app.llm_client import LLMClient

JUDGE_SYSTEM_PROMPT = (
    "你是一个严格的 AI 回答评估专家（LLM Judge）。"
    "你的任务是对三个回答（A/B/C）进行评分和比较分析。"
    "你必须始终输出合法的 JSON 格式，不要包含 Markdown 代码块标记。"
)

JUDGE_USER_PROMPT_TEMPLATE = """## 原始问题
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
## 回答 A
{answer_a}

## 回答 B
{answer_b}

## 回答 C
{answer_c}

---
请对以上三个回答进行严格评估。

### 评分指标（每项 1-10 分）

- relevance：是否正面回应原问题
- personalization：是否使用用户画像
- specificity：是否具体，有例子、判断标准或步骤
- actionability：用户是否知道下一步做什么
- non_generic：是否避免模板化、套话、空话
- constraint_following：是否遵守排除项和偏好

### 惩罚规则（必须严格执行）
1. 如果回答明显违反排除项（exclusions），constraint_following 不得高于 4。
2. 如果回答大量空话、鸡汤、泛泛建议，non_generic 不得高于 4。
3. 如果回答没有使用 user_profile，personalization 不得高于 4。

### 总分公式
total_score = relevance * 0.20 + personalization * 0.20 + specificity * 0.20 + actionability * 0.20 + non_generic * 0.10 + constraint_following * 0.10

### 输出要求
你必须只输出一个合法的 JSON 对象，不要包含任何其他文字、Markdown 标记或代码块标记。注意不要使用 ```json 包裹。

输出 JSON 结构：
{{
  "scores": {{
    "A": {{
      "relevance": <int>,
      "personalization": <int>,
      "specificity": <int>,
      "actionability": <int>,
      "non_generic": <int>,
      "constraint_following": <int>,
      "total_score": <float>
    }},
    "B": {{...}},
    "C": {{...}}
  }},
  "comparison_summary": "<说明哪个回答最好以及原因（中文）>",
  "main_weaknesses": {{
    "A": "<回答 A 的主要问题（中文）>",
    "B": "<回答 B 的主要问题（中文）>",
    "C": "<回答 C 的主要问题（中文）>"
  }},
  "prompt_improvement_suggestions": [
    "<下一轮提示词优化建议 1（中文）>",
    "<下一轮提示词优化建议 2（中文）>"
  ]
}}
"""


def _parse_judge_response(text: str) -> dict:
    """解析 Judge 返回的 JSON，处理可能的格式问题"""
    # 尝试直接解析
    text = text.strip()

    # 移除可能的 Markdown 代码块标记
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 JSON 对象（从第一个 { 到最后一个 }）
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Judge 返回的 JSON 解析失败。原始响应：\n{text[:500]}"
    )


def evaluate(
    client: LLMClient,
    original_question: str,
    user_profile: str,
    preferences: str,
    exclusions: str,
    answer_style: str,
    answers: dict[str, str],
) -> dict:
    """调用 LLM Judge 对回答进行评估"""
    user_prompt = JUDGE_USER_PROMPT_TEMPLATE.format(
        original_question=original_question,
        user_profile=user_profile,
        preferences=preferences,
        exclusions=exclusions,
        answer_style=answer_style,
        answer_a=answers["A"],
        answer_b=answers["B"],
        answer_c=answers["C"],
    )

    try:
        raw_response = client.generate(
            system_prompt=JUDGE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        raise RuntimeError(f"LLM Judge 调用失败: {e}") from e

    result = _parse_judge_response(raw_response)

    # 确定最佳回答
    scores = result.get("scores", {})
    best_id = max(scores, key=lambda k: scores[k].get("total_score", 0))
    result["best_answer_id"] = best_id

    return result
