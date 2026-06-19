"""用候选提示词生成回答"""

from app.llm_client import LLMClient

SYSTEM_PROMPT = (
    "你是一个专业的问题解答助手。请根据系统指令和用户画像，"
    "提供高质量、有深度的回答。回答必须符合要求的风格和标准。"
)


def generate_answers(
    client: LLMClient, prompt_candidates: dict[str, str]
) -> dict[str, str]:
    """对每个候选提示词生成对应的回答"""
    answers: dict[str, str] = {}

    for label, prompt in prompt_candidates.items():
        try:
            answer = client.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.7,
            )
            answers[label] = answer
        except Exception as e:
            raise RuntimeError(
                f"生成回答 {label} 失败: {e}"
            ) from e

    return answers
