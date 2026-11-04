"""Heuristic LaTeX extraction helpers built on pylatexenc 2.x.

Not a full AST — just enough to pull title, abstract, theorem statements
with labels, sections, and figure paths out of a typical math paper.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field

from pylatexenc.latexwalker import (
    LatexEnvironmentNode,
    LatexGroupNode,
    LatexMacroNode,
    LatexWalker,
)

THEOREM_ENVS = ("theorem", "proposition", "lemma", "corollary")


@dataclass
class TheoremBlock:
    id: str
    env: str
    statement_tex: str
    section_number: str | None = None


@dataclass
class SectionInfo:
    number: str
    title_tex: str
    start_pos: int


@dataclass
class ParsedPaper:
    title_tex: str
    author_tex: str
    date_tex: str
    abstract_tex: str
    theorems: list[TheoremBlock] = field(default_factory=list)
    sections: list[SectionInfo] = field(default_factory=list)
    figures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title_tex": self.title_tex,
            "author_tex": self.author_tex,
            "date_tex": self.date_tex,
            "abstract_tex": self.abstract_tex,
            "theorems": [asdict(t) for t in self.theorems],
            "sections": [asdict(s) for s in self.sections],
            "figures": self.figures,
        }


def _group_to_text(node) -> str:
    """Extract text content from a LatexGroupNode or similar."""
    if node is None:
        return ""
    if isinstance(node, LatexGroupNode):
        inner = "".join(_node_text(n) for n in node.nodelist)
        return inner.strip()
    return _node_text(node).strip()


def _node_text(node) -> str:
    """Return the latex_verbatim representation of a node."""
    if node is None:
        return ""
    try:
        return node.latex_verbatim()
    except Exception:
        return ""


def _macro_arg(node: LatexMacroNode) -> str:
    """Extract the first mandatory argument of a macro as text."""
    if not node.nodeargd or not node.nodeargd.argnlist:
        return ""
    for sub in node.nodeargd.argnlist:
        if sub is None:
            continue
        if isinstance(sub, LatexGroupNode):
            inner = "".join(_node_text(n) for n in sub.nodelist)
            return inner.strip()
        return _node_text(sub).strip("{} \n\t")
    return ""


def _env_body(node: LatexEnvironmentNode) -> str:
    return "".join(_node_text(n) for n in node.nodelist).strip()


def _find_label(nodes) -> str | None:
    for n in nodes:
        if isinstance(n, LatexMacroNode) and n.macroname == "label":
            return _macro_arg(n)
    return None


def parse_latex(source: str) -> ParsedPaper:
    """Parse a LaTeX source string into a ParsedPaper."""
    walker = LatexWalker(source)
    try:
        nodes, _, _ = walker.get_latex_nodes()
    except Exception as e:
        return ParsedPaper(
            title_tex="(untitled)",
            author_tex="",
            date_tex="",
            abstract_tex=f"(parse error: {e})",
        )

    out = ParsedPaper(
        title_tex="(untitled)", author_tex="", date_tex="", abstract_tex="(no abstract found)"
    )
    counters = {1: 0, 2: 0, 3: 0}  # section, subsection, subsubsection

    def walk(node_list):
        for n in node_list:
            if isinstance(n, LatexMacroNode):
                name = n.macroname
                if name == "title":
                    out.title_tex = _macro_arg(n)
                elif name == "author":
                    out.author_tex = _macro_arg(n)
                elif name == "date":
                    out.date_tex = _macro_arg(n)
                elif name == "section":
                    counters[1] += 1
                    counters[2] = 0
                    counters[3] = 0
                    out.sections.append(
                        SectionInfo(f"{counters[1]}", _macro_arg(n), n.pos)
                    )
                elif name == "subsection":
                    counters[2] += 1
                    counters[3] = 0
                    out.sections.append(
                        SectionInfo(f"{counters[1]}.{counters[2]}", _macro_arg(n), n.pos)
                    )
                elif name == "subsubsection":
                    counters[3] += 1
                    out.sections.append(
                        SectionInfo(
                            f"{counters[1]}.{counters[2]}.{counters[3]}", _macro_arg(n), n.pos
                        )
                    )
                elif name == "includegraphics":
                    out.figures.append(_macro_arg(n))
            elif isinstance(n, LatexEnvironmentNode):
                env = n.environmentname
                if env == "abstract":
                    out.abstract_tex = _env_body(n)
                elif env in THEOREM_ENVS:
                    label = _find_label(n.nodelist) or f"{env}:unlabeled:{n.pos}"
                    body = _env_body(n)
                    body = re.sub(r"\\label\{[^}]*\}\s*", "", body, count=1).strip()
                    cur_sec = out.sections[-1].number if out.sections else None
                    out.theorems.append(
                        TheoremBlock(
                            id=label, env=env, statement_tex=body, section_number=cur_sec
                        )
                    )
                elif env == "document":
                    walk(n.nodelist)
                elif hasattr(n, "nodelist") and n.nodelist:
                    walk(n.nodelist)

    walk(nodes)
    return out


def source_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
