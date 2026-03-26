"""配置设置"""
import yaml
from pathlib import Path
from typing import Any


class Settings:
    """配置管理类"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.yml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载 YAML 配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在：{self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def browser(self) -> dict:
        return self.get('browser', {})
    
    @property
    def test(self) -> dict:
        return self.get('test', {})
    
    @property
    def report(self) -> dict:
        return self.get('report', {})
    
    @property
    def log(self) -> dict:
        return self.get('log', {})
