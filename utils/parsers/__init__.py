from utils.parsers.base_parser import BaseParser, PageSnapshot, ElementInfo, FormInfo
from pages.base_page import SelectorRecord

_parsers = {}


class ParserFactory:
    _parsers = {}

    @classmethod
    def register(cls, name: str, parser_class):
        cls._parsers[name] = parser_class

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseParser:
        if name not in cls._parsers:
            raise ValueError(
                f"Unknown parser: {name}. Available: {list(cls._parsers.keys())}"
            )
        return cls._parsers[name](**kwargs)

    @classmethod
    def list_parsers(cls) -> list:
        return list(cls._parsers.keys())


from utils.parsers.playwright_parser import PlaywrightParser

ParserFactory.register("playwright", PlaywrightParser)


__all__ = [
    "BaseParser",
    "PageSnapshot",
    "ElementInfo",
    "FormInfo",
    "SelectorRecord",
    "ParserFactory",
]
