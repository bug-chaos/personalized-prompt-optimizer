"""Personalized Prompt Optimizer v0.1.1 - FastAPI 主入口"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse

from app.models import OptimizeRequest, OptimizeResponse, ScoreItem
from app.llm_client import LLMClient
from app.prompt_generator import generate_all_prompts
from app.answer_generator import generate_answers
from app.evaluator import evaluate
from app.refiner import generate_critique_report

app = FastAPI(
    title="Personalized Prompt Optimizer v0.1.1",
    description="反馈驱动的个性化提示词优化系统",
    version="0.1.1",
)


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Personalized Prompt Optimizer</title>
<style>
  :root {
    --bg-body: #0f1117;
    --bg-panel: #171a21;
    --bg-card: #1f2330;
    --bg-input: #262b3a;
    --border: #2d3342;
    --border-hover: #3d4460;
    --primary: #7c8cff;
    --primary-dim: rgba(124,140,255,0.12);
    --text: #e5e7eb;
    --text-muted: #9ca3af;
    --text-dim: #6b7280;
    --success: #34d399;
    --warning: #fbbf24;
    --danger: #fb7185;
    --radius: 8px;
    --radius-lg: 12px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans SC', sans-serif;
    background: var(--bg-body);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
  }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  ::selection { background: var(--primary-dim); color: var(--primary); }

  .header {
    border-bottom: 1px solid var(--border);
    padding: 14px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg-panel);
  }
  .header-left h1 { font-size: 16px; font-weight: 600; color: var(--text); letter-spacing: 0.3px; }
  .header-left .sub { font-size: 12px; color: var(--text-muted); margin-top: 1px; }
  .header-right { display: flex; gap: 8px; }
  .badge {
    font-size: 11px; padding: 3px 10px; border-radius: 20px;
    background: var(--bg-card); border: 1px solid var(--border);
    color: var(--text-muted); font-weight: 500; letter-spacing: 0.2px;
  }
  .badge.primary { border-color: var(--primary); color: var(--primary); background: var(--primary-dim); }

  .layout {
    display: flex; gap: 0; height: calc(100vh - 55px);
    max-width: 1600px; margin: 0 auto;
  }
  .panel {
    padding: 20px; overflow-y: auto;
  }
  .panel-left {
    width: 420px; min-width: 420px;
    border-right: 1px solid var(--border);
    background: var(--bg-panel);
  }
  .panel-right {
    flex: 1; background: var(--bg-body);
  }

  .panel-title {
    font-size: 13px; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.8px;
    margin-bottom: 16px; padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
  }

  .field { margin-bottom: 14px; }
  .field label {
    display: block; font-size: 13px; font-weight: 500; color: var(--text);
    margin-bottom: 4px;
  }
  .field label small { color: var(--text-dim); font-weight: 400; margin-left: 4px; }
  .field textarea {
    width: 100%; padding: 10px 12px;
    background: var(--bg-input); border: 1px solid var(--border);
    border-radius: var(--radius); color: var(--text);
    font-size: 13px; font-family: inherit; resize: vertical;
    transition: border-color 0.15s; line-height: 1.5;
  }
  .field textarea:focus {
    outline: none; border-color: var(--primary);
    box-shadow: 0 0 0 2px var(--primary-dim);
  }
  .field textarea::placeholder { color: var(--text-dim); font-size: 12px; }
  .field textarea.sm { min-height: 54px; }
  .field textarea.md { min-height: 80px; }

  .actions { display: flex; gap: 8px; margin-top: 20px; }
  .btn {
    flex: 1; padding: 10px 16px; border: none; border-radius: var(--radius);
    font-size: 14px; font-weight: 600; cursor: pointer;
    transition: all 0.15s; font-family: inherit;
  }
  .btn-primary {
    background: var(--primary); color: #fff;
  }
  .btn-primary:hover { background: #6a7be8; }
  .btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-secondary {
    background: var(--bg-card); color: var(--text-muted);
    border: 1px solid var(--border);
  }
  .btn-secondary:hover { border-color: var(--border-hover); color: var(--text); }
  .btn-clear {
    background: transparent; color: var(--text-dim);
    border: 1px solid var(--border); flex: 0 0 auto; padding: 10px 14px;
  }
  .btn-clear:hover { color: var(--danger); border-color: var(--danger); }
  .btn-ghost {
    background: transparent; color: var(--text-dim);
    border: 1px solid var(--border); padding: 4px 10px;
    font-size: 11px; font-weight: 500; cursor: pointer;
    border-radius: 4px; transition: all 0.15s;
  }
  .btn-ghost:hover { border-color: var(--text-muted); color: var(--text); }

  .loading-overlay {
    display: none; position: absolute; inset: 0;
    background: rgba(15,17,23,0.85);
    backdrop-filter: blur(2px); z-index: 10;
    align-items: center; justify-content: center; flex-direction: column;
    border-radius: var(--radius-lg);
  }
  .loading-overlay.show { display: flex; }
  .spinner {
    width: 28px; height: 28px; border: 2px solid var(--border);
    border-top-color: var(--primary); border-radius: 50%;
    animation: spin 0.7s linear infinite; margin-bottom: 12px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-text { font-size: 13px; color: var(--text-muted); }

  .empty-state {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; height: 100%; gap: 12px;
    padding: 60px 40px; text-align: center;
  }
  .empty-state .icon { font-size: 36px; opacity: 0.3; }
  .empty-state h3 { font-size: 15px; color: var(--text-muted); font-weight: 500; }
  .empty-state p { font-size: 13px; color: var(--text-dim); max-width: 360px; line-height: 1.7; }

  .result-area { padding: 0; display: none; height: 100%; }
  .result-area.show { display: block; }

  .section { margin-bottom: 16px; }
  .section-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 10px;
  }
  .section-title {
    font-size: 13px; font-weight: 600; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.6px;
  }

  .best-card {
    background: linear-gradient(135deg, #1a2332 0%, #1f2330 100%);
    border: 1px solid rgba(124,140,255,0.25);
    border-radius: var(--radius-lg); padding: 20px;
    position: relative;
  }
  .best-card::before {
    content: 'BEST'; position: absolute; top: 10px; right: 14px;
    font-size: 10px; font-weight: 700; letter-spacing: 1px;
    color: var(--primary); opacity: 0.5;
  }
  .best-card .best-label {
    font-size: 12px; color: var(--primary); font-weight: 600;
    margin-bottom: 8px;
  }
  .best-card .best-score {
    font-size: 28px; font-weight: 700; color: var(--success);
    margin-bottom: 12px;
  }
  .best-card .best-score small {
    font-size: 14px; font-weight: 400; color: var(--text-muted);
  }
  .best-card .best-content {
    font-size: 14px; line-height: 1.8; color: var(--text);
    white-space: pre-wrap; max-height: 280px; overflow-y: auto;
    padding: 12px; background: rgba(0,0,0,0.2);
    border-radius: var(--radius); margin-top: 8px;
  }
  .best-card .best-prompt-preview {
    margin-top: 12px; padding: 10px 12px;
    background: rgba(0,0,0,0.15); border-radius: var(--radius);
    font-size: 12px; color: var(--text-dim);
    white-space: pre-wrap; max-height: 120px; overflow-y: auto;
    border-left: 2px solid var(--border);
  }

  .card-panel {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--radius-lg); padding: 16px;
    margin-bottom: 14px;
  }

  .score-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .score-table th {
    text-align: left; padding: 8px 10px;
    color: var(--text-dim); font-weight: 500;
    border-bottom: 1px solid var(--border);
    font-size: 12px;
  }
  .score-table td {
    padding: 8px 10px; border-bottom: 1px solid rgba(45,51,66,0.5);
    color: var(--text);
  }
  .score-table tr.highlight td {
    background: rgba(124,140,255,0.06);
    border-bottom-color: var(--primary);
  }
  .score-table tr.highlight td:first-child {
    border-left: 2px solid var(--primary);
  }
  .score-table .score-val { font-weight: 600; color: var(--text); }
  .score-table .score-total { font-weight: 700; color: var(--primary); font-size: 15px; }

  details.card-panel {
    cursor: pointer; transition: border-color 0.15s;
  }
  details.card-panel[open] { border-color: var(--border-hover); }
  details.card-panel summary {
    font-size: 13px; font-weight: 600; color: var(--text);
    cursor: pointer; list-style: none; display: flex;
    align-items: center; justify-content: space-between;
  }
  details.card-panel summary::-webkit-details-marker { display: none; }
  details.card-panel summary::after {
    content: '+'; font-size: 16px; color: var(--text-dim);
    transition: transform 0.15s;
  }
  details.card-panel[open] summary::after { content: '−'; }
  details.card-panel .detail-body {
    margin-top: 12px; padding-top: 12px;
    border-top: 1px solid var(--border);
    font-size: 13px; line-height: 1.7; color: var(--text-muted);
    white-space: pre-wrap; max-height: 400px; overflow-y: auto;
  }
  details.card-panel .detail-body.pre-wrap { white-space: pre-wrap; }

  .critique-text {
    font-size: 14px; line-height: 1.8; color: var(--text);
    white-space: pre-wrap;
  }

  .weakness-list { list-style: none; }
  .weakness-list li {
    padding: 8px 0; border-bottom: 1px solid rgba(45,51,66,0.4);
    font-size: 13px; color: var(--text-muted);
  }
  .weakness-list li:last-child { border-bottom: none; }
  .weakness-list li strong { color: var(--text); }

  .suggestion-item {
    padding: 8px 12px; margin: 4px 0;
    border-left: 2px solid var(--primary); font-size: 13px;
    color: var(--text-muted); background: rgba(124,140,255,0.04);
    border-radius: 0 var(--radius) var(--radius) 0;
  }

  .error-banner {
    display: none; padding: 10px 14px;
    background: rgba(251,113,133,0.1); border: 1px solid rgba(251,113,133,0.3);
    border-radius: var(--radius); color: var(--danger);
    font-size: 13px; margin-top: 12px;
  }

  .copy-row {
    display: flex; gap: 6px; align-items: flex-start;
  }
  .copy-row .content-area { flex: 1; }

  @media (max-width: 960px) {
    .layout { flex-direction: column; height: auto; }
    .panel-left { width: 100%; min-width: 0; border-right: none; border-bottom: 1px solid var(--border); }
    .panel-right { height: auto; }
    .empty-state { padding: 40px 20px; }
  }

  .toast {
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
    background: var(--bg-card); border: 1px solid var(--border);
    padding: 8px 18px; border-radius: var(--radius);
    font-size: 13px; color: var(--text-muted);
    opacity: 0; transition: opacity 0.25s; pointer-events: none;
    z-index: 100;
  }
  .toast.show { opacity: 1; }
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1>Personalized Prompt Optimizer</h1>
    <div class="sub">个性化提示词优化器</div>
  </div>
  <div class="header-right">
    <span class="badge">v0.1.1</span>
    <span class="badge">Local</span>
    <span class="badge primary">LLM Judge</span>
  </div>
</div>

<div class="layout">
  <!-- LEFT PANEL: INPUT -->
  <div class="panel panel-left" style="position:relative">
    <div class="panel-title">输入节点</div>

    <div class="field">
      <label>原始问题 <small>你想解决什么？</small></label>
      <textarea id="question" class="md" placeholder="例如：我应该继续做 SaaS 项目，还是转去做 AI 工具？"></textarea>
    </div>
    <div class="field">
      <label>用户画像 <small>你的背景、经验、资源</small></label>
      <textarea id="profile" class="sm" placeholder="例如：独立开发者，3 年后端经验，现金流有限，不喜欢重运营"></textarea>
    </div>
    <div class="field">
      <label>回答偏好 <small>希望侧重什么方向？</small></label>
      <textarea id="preferences" class="sm" placeholder="例如：希望答案直接、具体、偏商业可行性分析"></textarea>
    </div>
    <div class="field">
      <label>排除项 <small>不希望看到什么？</small></label>
      <textarea id="exclusions" class="sm" placeholder="例如：不要空泛鸡汤，不要只说看兴趣，不要宏大战略"></textarea>
    </div>
    <div class="field">
      <label>回答风格 <small>希望的语气和调性</small></label>
      <textarea id="style" class="sm" placeholder="例如：冷静、理性、批判性、可执行"></textarea>
    </div>

    <div class="actions">
      <button class="btn btn-primary" id="submitBtn" onclick="submitOptimize()">开始优化</button>
      <button class="btn btn-secondary" onclick="fillSample()">填入示例</button>
      <button class="btn btn-clear" onclick="clearInputs()" title="清空输入">✕</button>
    </div>

    <div class="error-banner" id="errorMsg"></div>

    <div class="loading-overlay" id="loading">
      <div class="spinner"></div>
      <div class="loading-text">正在生成候选提示词、回答和评分...</div>
    </div>
  </div>

  <!-- RIGHT PANEL: RESULTS -->
  <div class="panel panel-right">
    <div class="panel-title">优化结果</div>

    <!-- Empty state -->
    <div class="empty-state" id="emptyState">
      <div class="icon">◈</div>
      <h3>等待输入问题并启动优化</h3>
      <p>系统会生成 3 个不同策略的候选提示词，分别调用 LLM 生成回答，并通过 LLM Judge 多维评分选出最佳版本。</p>
    </div>

    <!-- Result area -->
    <div class="result-area" id="resultArea">

      <!-- BEST -->
      <div class="best-card" id="bestSection">
        <div class="best-label" id="bestLabel">—</div>
        <div class="best-score"><span id="bestScoreNum">0.0</span> <small>/ 10</small></div>
        <div style="display:flex;gap:6px;margin-bottom:6px">
          <button class="btn-ghost" onclick="copyText('bestAnswer')">复制回答</button>
          <button class="btn-ghost" onclick="copyText('bestPromptPreview')">复制提示词</button>
        </div>
        <div class="best-content" id="bestAnswer"></div>
        <div class="best-prompt-preview" id="bestPromptPreview"></div>
      </div>

      <!-- SCORES -->
      <div class="card-panel">
        <div class="section-header"><span class="section-title">评分对比</span></div>
        <div style="overflow-x:auto">
          <table class="score-table" id="scoreTable">
            <thead>
              <tr><th>候选</th><th>相关性</th><th>个性化</th><th>具体性</th><th>可执行</th><th>非模板</th><th>遵守约束</th><th>总分</th></tr>
            </thead>
            <tbody id="scoreBody"></tbody>
          </table>
        </div>
        <div style="margin-top:8px;font-size:12px;color:var(--text-dim);line-height:1.6" id="comparisonSummary"></div>
      </div>

      <!-- PROMPT CANDIDATES -->
      <div class="section">
        <div class="section-header"><span class="section-title">候选提示词</span></div>
        <details class="card-panel" id="promptA">
          <summary>候选 A：具体执行型</summary>
          <div class="detail-body pre-wrap" id="promptAContent"></div>
        </details>
        <details class="card-panel" id="promptB">
          <summary>候选 B：反模板批判型</summary>
          <div class="detail-body pre-wrap" id="promptBContent"></div>
        </details>
        <details class="card-panel" id="promptC">
          <summary>候选 C：决策顾问型</summary>
          <div class="detail-body pre-wrap" id="promptCContent"></div>
        </details>
      </div>

      <!-- ANSWERS -->
      <div class="section">
        <div class="section-header"><span class="section-title">三个回答</span></div>
        <details class="card-panel" id="ansA">
          <summary>回答 A：具体执行型</summary>
          <div class="detail-body" id="answerAContent"></div>
        </details>
        <details class="card-panel" id="ansB">
          <summary>回答 B：反模板批判型</summary>
          <div class="detail-body" id="answerBContent"></div>
        </details>
        <details class="card-panel" id="ansC">
          <summary>回答 C：决策顾问型</summary>
          <div class="detail-body" id="answerCContent"></div>
        </details>
      </div>

      <!-- CRITIQUE -->
      <div class="card-panel">
        <div class="section-header"><span class="section-title">批判报告</span></div>
        <div class="critique-text" id="critiqueReport">暂无</div>
      </div>

      <!-- NEXT PROMPT -->
      <div class="card-panel">
        <div class="section-header">
          <span class="section-title">下一轮优化提示词</span>
          <button class="btn-ghost" onclick="copyText('nextPromptContent')">复制</button>
        </div>
        <div class="detail-body pre-wrap" id="nextPromptContent" style="margin-top:8px;border-top:1px solid var(--border);padding-top:12px"></div>
      </div>

      <!-- SUGGESTIONS -->
      <div class="card-panel">
        <div class="section-header"><span class="section-title">优化建议</span></div>
        <div id="suggestionsList"></div>
      </div>

    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
function fillSample() {
  document.getElementById('question').value = '我应该继续做现在的 SaaS 项目，还是转去做 AI 工具？';
  document.getElementById('profile').value = '独立开发者，有 3 年后端经验，现金流有限，不喜欢重运营项目';
  document.getElementById('preferences').value = '希望答案直接、具体、偏商业可行性分析';
  document.getElementById('exclusions').value = '不要空泛鸡汤，不要只说看兴趣，不要给过于宏大的战略建议';
  document.getElementById('style').value = '冷静、理性、批判性、可执行';
}

function clearInputs() {
  document.querySelectorAll('.panel-left textarea').forEach(t => t.value = '');
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}

function copyText(id) {
  const el = document.getElementById(id);
  const text = el.textContent || el.innerText;
  navigator.clipboard.writeText(text.trim()).then(() => showToast('已复制')).catch(() => showToast('复制失败'));
}

async function submitOptimize() {
  const btn = document.getElementById('submitBtn');
  const loading = document.getElementById('loading');
  const emptyState = document.getElementById('emptyState');
  const resultArea = document.getElementById('resultArea');
  const errorMsg = document.getElementById('errorMsg');

  const question = document.getElementById('question').value.trim();
  const profile = document.getElementById('profile').value.trim();
  const preferences = document.getElementById('preferences').value.trim();
  const exclusions = document.getElementById('exclusions').value.trim();
  const style = document.getElementById('style').value.trim();

  if (!question || !profile || !preferences || !exclusions || !style) {
    errorMsg.textContent = '所有字段均为必填，请完整填写';
    errorMsg.style.display = 'block';
    return;
  }

  errorMsg.style.display = 'none';
  resultArea.classList.remove('show');
  btn.disabled = true;
  loading.classList.add('show');

  try {
    const res = await fetch('/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        original_question: question,
        user_profile: profile,
        preferences: preferences,
        exclusions: exclusions,
        answer_style: style
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '请求失败');
    }

    const data = await res.json();
    displayResult(data);
  } catch (err) {
    errorMsg.textContent = err.message;
    errorMsg.style.display = 'block';
  } finally {
    btn.disabled = false;
    loading.classList.remove('show');
  }
}

function displayResult(data) {
  const jr = data.judge_result;
  const bestId = jr.best_answer_id;
  const bestLabel = bestId === 'A' ? 'A · 具体执行型' : bestId === 'B' ? 'B · 反模板批判型' : 'C · 决策顾问型';
  const bestScore = jr.scores[bestId]?.total_score || 0;

  document.getElementById('bestLabel').textContent = '最佳策略：' + bestLabel;
  document.getElementById('bestScoreNum').textContent = bestScore.toFixed(1);
  document.getElementById('bestAnswer').textContent = data.best_answer || '';
  document.getElementById('bestPromptPreview').textContent = data.best_prompt || '';

  // Score table
  const tbody = document.getElementById('scoreBody');
  tbody.innerHTML = '';
  const labels = { A: 'A · 执行型', B: 'B · 批判型', C: 'C · 顾问型' };
  for (const id of ['A','B','C']) {
    const sc = jr.scores[id] || {};
    const highlight = id === bestId ? ' class="highlight"' : '';
    tbody.innerHTML += `<tr${highlight}>
      <td><strong>${labels[id]}</strong></td>
      <td class="score-val">${sc.relevance||'-'}</td>
      <td class="score-val">${sc.personalization||'-'}</td>
      <td class="score-val">${sc.specificity||'-'}</td>
      <td class="score-val">${sc.actionability||'-'}</td>
      <td class="score-val">${sc.non_generic||'-'}</td>
      <td class="score-val">${sc.constraint_following||'-'}</td>
      <td class="score-total">${(sc.total_score||0).toFixed(1)}</td>
    </tr>`;
  }

  document.getElementById('comparisonSummary').textContent = jr.comparison_summary || '';

  // Prompt candidates
  document.getElementById('promptAContent').textContent = data.prompt_candidates?.A || '';
  document.getElementById('promptBContent').textContent = data.prompt_candidates?.B || '';
  document.getElementById('promptCContent').textContent = data.prompt_candidates?.C || '';

  // Answers
  document.getElementById('answerAContent').textContent = data.answers?.A || '';
  document.getElementById('answerBContent').textContent = data.answers?.B || '';
  document.getElementById('answerCContent').textContent = data.answers?.C || '';

  // Critique
  document.getElementById('critiqueReport').textContent = data.critique_report || '暂无';

  // Next prompt
  document.getElementById('nextPromptContent').textContent = data.next_iteration_prompt || '暂无';

  // Suggestions
  const sugDiv = document.getElementById('suggestionsList');
  sugDiv.innerHTML = '';
  if (jr.prompt_improvement_suggestions && jr.prompt_improvement_suggestions.length) {
    jr.prompt_improvement_suggestions.forEach(s => {
      sugDiv.innerHTML += '<div class="suggestion-item">' + s + '</div>';
    });
  }

  // Close all details
  document.querySelectorAll('details.card-panel').forEach(d => d.removeAttribute('open'));

  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('resultArea').classList.add('show');
  document.getElementById('resultArea').scrollIntoView({ behavior: 'smooth' });
}
</script>
</body>
</html>"""


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
