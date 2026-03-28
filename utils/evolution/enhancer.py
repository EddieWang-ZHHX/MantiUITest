"""
工具进化增强器 - 分析失败原因并生成改进代码

借鉴 Yunjue-Agent 的 enhance_tools() 核心逻辑：
1. 用 LLM 分析失败原因（Input Error / Execution Failure / Environment Error）
2. 对 Execution Failure，调用 LLM 生成改进代码
3. 验证新代码
"""

import inspect
import json
import ast
from typing import Dict
from loguru import logger


class ToolEnhancer:
    """
    工具进化增强器
    
    职责：
    1. 分析工具失败原因
    2. 生成改进代码
    3. 验证新代码
    """
    
    def __init__(self, llm_client):
        """
        初始化工具进化增强器
        
        Args:
            llm_client: LLM 客户端实例
        """
        self.llm_client = llm_client
    
    def analyze_failure(self, tool) -> dict:
        """
        用 LLM 分析工具失败原因
        
        对应 Yunjue-Agent 的 Tool Analyze 步骤：
        - Input Error: 参数错误（不改进工具）
        - Execution Failure: 工具逻辑问题（需要改进工具）
        - Environment Error: 环境问题（不改进工具）
        
        Args:
            tool: ToolRecord 实例
        
        Returns:
            分析结果字典 {
                'type': 'input_error' | 'execution_failure' | 'environment_error',
                'reason': '具体原因',
                'suggestion': '改进建议',
                'confidence': '高' | '中' | '低'
            }
        """
        prompt = f"""你是一个工具分析专家。分析以下工具失败原因：

工具名称: {tool.name}
工具模块: {tool.module}
工具文件: {tool.file_path}

失败上下文（最近 3 次）:
{json.dumps(tool.failure_contexts[-3:], indent=2, ensure_ascii=False)}

请判断：
1. 失败原因类型（必须是以下之一）：
   - "input_error": 参数错误（不改进工具）
   - "execution_failure": 工具逻辑问题（需要改进工具）
   - "environment_error": 环境问题（不改进工具）
2. 具体原因分析（100 字以内）
3. 改进建议（如果是 execution_failure，提供具体建议）
4. 置信度（高/中/低）

输出 JSON 格式：
{{
    "type": "execution_failure",
    "reason": "...",
    "suggestion": "...",
    "confidence": "高"
}}

只输出 JSON，不要其他内容。"""
        
        try:
            response = self.llm_client.chat(prompt)
            
            # 提取 JSON
            json_str = self._extract_json(response)
            analysis = json.loads(json_str)
            
            logger.info(f"失败分析完成: {analysis.get('type', 'Unknown')}")
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            return {
                'type': 'environment_error',
                'reason': 'LLM 响应格式错误',
                'suggestion': '检查 LLM 配置',
                'confidence': '低'
            }
        
        except Exception as e:
            logger.error(f"分析失败: {e}")
            return {
                'type': 'environment_error',
                'reason': f'分析过程异常: {str(e)}',
                'suggestion': '检查 LLM 服务',
                'confidence': '低'
            }
    
    def generate_tool_code(self, tool, analysis: dict) -> str:
        """
        用 LLM 生成新工具代码
        
        对应 Yunjue-Agent 的 Codex 生成工具代码步骤
        
        Args:
            tool: ToolRecord 实例
            analysis: 失败分析结果
        
        Returns:
            改进后的工具代码
        """
        # 读取原始工具代码
        try:
            original_code = self._read_tool_code(tool.file_path, tool.name)
        except Exception as e:
            logger.error(f"读取原始代码失败: {e}")
            return ""
        
        prompt = f"""你是一个 Python 代码专家。基于失败分析，改进以下工具代码：

原始代码:
```python
{original_code}
```

失败分析:
{json.dumps(analysis, indent=2, ensure_ascii=False)}

请生成改进后的完整工具代码，要求：
1. 保持相同的函数签名
2. 保持相同的导入语句
3. 添加详细的错误处理（try-except）
4. 添加日志记录（使用 loguru.logger）
5. 保持代码简洁，不要过度工程化
6. 不要添加新的依赖

输出格式：
```python
# 改进后的代码
...
```

只输出代码，不要其他内容。"""
        
        try:
            response = self.llm_client.chat(prompt)
            new_code = self._extract_code(response)
            
            logger.info(f"生成新代码成功: {len(new_code)} 字符")
            return new_code
            
        except Exception as e:
            logger.error(f"生成代码失败: {e}")
            return ""
    
    def validate_tool(self, code: str) -> bool:
        """
        验证新工具代码
        
        Args:
            code: 工具代码
        
        Returns:
            是否验证通过
        """
        # 1. 语法检查
        try:
            ast.parse(code)
            logger.debug("语法检查通过")
        except SyntaxError as e:
            logger.error(f"语法错误: {e}")
            return False
        
        # 2. 检查必要的函数定义
        # TODO: 更严格的验证
        
        return True
    
    def _read_tool_code(self, file_path: str, tool_name: str) -> str:
        """
        读取工具代码
        
        Args:
            file_path: 文件路径
            tool_name: 工具名称
        
        Returns:
            工具代码
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 如果工具名包含模块名，提取函数名
        if '.' in tool_name:
            func_name = tool_name.split('.')[-1]
        else:
            func_name = tool_name
        
        # 尝试提取函数代码
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    # 获取函数的起始和结束行
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    
                    lines = content.split('\n')
                    func_code = '\n'.join(lines[start_line:end_line])
                    
                    # 提取导入语句
                    import_lines = []
                    for line in lines[:start_line]:
                        if line.strip().startswith('import ') or line.strip().startswith('from '):
                            import_lines.append(line)
                    
                    # 组合导入和函数代码
                    full_code = '\n'.join(import_lines) + '\n\n' + func_code
                    return full_code
            
            # 如果找不到函数，返回整个文件
            return content
            
        except Exception as e:
            logger.warning(f"提取函数代码失败: {e}，返回整个文件")
            return content
    
    def _extract_json(self, response: str) -> str:
        """从 LLM 响应中提取 JSON"""
        # 尝试提取 ```json ... ```
        if '```json' in response:
            start = response.index('```json') + len('```json')
            end = response.index('```', start)
            return response[start:end].strip()
        
        # 尝试提取 { ... }
        if '{' in response and '}' in response:
            start = response.index('{')
            end = response.rindex('}') + 1
            return response[start:end]
        
        return response
    
    def _extract_code(self, response: str) -> str:
        """从 LLM 响应中提取代码"""
        # 尝试提取 ```python ... ```
        if '```python' in response:
            start = response.index('```python') + len('```python')
            end = response.index('```', start)
            return response[start:end].strip()
        
        # 尝试提取 ``` ... ```
        if '```' in response:
            start = response.index('```') + len('```')
            end = response.index('```', start)
            return response[start:end].strip()
        
        return response