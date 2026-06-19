"""生成 A/B/C 三个不同策略的候选提示词"""

from app.models import OptimizeRequest


def _build_base_prompt(req: OptimizeRequest) -> str:
    return (
        f"## 用户原始问题\n{req.original_question}\n\n"
        f"## 用户画像\n{req.user_profile}\n\n"
        f"## 用户偏好\n{req.preferences}\n\n"
        f"## 用户排除项\n{req.exclusions}\n\n"
        f"## 回答风格要求\n{req.answer_style}"
    )


def generate_prompt_a(req: OptimizeRequest) -> str:
    """A：具体执行型"""
    base = _build_base_prompt(req)
    return (
        f"{base}\n\n"
        f"## 回答要求\n"
        f"请以「具体执行型」风格回答上述问题。你的回答必须：\n"
        f"1. 非常具体，包含可执行的步骤和行动项\n"
        f"2. 给出明确的判断标准和决策框架\n"
        f"3. 列出具体的下一步行动（what, how, when）\n"
        f"4. 提供可量化的评估指标\n"
        f"5. 避免空泛建议，每一条建议都必须有可操作性\n"
        f"6. 结合用户画像中的背景和约束条件\n\n"
        f"请用冷静、理性的语气回答。"
    )


def generate_prompt_b(req: OptimizeRequest) -> str:
    """B：反模板批判型"""
    base = _build_base_prompt(req)
    return (
        f"{base}\n\n"
        f"## 回答要求\n"
        f"请以「反模板批判型」风格回答上述问题。你的回答必须：\n"
        f"1. 完全不使用套话、鸡汤、泛泛建议\n"
        f"2. 批判性分析用户的问题和假设\n"
        f"3. 指出用户可能忽略的关键信息和盲点\n"
        f"4. 分析潜在风险和失败原因\n"
        f"5. 指出问题中缺失的关键信息，并说明为什么这些信息重要\n"
        f"6. 不迎合用户，给出可能不中听但真实的建议\n"
        f"7. 如果用户假设有问题，直接指出\n\n"
        f"请用冷静、理性的语气回答。"
    )


def generate_prompt_c(req: OptimizeRequest) -> str:
    """C：决策顾问型"""
    base = _build_base_prompt(req)
    return (
        f"{base}\n\n"
        f"## 回答要求\n"
        f"请以「决策顾问型」风格回答上述问题。你的回答必须：\n"
        f"1. 像专业顾问一样系统性地分析问题\n"
        f"2. 比较多个选项的收益、成本、风险和适用条件\n"
        f"3. 给出明确的验证方法和小规模测试方案\n"
        f"4. 提供决策矩阵或评估框架\n"
        f"5. 结合用户的具体约束条件（背景、资源、经验）\n"
        f"6. 给出分阶段的建议：短期可做什么、中期怎么规划\n"
        f"7. 说明每种选择的 trade-off 和妥协点\n\n"
        f"请用冷静、理性的语气回答。"
    )


def generate_all_prompts(req: OptimizeRequest) -> dict[str, str]:
    return {
        "A": generate_prompt_a(req),
        "B": generate_prompt_b(req),
        "C": generate_prompt_c(req),
    }
