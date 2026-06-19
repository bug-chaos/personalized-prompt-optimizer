# Personalized Prompt Optimizer v0.1

个性化 AI 回答优化器——一个**反馈驱动的提示词优化系统**，参考 PromptWizard 和 DSPy 的设计思路。

## 核心流程

```
用户问题 + 用户画像 + 偏好 + 排除项 + 回答风格
→ 生成 3 个不同策略的提示词候选
→ 分别调用 LLM 生成 3 个回答
→ 用 LLM Judge 对回答评分和比较
→ 选出最佳回答和最佳提示词
→ 输出 critique 报告和下一轮优化提示词
```

主要面向**开放式问题**：职业规划、学习路径、项目方向、人生建议、创意生成、决策辅助等。

## 项目结构

```
personalized-prompt-optimizer/
├── app/
│   ├── main.py               # FastAPI 应用入口
│   ├── models.py             # Pydantic 输入输出模型
│   ├── config.py             # 环境变量配置
│   ├── llm_client.py         # LLM 调用封装
│   ├── prompt_generator.py   # 提示词生成策略
│   ├── answer_generator.py   # 回答生成
│   ├── evaluator.py          # LLM Judge 评估
│   └── refiner.py            # 批判报告和优化
├── requirements.txt
├── .env.example
└── README.md
```

## 安装方式

```bash
# 1. 克隆项目
git clone <repo-url>
cd personalized-prompt-optimizer

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt
```

## 环境变量配置

复制 `.env.example` 为 `.env` 并填入配置：

```bash
cp .env.example .env
```

```ini
# OpenAI-compatible API 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

支持任何兼容 OpenAI API 的服务（OpenAI、Azure OpenAI、DeepSeek、通义千问等）。

## 启动命令

```bash
uvicorn app.main:app --reload --port 8000
```

API 文档将自动生成在：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 请求示例

```bash
curl -X POST "http://localhost:8000/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "original_question": "我应该继续做现在的 SaaS 项目，还是转去做 AI 工具？",
    "user_profile": "独立开发者，有 3 年后端经验，现金流有限，不喜欢重运营项目",
    "preferences": "希望答案直接、具体、偏商业可行性分析",
    "exclusions": "不要空泛鸡汤，不要只说看兴趣，不要给过于宏大的战略建议",
    "answer_style": "冷静、理性、批判性、可执行"
  }'
```

## API 返回示例

```json
{
  "prompt_candidates": {
    "A": "【具体执行型提示词】...",
    "B": "【反模板批判型提示词】...",
    "C": "【决策顾问型提示词】..."
  },
  "answers": {
    "A": "回答 A 的内容...",
    "B": "回答 B 的内容...",
    "C": "回答 C 的内容..."
  },
  "judge_result": {
    "best_answer_id": "C",
    "scores": {
      "A": {
        "relevance": 8,
        "personalization": 7,
        "specificity": 8,
        "actionability": 9,
        "non_generic": 7,
        "constraint_following": 9,
        "total_score": 8.1
      }
    },
    "comparison_summary": "回答 C 最好，因为...",
    "main_weaknesses": {
      "A": "回答 A 的主要问题",
      "B": "回答 B 的主要问题",
      "C": "回答 C 的主要问题"
    },
    "prompt_improvement_suggestions": [
      "下一轮优化建议 1",
      "下一轮优化建议 2"
    ]
  },
  "best_prompt": "最佳提示词内容",
  "best_answer": "最佳回答内容",
  "critique_report": "总结性批判报告",
  "next_iteration_prompt": "下一轮优化后的提示词"
}
```

## 评分指标

| 指标 | 权重 | 说明 |
|------|------|------|
| relevance | 20% | 是否正面回应原问题 |
| personalization | 20% | 是否使用用户画像 |
| specificity | 20% | 是否具体，有例子、判断标准或步骤 |
| actionability | 20% | 用户是否知道下一步做什么 |
| non_generic | 10% | 是否避免模板化、套话、空话 |
| constraint_following | 10% | 是否遵守排除项和偏好 |

### 惩罚规则

- 违反排除项 → constraint_following 不高于 4
- 大量空话/鸡汤 → non_generic 不高于 4
- 未使用用户画像 → personalization 不高于 4

## 提示词策略

### A：具体执行型
具体、可执行、有步骤、有判断标准、有下一步行动。

### B：反模板批判型
避免空话和鸡汤、不迎合用户、指出信息缺失和潜在风险。

### C：决策顾问型
系统性分析、多选项比较、收益/成本/风险评估、验证方法。

## 鲁棒性处理

- 输入字段为空时返回 422
- LLM 调用失败时返回清晰错误信息
- Judge JSON 解析失败时不会导致服务崩溃
- API Key 仅从环境变量读取，不写入代码

## 后续扩展方向

- 增加更多提示词策略（如角色扮演型、数据驱动型）
- 增加用户反馈闭环（人工评分反馈）
- 增加历史记录和对话管理
- 增加多轮 prompt refinement 迭代
- 增加 DSPy 风格 optimizer（自动提示词优化）
- 增加 PromptWizard 风格 critique-synthesis 循环
- 增加前端可视化评分面板

## License

MIT
