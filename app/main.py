"""Personalized Prompt Optimizer v0.1 - FastAPI 主入口"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse

from app.models import OptimizeRequest, OptimizeResponse, ScoreItem
from app.llm_client import LLMClient
from app.prompt_generator import generate_all_prompts
from app.answer_generator import generate_answers
from app.evaluator import evaluate
from app.refiner import generate_critique_report

app = FastAPI(
    title="Personalized Prompt Optimizer v0.1",
    description="反馈驱动的个性化提示词优化系统",
    version="0.1.0",
)


HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 回答优化器</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f0f2f5; color: #333; line-height: 1.6; padding: 20px;
  }
  .container { max-width: 900px; margin: 0 auto; }
  h1 { text-align: center; color: #1a1a2e; margin-bottom: 8px; font-size: 28px; }
  .subtitle { text-align: center; color: #666; margin-bottom: 24px; font-size: 14px; }
  .card {
    background: #fff; border-radius: 12px; padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px;
  }
  .card h2 { font-size: 18px; margin-bottom: 16px; color: #1a1a2e; }
  .form-group { margin-bottom: 16px; }
  label { display: block; font-weight: 600; font-size: 14px; margin-bottom: 4px; color: #444; }
  label small { font-weight: 400; color: #999; }
  textarea {
    width: 100%; padding: 10px 12px; border: 1px solid #d9d9d9; border-radius: 8px;
    font-size: 14px; font-family: inherit; resize: vertical; transition: border-color .2s;
  }
  textarea:focus { outline: none; border-color: #4f46e5; box-shadow: 0 0 0 3px rgba(79,70,229,0.1); }
  textarea.sm { min-height: 60px; }
  textarea.md { min-height: 100px; }
  .btn {
    display: block; width: 100%; padding: 12px; border: none; border-radius: 8px;
    font-size: 16px; font-weight: 600; cursor: pointer; transition: all .2s;
    background: #4f46e5; color: #fff;
  }
  .btn:hover { background: #4338ca; }
  .btn:disabled { background: #a5b4fc; cursor: not-allowed; }
  .loading { text-align: center; padding: 40px; display: none; }
  .spinner {
    width: 40px; height: 40px; border: 4px solid #e5e7eb; border-top-color: #4f46e5;
    border-radius: 50%; animation: spin .8s linear infinite; margin: 0 auto 12px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .result { display: none; }
  .result .card { border-left: 4px solid #4f46e5; }
  .result .card.best { border-left-color: #059669; background: #f0fdf4; }
  .tabs { display: flex; gap: 4px; margin-bottom: 12px; }
  .tab-btn {
    flex: 1; padding: 8px; border: 1px solid #d9d9d9; border-radius: 6px;
    background: #fff; cursor: pointer; font-size: 13px; font-weight: 600;
    transition: all .2s; text-align: center;
  }
  .tab-btn:hover { border-color: #4f46e5; }
  .tab-btn.active { background: #4f46e5; color: #fff; border-color: #4f46e5; }
  .tab-content { display: none; }
  .tab-content.active { display: block; }
  .score-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 12px 0; }
  .score-item { background: #f9fafb; border-radius: 8px; padding: 12px; text-align: center; }
  .score-item .label { font-size: 12px; color: #666; }
  .score-item .value { font-size: 24px; font-weight: 700; color: #4f46e5; }
  .content-box {
    background: #f9fafb; border-radius: 8px; padding: 16px;
    white-space: pre-wrap; font-size: 14px; line-height: 1.7; max-height: 400px; overflow-y: auto;
  }
  .error-msg { color: #dc2626; background: #fef2f2; padding: 12px; border-radius: 8px; display: none; }
  .tag {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 12px; font-weight: 600; margin-left: 6px;
  }
  .tag-a { background: #dbeafe; color: #1e40af; }
  .tag-b { background: #fce7f3; color: #9d174d; }
  .tag-c { background: #d1fae5; color: #065f46; }
  .meta { font-size: 13px; color: #888; margin-top: 4px; }
  .weakness-item { padding: 8px 12px; margin: 4px 0; border-radius: 6px; background: #fefce8; font-size: 14px; }
  pre { white-space: pre-wrap; word-break: break-word; }
  @media (max-width: 600px) { .score-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
</head>
<body>
<div class="container">
  <h1>🧠 AI 回答优化器</h1>
  <p class="subtitle">输入你的问题和个人信息，系统会生成 3 个不同策略的回答并选出最佳方案</p>

  <div class="card">
    <h2>📝 输入信息</h2>
    <div class="form-group">
      <label>你的问题 <small>你想问什么？</small></label>
      <textarea id="question" class="md" placeholder="例如：我应该继续做现在的 SaaS 项目，还是转去做 AI 工具？">我应该继续做现在的 SaaS 项目，还是转去做 AI 工具？</textarea>
    </div>
    <div class="form-group">
      <label>用户画像 <small>你的背景、经验、资源情况</small></label>
      <textarea id="profile" class="sm" placeholder="例如：独立开发者，3 年后端经验，现金流有限">独立开发者，有 3 年后端经验，现金流有限，不喜欢重运营项目</textarea>
    </div>
    <div class="form-group">
      <label>偏好 <small>你希望回答侧重什么？</small></label>
      <textarea id="preferences" class="sm" placeholder="例如：希望答案直接、具体、偏商业可行性分析">希望答案直接、具体、偏商业可行性分析</textarea>
    </div>
    <div class="form-group">
      <label>排除项 <small>你不想看到什么内容？</small></label>
      <textarea id="exclusions" class="sm" placeholder="例如：不要空泛鸡汤">不要空泛鸡汤，不要只说看兴趣，不要给过于宏大的战略建议</textarea>
    </div>
    <div class="form-group">
      <label>回答风格 <small>你希望的语气和调性</small></label>
      <textarea id="style" class="sm" placeholder="例如：冷静、理性、批判性、可执行">冷静、理性、批判性、可执行</textarea>
    </div>
    <button class="btn" id="submitBtn" onclick="submitOptimize()">🚀 开始优化</button>
    <div class="error-msg" id="errorMsg"></div>
  </div>

  <div class="loading" id="loading">
    <div class="spinner"></div>
    <p>正在生成 3 个策略的回答，并评估最佳方案...</p>
    <p class="meta">这可能需要 30-60 秒</p>
  </div>

  <div class="result" id="result">
    <div class="card best" id="bestSection">
      <h2>🏆 最佳回答</h2>
      <p class="meta">最佳策略: <strong id="bestLabel"></strong></p>
      <div class="content-box" id="bestAnswer"></div>
    </div>

    <div class="card">
      <h2>📊 评分对比</h2>
      <div class="score-grid" id="scoreGrid"></div>
      <div style="margin-top:12px; font-size:14px; color:#555;" id="comparisonSummary"></div>
    </div>

    <div class="card">
      <h2>💬 三个回答对比</h2>
      <div class="tabs">
        <div class="tab-btn active" onclick="switchTab('A', this)">策略 A <span class="tag tag-a">执行型</span></div>
        <div class="tab-btn" onclick="switchTab('B', this)">策略 B <span class="tag tag-b">批判型</span></div>
        <div class="tab-btn" onclick="switchTab('C', this)">策略 C <span class="tag tag-c">顾问型</span></div>
      </div>
      <div class="tab-content active" id="tabA">
        <div class="content-box" id="answerA"></div>
      </div>
      <div class="tab-content" id="tabB">
        <div class="content-box" id="answerB"></div>
      </div>
      <div class="tab-content" id="tabC">
        <div class="content-box" id="answerC"></div>
      </div>
    </div>

    <div class="card">
      <h2>🔍 各回答不足</h2>
      <div id="weaknesses"></div>
    </div>

    <div class="card">
      <h2>📋 批判报告</h2>
      <div class="content-box" id="critiqueReport"></div>
    </div>

    <div class="card">
      <h2>🔄 下一轮优化提示词</h2>
      <div class="content-box" id="nextPrompt"></div>
    </div>

    <div class="card">
      <h2>💡 优化建议</h2>
      <div id="suggestions"></div>
    </div>
  </div>
</div>

<script>
async function submitOptimize() {
  const btn = document.getElementById('submitBtn');
  const loading = document.getElementById('loading');
  const result = document.getElementById('result');
  const errorMsg = document.getElementById('errorMsg');

  errorMsg.style.display = 'none';
  result.style.display = 'none';
  btn.disabled = true;
  loading.style.display = 'block';

  try {
    const res = await fetch('/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        original_question: document.getElementById('question').value.trim(),
        user_profile: document.getElementById('profile').value.trim(),
        preferences: document.getElementById('preferences').value.trim(),
        exclusions: document.getElementById('exclusions').value.trim(),
        answer_style: document.getElementById('style').value.trim()
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '请求失败');
    }

    const data = await res.json();
    displayResult(data);
  } catch (err) {
    errorMsg.textContent = '❌ ' + err.message;
    errorMsg.style.display = 'block';
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}

function displayResult(data) {
  const jr = data.judge_result;
  const bestId = jr.best_answer_id;

  // 最佳回答
  document.getElementById('bestLabel').textContent = bestId === 'A' ? 'A - 具体执行型' : bestId === 'B' ? 'B - 反模板批判型' : 'C - 决策顾问型';
  document.getElementById('bestAnswer').textContent = data.best_answer;

  // 评分
  const scoreGrid = document.getElementById('scoreGrid');
  scoreGrid.innerHTML = '';
  for (const [id, sc] of Object.entries(jr.scores)) {
    const label = id === 'A' ? 'A · 执行型' : id === 'B' ? 'B · 批判型' : 'C · 顾问型';
    const highlight = id === bestId ? ' style="background:#f0fdf4;border:2px solid #059669;"' : '';
    scoreGrid.innerHTML += `
      <div class="score-item"${highlight}>
        <div class="label">${label}</div>
        <div class="value">${sc.total_score.toFixed(1)}</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">
          R${sc.relevance} P${sc.personalization} S${sc.specificity}<br>
          A${sc.actionability} N${sc.non_generic} C${sc.constraint_following}
        </div>
      </div>`;
  }
  document.getElementById('comparisonSummary').textContent = jr.comparison_summary;

  // 三个回答
  document.getElementById('answerA').textContent = data.answers.A || '生成失败';
  document.getElementById('answerB').textContent = data.answers.B || '生成失败';
  document.getElementById('answerC').textContent = data.answers.C || '生成失败';

  // 弱点
  const weaknessesDiv = document.getElementById('weaknesses');
  weaknessesDiv.innerHTML = '';
  for (const [id, w] of Object.entries(jr.main_weaknesses)) {
    const label = id === 'A' ? 'A · 执行型' : id === 'B' ? 'B · 批判型' : 'C · 顾问型';
    weaknessesDiv.innerHTML += `<div class="weakness-item"><strong>${label}</strong>：${w}</div>`;
  }

  // 批判报告
  document.getElementById('critiqueReport').textContent = data.critique_report || '暂无';

  // 下一轮提示词
  document.getElementById('nextPrompt').textContent = data.next_iteration_prompt || '暂无';

  // 优化建议
  const suggestionsDiv = document.getElementById('suggestions');
  suggestionsDiv.innerHTML = '';
  if (jr.prompt_improvement_suggestions && jr.prompt_improvement_suggestions.length) {
    jr.prompt_improvement_suggestions.forEach(s => {
      suggestionsDiv.innerHTML += `<div class="weakness-item" style="background:#eff6ff;">💡 ${s}</div>`;
    });
  }

  document.getElementById('result').style.display = 'block';
  document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
}

function switchTab(id, btn) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('tab' + id).classList.add('active');
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"},
    )


def _build_score_item(score_dict: dict) -> ScoreItem:
    return ScoreItem(
        relevance=score_dict.get("relevance", 1),
        personalization=score_dict.get("personalization", 1),
        specificity=score_dict.get("specificity", 1),
        actionability=score_dict.get("actionability", 1),
        non_generic=score_dict.get("non_generic", 1),
        constraint_following=score_dict.get("constraint_following", 1),
        total_score=score_dict.get("total_score", 1),
    )


@app.post("/optimize", response_model=OptimizeResponse)
async def optimize(req: OptimizeRequest):
    """
    完整的提示词优化流程：
    1. 生成 3 个候选提示词
    2. 生成 3 个回答
    3. LLM Judge 评估
    4. 生成批判报告和下一轮提示词
    """
    # 初始化 LLM 客户端
    try:
        client = LLMClient()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 1. 生成候选提示词
    try:
        prompt_candidates = generate_all_prompts(req)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"生成候选提示词失败: {e}"
        )

    # 2. 生成回答
    try:
        answers = generate_answers(client, prompt_candidates)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"生成回答失败: {e}"
        )

    # 3. LLM Judge 评估
    try:
        judge_data = evaluate(
            client=client,
            original_question=req.original_question,
            user_profile=req.user_profile,
            preferences=req.preferences,
            exclusions=req.exclusions,
            answer_style=req.answer_style,
            answers=answers,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"LLM Judge 评估失败: {e}"
        )

    best_answer_id = judge_data.get("best_answer_id", "A")
    best_answer = answers.get(best_answer_id, answers.get("A", ""))
    best_prompt = prompt_candidates.get(
        best_answer_id, prompt_candidates.get("A", "")
    )

    # 4. 生成批判报告和下一轮提示词
    try:
        refiner_result = generate_critique_report(
            client=client,
            req=req,
            judge_result=judge_data,
            best_answer_id=best_answer_id,
            best_answer=best_answer,
        )
    except Exception as e:
        # 如果 refiner 失败，使用 fallback
        refiner_result = {
            "critique_report": f"生成批判报告失败: {e}",
            "next_iteration_prompt": best_prompt,
        }

    # 5. 构建响应
    scores = {}
    for aid in ["A", "B", "C"]:
        raw_score = judge_data.get("scores", {}).get(aid, {})
        scores[aid] = _build_score_item(raw_score)

    return OptimizeResponse(
        prompt_candidates=prompt_candidates,
        answers=answers,
        judge_result={
            "best_answer_id": best_answer_id,
            "scores": scores,
            "comparison_summary": judge_data.get(
                "comparison_summary", ""
            ),
            "main_weaknesses": judge_data.get(
                "main_weaknesses", {"A": "", "B": "", "C": ""}
            ),
            "prompt_improvement_suggestions": judge_data.get(
                "prompt_improvement_suggestions", []
            ),
        },
        best_prompt=best_prompt,
        best_answer=best_answer,
        critique_report=refiner_result.get("critique_report", ""),
        next_iteration_prompt=refiner_result.get(
            "next_iteration_prompt", best_prompt
        ),
    )
