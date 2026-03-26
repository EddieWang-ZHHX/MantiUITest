"""
自定义测试报告生成器
生成包含可点击证据链接的 HTML 报告
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from jinja2 import Template


class EvidenceReportGenerator:
    """证据报告生成器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.reports_dir = self.project_root / "reports"
        self.evidence_base = self.reports_dir / "evidence"
        self.pytest_report = self.reports_dir / "report.html"
        
    def get_all_evidence_dirs(self) -> List[Dict[str, Any]]:
        """扫描所有证据目录"""
        evidence_dirs = []
        
        if not self.evidence_base.exists():
            return evidence_dirs
            
        for evidence_dir in sorted(self.evidence_base.iterdir()):
            if evidence_dir.is_dir():
                test_name = evidence_dir.name
                files = list(evidence_dir.iterdir())
                
                # 分类文件
                screenshot = None
                video = None
                trace = None
                page_html = None
                console_log = None
                
                for f in files:
                    if f.suffix == '.png' or 'screenshot' in f.name.lower():
                        screenshot = f
                    elif f.suffix == '.webm' or 'video' in f.name.lower():
                        video = f
                    elif f.suffix == '.zip' or 'trace' in f.name.lower():
                        trace = f
                    elif f.name == 'page.html':
                        page_html = f
                    elif 'console' in f.name.lower() and f.suffix == '.log':
                        console_log = f
                
                evidence_dirs.append({
                    'test_name': test_name,
                    'path': evidence_dir,
                    'screenshot': screenshot,
                    'video': video,
                    'trace': trace,
                    'page_html': page_html,
                    'console_log': console_log,
                    'file_count': len(files),
                    'has_content': len(files) > 0
                })
        
        return evidence_dirs
    
    def file_to_url(self, file_path: Path) -> str:
        """将文件路径转换为 file:// URL"""
        # 转换反斜杠为正斜杠
        path_str = str(file_path.resolve()).replace('\\', '/')
        return f"file:///{path_str}"
    
    def generate_html_report(self) -> str:
        """生成 HTML 报告"""
        evidence_dirs = self.get_all_evidence_dirs()
        
        # 读取 pytest-html 报告（如果存在）
        pytest_report_content = ""
        if self.pytest_report.exists():
            with open(self.pytest_report, 'r', encoding='utf-8') as f:
                pytest_report_content = f.read()
        
        template = Template(TEMPLATE_HTML)
        
        html = template.render(
            title="测试证据报告",
            generated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            evidence_count=len(evidence_dirs),
            evidence_dirs=evidence_dirs,
            file_to_url=self.file_to_url,
            pytest_report_exists=self.pytest_report.exists(),
            project_root=str(self.project_root)
        )
        
        return html
    
    def save_report(self, output_path: str = None) -> str:
        """保存报告到文件"""
        if output_path is None:
            output_path = self.reports_dir / "evidence_report.html"
        else:
            output_path = Path(output_path)
        
        html = self.generate_html_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(output_path)


TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #2d3748;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header .meta {
            color: #718096;
            font-size: 14px;
        }
        
        .stats {
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            border-radius: 12px;
            text-align: center;
        }
        
        .stat-card .number {
            font-size: 36px;
            font-weight: bold;
        }
        
        .stat-card .label {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .pytest-link {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 24px;
            background: #48bb78;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .pytest-link:hover {
            background: #38a169;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(72, 187, 120, 0.4);
        }
        
        .evidence-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }
        
        .evidence-card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .evidence-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }
        
        .evidence-card h3 {
            color: #2d3748;
            font-size: 18px;
            margin-bottom: 16px;
            word-break: break-all;
        }
        
        .evidence-links {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .evidence-link {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            background: #f7fafc;
            border-radius: 8px;
            text-decoration: none;
            color: #4a5568;
            transition: all 0.2s ease;
            border: 1px solid #e2e8f0;
        }
        
        .evidence-link:hover {
            background: #edf2f7;
            border-color: #667eea;
            color: #667eea;
        }
        
        .evidence-link .icon {
            font-size: 20px;
            margin-right: 12px;
            width: 28px;
            text-align: center;
        }
        
        .evidence-link .label {
            flex: 1;
            font-weight: 500;
        }
        
        .evidence-link .arrow {
            opacity: 0;
            transition: opacity 0.2s ease;
        }
        
        .evidence-link:hover .arrow {
            opacity: 1;
        }
        
        .no-evidence {
            text-align: center;
            padding: 60px;
            background: white;
            border-radius: 16px;
            color: #718096;
        }
        
        .no-evidence .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            color: rgba(255,255,255,0.8);
            font-size: 14px;
        }
        
        .btn-group {
            display: flex;
            gap: 12px;
            margin-top: 16px;
        }
        
        .btn {
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a67d8;
        }
        
        .btn-secondary {
            background: #e2e8f0;
            color: #4a5568;
        }
        
        .btn-secondary:hover {
            background: #cbd5e0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 {{ title }}</h1>
            <div class="meta">
                生成时间: {{ generated_time }} | 项目路径: {{ project_root }}
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="number">{{ evidence_count }}</div>
                    <div class="label">测试证据集</div>
                </div>
            </div>
            
            <div class="btn-group">
                {% if pytest_report_exists %}
                <a href="report.html" class="pytest-link">📊 查看 Pytest-HTML 报告</a>
                {% endif %}
                <button onclick="location.reload()" class="btn btn-secondary">🔄 刷新报告</button>
            </div>
        </div>
        
        {% if evidence_dirs %}
        <div class="evidence-grid">
            {% for evidence in evidence_dirs %}
            <div class="evidence-card">
                <h3>📁 {{ evidence.test_name }}</h3>
                
                <div class="evidence-links">
                    {% if evidence.screenshot %}
                    <a href="{{ file_to_url(evidence.screenshot) }}" target="_blank" class="evidence-link">
                        <span class="icon">📷</span>
                        <span class="label">截图</span>
                        <span class="arrow">→</span>
                    </a>
                    {% endif %}
                    
                    {% if evidence.video %}
                    <a href="{{ file_to_url(evidence.video) }}" target="_blank" class="evidence-link">
                        <span class="icon">🎬</span>
                        <span class="label">录屏</span>
                        <span class="arrow">→</span>
                    </a>
                    {% endif %}
                    
                    {% if evidence.page_html %}
                    <a href="{{ file_to_url(evidence.page_html) }}" target="_blank" class="evidence-link">
                        <span class="icon">📄</span>
                        <span class="label">页面源码</span>
                        <span class="arrow">→</span>
                    </a>
                    {% endif %}
                    
                    {% if evidence.console_log %}
                    <a href="{{ file_to_url(evidence.console_log) }}" target="_blank" class="evidence-link">
                        <span class="icon">📝</span>
                        <span class="label">控制台日志</span>
                        <span class="arrow">→</span>
                    </a>
                    {% endif %}
                    
                    {% if evidence.trace %}
                    <a href="{{ file_to_url(evidence.trace) }}" target="_blank" class="evidence-link">
                        <span class="icon">🔍</span>
                        <span class="label">Playwright Trace</span>
                        <span class="arrow">→</span>
                    </a>
                    {% endif %}
                    
                    <a href="{{ file_to_url(evidence.path) }}" target="_blank" class="evidence-link" style="background: #edf2f7; border-style: dashed;">
                        <span class="icon">📂</span>
                        <span class="label">打开目录</span>
                        <span class="arrow">→</span>
                    </a>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="no-evidence">
            <div class="icon">📭</div>
            <h2>暂无证据文件</h2>
            <p>运行测试后，证据文件将显示在这里</p>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>由 Manti 测试框架生成 | 报告路径: {{ project_root }}/reports/evidence_report.html</p>
        </div>
    </div>
</body>
</html>
"""


def generate_evidence_report(project_root: str = None) -> str:
    """生成证据报告的便捷函数"""
    generator = EvidenceReportGenerator(project_root)
    return generator.save_report()


if __name__ == "__main__":
    report_path = generate_evidence_report("C:/11_UITest")
    print(f"✅ 证据报告已生成: {report_path}")
