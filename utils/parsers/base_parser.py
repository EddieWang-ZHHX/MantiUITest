from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class ElementInfo:
    tag: str
    attrs: Dict[str, Any]
    selector: str
    selector_candidates: List[str]
    stability: str
    group: str
    text: str = ""
    element_id: str = ""

    def __post_init__(self):
        if not self.element_id:
            import hashlib

            key = f"{self.tag}_{self.attrs.get('placeholder', '')}_{self.text}"
            self.element_id = "el_" + hashlib.md5(key.encode()).hexdigest()[:8]


@dataclass
class FormInfo:
    name: str
    element_ids: List[str]


@dataclass
class PageSnapshot:
    url: str
    title: str
    explored_at: str
    parser: str
    elements: List[ElementInfo] = field(default_factory=list)
    forms: List[FormInfo] = field(default_factory=list)
    buttons: List[ElementInfo] = field(default_factory=list)
    links: List[ElementInfo] = field(default_factory=list)
    inputs: List[ElementInfo] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "explored_at": self.explored_at,
            "parser": self.parser,
            "elements": [asdict(e) for e in self.elements],
            "forms": [asdict(f) for f in self.forms],
            "buttons": [asdict(b) for b in self.buttons],
            "links": [asdict(l) for l in self.links],
            "inputs": [asdict(i) for i in self.inputs],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PageSnapshot":
        data = data.copy()
        data["elements"] = [ElementInfo(**e) for e in data.get("elements", [])]
        data["forms"] = [FormInfo(**f) for f in data.get("forms", [])]
        data["buttons"] = [ElementInfo(**b) for b in data.get("buttons", [])]
        data["links"] = [ElementInfo(**l) for l in data.get("links", [])]
        data["inputs"] = [ElementInfo(**i) for i in data.get("inputs", [])]
        return cls(**data)


class BaseParser(ABC):
    STABILITY_HIGH = "high"
    STABILITY_MEDIUM = "medium"
    STABILITY_LOW = "low"

    GROUP_INPUTS = "inputs"
    GROUP_BUTTONS = "buttons"
    GROUP_LINKS = "links"
    GROUP_SELECTS = "selects"
    GROUP_TEXTAREA = "textarea"

    @abstractmethod
    def parse(self, source: str, **kwargs) -> PageSnapshot:
        pass

    def _generate_selectors(
        self, tag: str, attrs: Dict[str, Any], text: str = ""
    ) -> List[str]:
        selectors = []

        placeholder = attrs.get("placeholder", "")
        if placeholder:
            selectors.append(f"{tag}[placeholder*='{placeholder}']")

        name = attrs.get("name", "")
        if name:
            selectors.append(f"{tag}[name='{name}']")

        id_val = attrs.get("id", "")
        if id_val:
            selectors.append(f"{tag}#{id_val}")

        aria_label = attrs.get("aria-label", "")
        if aria_label:
            selectors.append(f"{tag}[aria-label*='{aria_label}']")

        type_val = attrs.get("type", "")
        if type_val and tag == "input":
            selectors.append(f"input[type='{type_val}']")

        if text:
            if tag == "button":
                selectors.append(f"button:has-text('{text}')")
            elif tag == "a":
                selectors.append(f"a:has-text('{text}')")

        return selectors

    def _assess_stability(self, selector: str) -> str:
        if "[placeholder" in selector or "[aria-label" in selector:
            return self.STABILITY_HIGH
        elif "[name" in selector or "[id=" in selector:
            return self.STABILITY_MEDIUM
        elif ":nth-of-type" in selector or ":nth-child" in selector:
            return self.STABILITY_LOW
        return self.STABILITY_MEDIUM

    def _get_group(self, tag: str) -> str:
        if tag == "input":
            return self.GROUP_INPUTS
        elif tag == "button":
            return self.GROUP_BUTTONS
        elif tag == "a":
            return self.GROUP_LINKS
        elif tag == "select":
            return self.GROUP_SELECTS
        elif tag == "textarea":
            return self.GROUP_TEXTAREA
        return tag

    def _group_elements(self, elements: List[ElementInfo]) -> tuple:
        inputs = [e for e in elements if e.group == self.GROUP_INPUTS]
        buttons = [e for e in elements if e.group == self.GROUP_BUTTONS]
        links = [e for e in elements if e.group == self.GROUP_LINKS]

        forms = self._detect_forms(elements)

        return inputs, buttons, links, forms

    def _detect_forms(self, elements: List[ElementInfo]) -> List[FormInfo]:
        forms = []
        form_count = 0

        nearby_inputs = [e for e in elements if e.group == self.GROUP_INPUTS]
        nearby_buttons = [e for e in elements if e.group == self.GROUP_BUTTONS]

        if nearby_inputs:
            form_count += 1
            forms.append(
                FormInfo(
                    name=f"form_{form_count}",
                    element_ids=[e.element_id for e in nearby_inputs + nearby_buttons],
                )
            )

        return forms
