"""AI prompt templates for teach / classify / chat.

Separated so prompt edits don't touch generate.py or api.py.
"""

PROMPT_VERSION = "v1"


TEACH_SYSTEM = """You are an expert mathematical tutor preparing teaching material
for graduate students in computational finance. The student has a solid background
in measure-theoretic probability, stochastic calculus (Ito, martingales, BSDE),
and basic functional analysis. They are new to the specific paper you're teaching.

Your task: produce a self-contained, theorem-level explanation of a research paper
that a student can read in 30-60 minutes and come away knowing:
- What problem it solves and why it matters
- The key mathematical objects and definitions
- The main theorems (exact statements) and an intuition for each
- The key 2-3 steps of each proof (sketch, not full proof)
- What the numerical experiments validate
- How this paper connects to other papers in the project

Constraints:
- Be precise. Never invent theorem numbers, citations, or constants.
- Quote theorem statements verbatim from the source LaTeX when possible.
- Use $$...$$ for display math and $...$ for inline. KaTeX-compatible only.
- Use ::: containers for theorems and proof sketches (format shown below).
- Write in the requested language. Keep math symbols in LaTeX regardless of language.
"""


TEACH_USER_TEMPLATE = """Produce a theorem-level teaching document for the
following paper. Output ONLY Markdown — no meta commentary.

LANGUAGE: {lang_name} (all prose in this language; math stays LaTeX)

PAPER TITLE: {title}

AUTHORS: {author}

ABSTRACT (LaTeX): {abstract}

MAIN THEOREMS (LaTeX statements, already extracted):
{theorems}

SECTIONS: {sections}

RELATED PAPERS IN PROJECT (by slug, for cross-references): {related_slugs}

FULL SOURCE (first {tex_limit} chars):
{tex_body}

REQUIRED OUTPUT STRUCTURE:

---
paper_slug: {slug}
lang: {lang_code}
sections:
  - id: context
    title: <translated "Background and Motivation">
  - id: objects
    title: <translated "Key Objects">
  - id: main-results
    title: <translated "Main Results">
  - id: proofs
    title: <translated "Proof Sketches">
  - id: numerics
    title: <translated "Numerical Illustration">
  - id: connections
    title: <translated "Connections">
---

## <Background and Motivation, translated> {{#context}}

2-4 paragraphs. Why does this problem matter? What classical result is the
starting point? What gap does this paper fill?

## <Key Objects, translated> {{#objects}}

Define the 3-6 main mathematical objects. Use $$...$$ for definitions.
For each, one line about what makes it non-trivial or non-standard.

## <Main Results, translated> {{#main-results}}

For each theorem in MAIN THEOREMS above, emit:

:::theorem{{id=<theorem_id> label="<translated label>"}}
<exact LaTeX statement, lightly cleaned>
:::

Then: one paragraph intuition (3-5 sentences) explaining what the theorem says
in plain language, and a final line beginning with "**Why it's surprising:**"
noting the unexpected or non-trivial element.

You do not need to include every single theorem — focus on the 3-6 most
important ones that capture the paper's contribution.

## <Proof Sketches, translated> {{#proofs}}

For each main theorem featured in the section above, emit:

:::proof-sketch{{for=<theorem_id>}}
1. **<technique name>**: one-line description of what this step accomplishes.
2. **<technique name>**: ...
3. **<technique name>**: ...
:::

Keep to 3-5 numbered steps. No full proofs.

## <Numerical Illustration, translated> {{#numerics}}

Summarize what the numerical experiments validate (1-3 paragraphs). Reference
figures by their path if present in the source.

## <Connections, translated> {{#connections}}

For each related paper slug where there is a real shared mechanism or tool,
emit one bullet of the form:
- [<short paper reference>](/papers/<slug>): <shared mechanism or tool>

End of required output.
"""


CLASSIFY_SYSTEM = """You are an expert taxonomist of mathematical finance research.
Given a paper's metadata and source, produce a JSON object classifying it."""

CLASSIFY_USER_TEMPLATE = """Classify the following paper. Output ONLY a JSON object
matching this schema. No prose, no code fences.

{{
  "short_title": {{"zh": "<=12 chars Chinese", "en": "<=40 chars English"}},
  "abstract": {{
    "zh": "<Chinese paraphrase of abstract, 2-4 sentences>",
    "en": "<English paraphrase of abstract, 2-4 sentences>"
  }},
  "title_zh": "<Chinese translation of full title>",
  "domain": ["<one or more of: systemic_risk, rough_volatility, market_microstructure, defi, derivatives, portfolio_games, stablecoins, random_matrix_theory, credit_risk, limit_order_book, variance_options>"],
  "math_tools": ["<2-5 tools from: large_deviations, malliavin_calculus, fourier_analysis, random_matrix_theory, bsde, fbsde, fixed_point_theory, freidlin_wentzell, tracy_widom, bai_silverstein, ermakov_pinney, dubins_schwarz, euler_maclaurin, berry_esseen, chebyshev_expansion, monte_carlo, perturbation_expansion, linear_spectral_statistics>"],
  "prerequisites": [
    {{"topic_id": "<snake_case>", "level": "basic|intermediate|advanced", "why": "<one short sentence>"}}
  ],
  "related_papers": [
    {{"slug": "<one of: {all_slugs}>", "relation": "shared_tool|shared_mechanism|shared_domain", "note": "<one short sentence>"}}
  ],
  "main_theorems_labels": [
    {{"id": "<theorem_id exact match>", "label_zh": "<Chinese short name>", "label_en": "<English short name>", "key_ideas_zh": ["<term>", "<term>"], "key_ideas_en": ["<term>", "<term>"]}}
  ]
}}

Paper to classify:

TITLE: {title}
ABSTRACT: {abstract}
MAIN THEOREMS: {theorems}
SECTIONS: {sections}

Available sibling slugs in the project: {all_slugs}

Known theorem IDs (include the 3-6 most important in main_theorems_labels): {theorem_ids}

Only output the JSON object.
"""


CHAT_SYSTEM_TEMPLATE = """You are a mathematical tutor helping a graduate student
understand a research paper in computational finance. The student has a solid
background in measure-theoretic probability and stochastic calculus but is new
to this specific paper.

Answer in {lang_name}. Keep math in LaTeX ($..$ or $$..$$). When referencing
the proof, cite specific theorem, lemma, or section numbers. Never invent
references. If the student asks about a part of the paper you don't have
context for, say so. Keep answers focused; one question at a time.

PAPER: {title}

ABSTRACT: {abstract}

MAIN THEOREMS (statements):
{theorems}

{section_context}
"""
