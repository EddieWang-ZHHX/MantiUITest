"""
工具进化机制单元测试

测试目标：
1. ToolRegistry 工具注册和状态管理
2. evolution_monitor 装饰器功能
3. LLMClient 调用（可选，需要配置）
4. ToolEnhancer 分析和代码生成（可选，需要 LLM）
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import json

from utils.evolution.registry import ToolRegistry, ToolRecord
from utils.evolution.decorator import evolution_monitor
from utils.evolution.llm_client import LLMClient
from utils.evolution.enhancer import ToolEnhancer


class TestToolRegistry:
    """测试 ToolRegistry 核心功能"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        assert registry1 is registry2

    def test_register_tool(self):
        """测试工具注册"""
        registry = ToolRegistry()
        registry.register("test_tool", "test_module", "test_path.py")

        assert "test_tool" in registry.tools
        assert registry.tools["test_tool"].name == "test_tool"
        assert registry.tools["test_tool"].module == "test_module"
        assert registry.tools["test_tool"].status == "untested"

    def test_record_execution_success(self):
        """测试记录成功执行"""
        registry = ToolRegistry()
        registry.register("test_tool", "test_module", "test_path.py")

        registry.record_execution("test_tool", True, {"args": "test"})

        tool = registry.tools["test_tool"]
        assert tool.attempts == 1
        assert tool.successes == 1
        assert tool.failures == 0
        assert tool.status == "verified"

    def test_record_execution_failure(self):
        """测试记录失败执行"""
        registry = ToolRegistry()
        registry.register("test_tool", "test_module", "test_path.py")

        registry.record_execution("test_tool", False, {"error": "test error"})

        tool = registry.tools["test_tool"]
        assert tool.attempts == 1
        assert tool.successes == 0
        assert tool.failures == 1
        assert tool.status == "failed"
        assert len(tool.failure_contexts) == 1

    def test_failure_threshold_triggers_evolution(self):
        """测试连续失败触发进化"""
        registry = ToolRegistry()
        registry.register("test_tool", "test_module", "test_path.py")

        # Mock LLM client to avoid actual API calls
        with patch.object(registry, '_trigger_evolution') as mock_evolution:
            # 连续失败 3 次
            for i in range(3):
                registry.record_execution("test_tool", False, {"error": f"error {i}"})

            # 验证进化被触发
            assert mock_evolution.called
            assert registry.tools["test_tool"].status == "quarantined"


class TestEvolutionDecorator:
    """测试 evolution_monitor 装饰器"""

    def test_decorator_registers_tool(self):
        """测试装饰器自动注册工具"""
        @evolution_monitor("test_function")
        def test_function(x: int) -> int:
            return x * 2

        # 调用函数触发注册
        result = test_function(5)

        # 验证注册
        registry = ToolRegistry()
        assert "test_function" in registry.tools

    def test_decorator_records_success(self):
        """测试装饰器记录成功"""
        @evolution_monitor("success_function")
        def success_function(x: int) -> int:
            return x * 2

        result = success_function(5)

        registry = ToolRegistry()
        tool = registry.tools["success_function"]
        assert tool.successes == 1
        assert tool.failures == 0

    def test_decorator_records_failure(self):
        """测试装饰器记录失败"""
        @evolution_monitor("failure_function")
        def failure_function(x: int) -> int:
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failure_function(5)

        registry = ToolRegistry()
        tool = registry.tools["failure_function"]
        assert tool.successes == 0
        assert tool.failures == 1
        assert len(tool.failure_contexts) == 1
        assert "ValueError" in tool.failure_contexts[0]["error_type"]


class TestLLMClient:
    """测试 LLM 客户端"""

    def test_llm_client_initialization(self):
        """测试 LLM 客户端初始化"""
        config = {
            "api_base": "http://localhost:11434/v1",
            "api_key": "",
            "model": "qwen2.5:14b",
            "timeout": 60,
            "max_tokens": 4096,
            "temperature": 0.7
        }

        client = LLMClient(config)

        assert client.api_base == "http://localhost:11434/v1"
        assert client.model == "qwen2.5:14b"
        assert client.timeout == 60

    @pytest.mark.skip(reason="需要实际 LLM 服务")
    def test_llm_client_chat(self):
        """测试 LLM 调用（需要实际服务）"""
        config = {
            "api_base": "http://localhost:11434/v1",
            "model": "qwen2.5:14b"
        }

        client = LLMClient(config)
        response = client.chat("Hello, how are you?")

        assert isinstance(response, str)
        assert len(response) > 0


class TestToolEnhancer:
    """测试工具进化增强器"""

    def test_enhancer_initialization(self):
        """测试增强器初始化"""
        mock_llm = Mock()
        enhancer = ToolEnhancer(mock_llm)

        assert enhancer.llm_client is mock_llm

    def test_analyze_failure(self):
        """测试失败分析"""
        mock_llm = Mock()
        mock_llm.chat.return_value = json.dumps({
            "type": "execution_failure",
            "reason": "Test reason",
            "suggestion": "Test suggestion",
            "confidence": "高"
        })

        enhancer = ToolEnhancer(mock_llm)

        # 创建测试工具记录
        tool = ToolRecord(
            name="test_tool",
            module="test_module",
            file_path="test_path.py",
            failure_contexts=[{"error": "test error"}]
        )

        analysis = enhancer.analyze_failure(tool)

        assert analysis["type"] == "execution_failure"
        assert analysis["reason"] == "Test reason"

    def test_validate_tool_code(self):
        """测试代码验证"""
        mock_llm = Mock()
        enhancer = ToolEnhancer(mock_llm)

        # 有效代码
        valid_code = "def test(): return 1"
        assert enhancer.validate_tool(valid_code) is True

        # 无效代码
        invalid_code = "def test( return 1"
        assert enhancer.validate_tool(invalid_code) is False


class TestToolScanner:
    """测试工具扫描器"""

    def test_scanner_initialization(self):
        """测试扫描器初始化"""
        from utils.evolution.scanner import ToolScanner

        scanner = ToolScanner()
        assert scanner.registry is not None


# 集成测试
class TestEvolutionIntegration:
    """集成测试 - 完整进化流程"""

    @pytest.mark.skip(reason="需要完整配置")
    def test_full_evolution_workflow(self):
        """测试完整进化流程（需要配置）"""
        # 1. 注册工具
        # 2. 模拟失败
        # 3. 触发进化
        # 4. 验证结果
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])