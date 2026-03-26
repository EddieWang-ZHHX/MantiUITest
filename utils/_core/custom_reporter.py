"""自定义测试报告生成器

生成独立的 HTML 报告，支持：
- 按测试模块分组
- TC-ID + 功能描述显示
- 证据内嵌（截图可点击放大）
- 耗时统计
- 深色专业主题
"""
import json
import pathlib
from datetime import datetime
from typing import Dict, List, Any


class TestReport:
    """测试报告生成器"""

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif; background: #0f1117; color: #e0e0e0; font-size: 14px; min-width: 900px; }}

/* Header */
.header {{ background: linear-gradient(135deg, #1a1d27 0%, #161922 100%); border-bottom: 1px solid #2a2d3a; padding: 24px 32px; }}
.header-title {{ font-size: 22px; font-weight: 600; color: #ffffff; margin-bottom: 6px; }}
.header-meta {{ font-size: 12px; color: #6b7280; }}
.header-meta span {{ margin-right: 20px; }}

/* Summary Bar */
.summary-bar {{ display: flex; gap: 24px; padding: 20px 32px; background: #1a1d27; border-bottom: 1px solid #2a2d3a; }}
.stat-card {{ background: #242838; border-radius: 10px; padding: 16px 24px; flex: 1; text-align: center; border: 1px solid #2a2d3a; }}
.stat-card.passed {{ border-color: #22c55e; }}
.stat-card.failed {{ border-color: #ef4444; }}
.stat-number {{ font-size: 32px; font-weight: 700; }}
.stat-number.green {{ color: #22c55e; }}
.stat-number.red {{ color: #ef4444; }}
.stat-number.gray {{ color: #9ca3af; }}
.stat-label {{ font-size: 12px; color: #9ca3af; margin-top: 4px; }}

/* Module Cards */
.content {{ padding: 24px 32px; }}
.module-card {{ background: #1a1d27; border: 1px solid #2a2d3a; border-radius: 12px; margin-bottom: 20px; overflow: hidden; }}
.module-header {{ padding: 14px 20px; background: #242838; display: flex; align-items: center; justify-content: space-between; cursor: pointer; user-select: none; }}
.module-title {{ display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 600; color: #ffffff; }}
.module-title .icon {{ font-size: 18px; }}
.module-badge {{ display: flex; gap: 8px; align-items: center; }}
.badge {{ padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
.badge.pass {{ background: #22c55e22; color: #22c55e; border: 1px solid #22c55e44; }}
.badge.fail {{ background: #ef444422; color: #ef4444; border: 1px solid #ef444444; }}
.badge.skip {{ background: #f59e0b22; color: #f59e0b; border: 1px solid #f59e0b44; }}
.badge.total {{ background: #3b82f622; color: #60a5fa; border: 1px solid #3b82f644; }}
.module-body {{ display: none; }}
.module-body.open {{ display: block; }}
.expand-icon {{ color: #6b7280; transition: transform 0.2s; font-size: 12px; }}
.module-header.open .expand-icon {{ transform: rotate(90deg); }}

/* Test Rows */
.test-row {{ display: grid; grid-template-columns: 120px 1fr 80px 80px 100px; align-items: center; padding: 10px 20px; border-bottom: 1px solid #242838; gap: 12px; }}
.test-row:last-child {{ border-bottom: none; }}
.test-row:hover {{ background: #242838; }}
.test-row.header {{ background: #0f1117; padding: 8px 20px; font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }}

.tc-id {{ font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; color: #60a5fa; background: #3b82f611; padding: 3px 8px; border-radius: 4px; border: 1px solid #3b82f622; }}
.tc-id.none {{ color: #6b7280; background: #242838; border-color: #2a2d3a; }}
.test-name {{ color: #d1d5db; font-size: 13px; }}
.result {{ font-size: 13px; font-weight: 600; text-align: center; }}
.result.pass {{ color: #22c55e; }}
.result.fail {{ color: #ef4444; }}
.result.error {{ color: #f59e0b; }}
.duration {{ font-size: 12px; color: #9ca3af; text-align: right; font-family: 'Consolas', monospace; }}
.evidence-btn {{ text-align: center; }}
.evidence-btn button {{ background: #3b82f622; border: 1px solid #3b82f644; color: #60a5fa; padding: 3px 10px; border-radius: 4px; font-size: 11px; cursor: pointer; }}
.evidence-btn button:hover {{ background: #3b82f644; }}

/* Evidence Modal */
.modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 9999; justify-content: center; align-items: center; flex-direction: column; }}
.modal.open {{ display: flex; }}
.modal img {{ max-width: 90%; max-height: 85vh; border-radius: 8px; border: 2px solid #3b82f6; }}
.modal-close {{ color: #fff; margin-top: 16px; padding: 8px 24px; background: #3b82f6; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }}
.modal-close:hover {{ background: #2563eb; }}
.modal-label {{ color: #9ca3af; font-size: 12px; margin-bottom: 8px; }}

/* Error Detail */
.error-detail {{ display: none; padding: 12px 20px; background: #ef444411; border-top: 1px solid #ef444422; font-family: 'Consolas', monospace; font-size: 12px; color: #fca5a5; white-space: pre-wrap; word-break: break-all; }}
.error-detail.open {{ display: block; }}
.expand-btn {{ font-size: 11px; color: #6b7280; cursor: pointer; background: none; border: none; padding: 2px 6px; }}
.expand-btn:hover {{ color: #9ca3af; }}

/* Duration Bar */
.duration-bar-wrap {{ width: 60px; height: 4px; background: #2a2d3a; border-radius: 2px; }}
.duration-bar {{ height: 4px; border-radius: 2px; background: #60a5fa; }}

/* Environment */
.env-section {{ margin-top: 24px; background: #1a1d27; border: 1px solid #2a2d3a; border-radius: 12px; padding: 20px; }}
.env-section h3 {{ font-size: 13px; color: #9ca3af; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
.env-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px; }}
.env-item {{ background: #242838; border-radius: 6px; padding: 8px 12px; font-size: 12px; }}
.env-item .key {{ color: #6b7280; }}
.env-item .value {{ color: #e0e0e0; font-family: monospace; margin-left: 6px; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-title">{header_title}</div>
  <div class="header-meta">
    <span>执行时间: {exec_time}</span>
    <span>总耗时: {total_duration}</span>
    <span>环境: {env_name}</span>
  </div>
</div>

<div class="summary-bar">
  <div class="stat-card">
    <div class="stat-number green">{pass_count}</div>
    <div class="stat-label">通过</div>
  </div>
  <div class="stat-card">
    <div class="stat-number red">{fail_count}</div>
    <div class="stat-label">失败</div>
  </div>
  <div class="stat-card">
    <div class="stat-number gray">{total_count}</div>
    <div class="stat-label">总计</div>
  </div>
  <div class="stat-card">
    <div class="stat-number {pass_rate_color}">{pass_rate}</div>
    <div class="stat-label">通过率</div>
  </div>
  <div class="stat-card">
    <div class="stat-number gray">{total_duration_stat}</div>
    <div class="stat-label">总耗时</div>
  </div>
</div>

<div class="content">
{module_cards}
</div>

<div class="content" style="padding-top: 0;">
  <div class="env-section">
    <h3>环境信息</h3>
    <div class="env-grid">{env_items}</div>
  </div>
</div>

<!-- Evidence Modal -->
<div class="modal" id="evidenceModal" onclick="closeModal(event)">
  <div class="modal-label" id="modalLabel"></div>
  <img id="modalImg" src="" alt="evidence" style="display:none">
  <video id="modalVideo" controls style="display:none;max-width:90%;max-height:85vh;border-radius:8px;border:2px solid #3b82f6;"></video>
  <button class="modal-close" onclick="closeModal()">关闭</button>
</div>

<script>
function toggleModule(el) {{
  el.classList.toggle('open');
  el.nextElementSibling.classList.toggle('open');
}}
function toggleError(el) {{
  el.previousElementSibling.classList.toggle('open');
}}
function openModalImg(dataUri, label) {{
  const modal = document.getElementById('evidenceModal');
  const img = document.getElementById('modalImg');
  const video = document.getElementById('modalVideo');
  document.getElementById('modalLabel').textContent = label + ' (截图)';
  img.src = dataUri;
  img.style.display = 'block';
  video.style.display = 'none';
  video.pause();
  modal.classList.add('open');
}}
function openModalVideo(dataUri, label) {{
  const modal = document.getElementById('evidenceModal');
  const img = document.getElementById('modalImg');
  const video = document.getElementById('modalVideo');
  document.getElementById('modalLabel').textContent = label + ' (视频)';
  video.src = dataUri;
  video.style.display = 'block';
  img.style.display = 'none';
  modal.classList.add('open');
}}
function closeModal(event) {{
  if (!event || event.target === document.getElementById('evidenceModal') || event.target.classList.contains('modal-close')) {{
    const modal = document.getElementById('evidenceModal');
    const video = document.getElementById('modalVideo');
    modal.classList.remove('open');
    video.pause();
  }}
}}
// Auto-expand failed modules
document.querySelectorAll('.result.fail').forEach(el => {{
  const card = el.closest('.module-card');
  if (card) {{
    card.querySelector('.module-header').classList.add('open');
    card.querySelector('.module-body').classList.add('open');
  }}
}});
</script>
</body>
</html>"""

    def __init__(self):
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.env: Dict[str, Any] = {}
        self.summary: Dict[str, Any] = {}
        self.report_path: pathlib.Path = None

    def set_summary(self, total: int, passed: int, failed: int, duration: str):
        self.summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "duration": duration
        }

    def set_env(self, env: Dict[str, Any]):
        self.env = env

    def add_module(self, module_name: str, icon: str = "📋"):
        if module_name not in self.modules:
            self.modules[module_name] = {
                "icon": icon,
                "tests": []
            }

    def add_test(self, module_name: str, tc_id: str, name: str, result: str,
                 duration: str, error_msg: str = "",
                 screenshot_b64: str = "", video_b64: str = "",
                 file_path: str = ""):
        self.add_module(module_name)
        self.modules[module_name]["tests"].append({
            "tc_id": tc_id,
            "name": name,
            "result": result,
            "duration": duration,
            "error_msg": error_msg,
            "screenshot_b64": screenshot_b64,
            "video_b64": video_b64,
            "file_path": file_path
        })

    def generate(self, output_path: pathlib.Path):
        self.report_path = output_path

        # Calculate pass rate
        total = self.summary.get("total", 0)
        passed = self.summary.get("passed", 0)
        failed = self.summary.get("failed", 0)
        pass_rate = f"{(passed/total*100):.1f}%" if total > 0 else "0%"
        pass_rate_color = "green" if pass_rate >= "80%" else ("red" if pass_rate < "50%" else "gray")

        # Format duration
        total_dur = self.summary.get("duration", "0s")
        try:
            dur_float = float(total_dur.replace("s", ""))
            total_dur_fmt = f"{dur_float:.2f}s" if dur_float < 60 else f"{dur_float/60:.1f}m"
        except:
            total_dur_fmt = total_dur

        # Build module cards
        module_cards = ""
        for mod_name, mod_data in self.modules.items():
            tests = mod_data["tests"]
            pass_count = sum(1 for t in tests if t["result"] == "passed")
            fail_count = sum(1 for t in tests if t["result"] in ("failed", "error"))
            total_count = len(tests)

            # Build test rows
            rows = self._build_test_rows(tests)

            badge_html = ""
            if pass_count > 0:
                badge_html += f'<span class="badge pass">✅ {pass_count}</span>'
            if fail_count > 0:
                badge_html += f'<span class="badge fail">❌ {fail_count}</span>'
            badge_html += f'<span class="badge total">{total_count} 个</span>'

            module_cards += f"""
<div class="module-card">
  <div class="module-header open" onclick="toggleModule(this)">
    <div class="module-title">
      <span class="icon">{mod_data['icon']}</span>
      <span>{mod_name}</span>
    </div>
    <div class="module-badge">
      {badge_html}
      <span class="expand-icon">▶</span>
    </div>
  </div>
  <div class="module-body open">
    <div class="test-row header">
      <div>用例ID</div>
      <div>测试内容</div>
      <div>结果</div>
      <div>耗时</div>
      <div>证据</div>
    </div>
    {rows}
  </div>
</div>"""

        # Build env items
        env_items = ""
        for key, val in self.env.items():
            if isinstance(val, dict):
                for k2, v2 in val.items():
                    env_items += f'<div class="env-item"><span class="key">{key}.{k2}</span><span class="value">{v2}</span></div>'
            else:
                env_items += f'<div class="env-item"><span class="key">{key}</span><span class="value">{val}</span></div>'

        html = self.HTML_TEMPLATE.format(
            title=f"测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            header_title="教师数据中心 UI 自动化测试报告",
            exec_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_duration=total_dur_fmt,
            env_name="http://172.16.34.104:7777/dataapp",
            pass_count=passed,
            fail_count=failed,
            total_count=total,
            pass_rate=pass_rate,
            pass_rate_color=pass_rate_color,
            total_duration_stat=total_dur_fmt,
            module_cards=module_cards,
            env_items=env_items
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        return str(output_path)

    def _build_test_rows(self, tests: List[Dict[str, Any]]) -> str:
        rows = ""
        for t in tests:
            tc = t.get("tc_id", "")
            tc_class = "none" if not tc or tc.startswith("test_") else ""
            tc_html = f'<span class="tc-id {tc_class}">{tc or "—"}</span>'

            result_class = "pass" if t["result"] == "passed" else ("fail" if t["result"] == "failed" else "error")
            result_icon = "✅ PASS" if t["result"] == "passed" else ("❌ FAIL" if t["result"] == "failed" else "⚠️ ERROR")

            dur = t.get("duration", "")
            dur_html = f'<span>{dur}</span>'

            # Evidence: 优先用 base64 内嵌，其次用文件路径
            screenshot_b64 = t.get("screenshot_b64", "")
            video_b64 = t.get("video_b64", "")

            if screenshot_b64:
                ev_html = (
                    f'<div class="evidence-btn">'
                    f'<button onclick="openModalImg(\'data:image/png;base64,{screenshot_b64}\', \'{t["name"]}\')">📷 截图</button>'
                    f'</div>'
                )
            elif video_b64:
                ev_html = (
                    f'<div class="evidence-btn">'
                    f'<button onclick="openModalVideo(\'data:video/webm;base64,{video_b64}\', \'{t["name"]}\')">🎬 视频</button>'
                    f'</div>'
                )
            else:
                ev_html = '<span style="color:#4b5563;font-size:11px;">—</span>'

            rows += f"""
    <div class="test-row">
      {tc_html}
      <div class="test-name">{t['name']}</div>
      <div class="result {result_class}">{result_icon}</div>
      <div class="duration">{dur_html}</div>
      {ev_html}
    </div>"""
            if t.get("error_msg"):
                err = t["error_msg"].replace("`", "\\`").replace("\n", "\\n").replace("'", "\\'")
                rows += f"""
    <div class="error-detail">{err}</div>"""

        return rows
