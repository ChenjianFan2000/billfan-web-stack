#!/usr/bin/env python3
import json
import os
import re
import shutil
from html import escape
from pathlib import Path


BASE_DIR = Path("/var/www")
DIST_DIR = BASE_DIR / "dist"
AIMATH_DIR = DIST_DIR / "aimath"
ASSETS_DIR = AIMATH_DIR / "assets"
PAPERS_DIR = AIMATH_DIR / "papers"
API_DIR = AIMATH_DIR / "api"
CONTENT_DIR = BASE_DIR / "services" / "paper-visualizer" / "paper_visualizer" / "backend" / "content"
KATEX_SRC = BASE_DIR / "frontend" / "node_modules" / "katex" / "dist"
KATEX_DST = AIMATH_DIR / "vendor" / "katex"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path):
    return path.read_text(encoding="utf-8")


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)


def strip_front_matter(text):
    if not text.startswith("---\n"):
        return text
    lines = text.splitlines(True)
    if not lines or lines[0].strip() != "---":
        return text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "".join(lines[idx + 1 :]).lstrip("\n")
    return text


def normalize_paper_link(url):
    if url.startswith("/papers/"):
        slug = url[len("/papers/") :].strip("/")
        return "/aimath/papers/{}/".format(slug)
    return url


def format_inline(text):
    escaped = escape(text)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: '<a href="{}">{}</a>'.format(
            escape(normalize_paper_link(m.group(2)), quote=True), m.group(1)
        ),
        escaped,
    )
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    return escaped


def slugify_title(title):
    slug = re.sub(r"[^\w\- ]+", "", title, flags=re.UNICODE).strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    return slug or "section"


def parse_attrs(raw):
    attrs = {}
    if not raw:
        return attrs
    for key, value in re.findall(r'(\w+)="([^"]*)"', raw):
        attrs[key] = value
    raw = re.sub(r'\w+="[^"]*"', "", raw)
    for item in raw.split():
        if "=" in item:
            key, value = item.split("=", 1)
            attrs[key.strip()] = value.strip().strip('"')
    return attrs


def md_to_html(text, anchor_prefix=""):
    lines = strip_front_matter(text).replace("\r\n", "\n").split("\n")
    blocks = []
    toc = []
    idx = 0

    def flush_paragraph(buffer):
        if not buffer:
            return
        content = " ".join(line.strip() for line in buffer if line.strip())
        if content:
            blocks.append("<p>{}</p>".format(format_inline(content)))

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if not stripped:
            idx += 1
            continue

        if stripped.startswith(":::"):
            marker = stripped[3:]
            kind = "callout"
            attrs = {}
            m = re.match(r"([a-zA-Z0-9_-]+)(?:\{(.*)\})?$", marker)
            if m:
                kind = m.group(1)
                attrs = parse_attrs(m.group(2) or "")
            inner = []
            idx += 1
            while idx < len(lines) and lines[idx].strip() != ":::":
                inner.append(lines[idx])
                idx += 1
            inner_html, _ = md_to_html("\n".join(inner), anchor_prefix=anchor_prefix)
            label = attrs.get("label", "")
            if kind == "proof-sketch":
                summary = label or "Proof Sketch"
                blocks.append(
                    '<details class="pv-callout pv-proof" open><summary>{}</summary>{}</details>'.format(
                        escape(summary), inner_html
                    )
                )
            else:
                title = label or kind.replace("-", " ").title()
                blocks.append(
                    '<section class="pv-callout pv-{}"><div class="pv-callout-title">{}</div>{}</section>'.format(
                        escape(kind), escape(title), inner_html
                    )
                )
            idx += 1
            continue

        if stripped.startswith("```"):
            fence_lang = stripped[3:].strip()
            code_lines = []
            idx += 1
            while idx < len(lines) and not lines[idx].strip().startswith("```"):
                code_lines.append(lines[idx])
                idx += 1
            blocks.append(
                '<pre class="pv-code" data-lang="{}"><code>{}</code></pre>'.format(
                    escape(fence_lang), escape("\n".join(code_lines))
                )
            )
            idx += 1
            continue

        if stripped == "---":
            blocks.append('<hr class="pv-rule" />')
            idx += 1
            continue

        if stripped.startswith("$$"):
            math_lines = [line]
            if stripped != "$$" and stripped.endswith("$$") and len(stripped) > 2:
                blocks.append('<div class="pv-math-block">{}</div>'.format(escape("\n".join(math_lines))))
                idx += 1
                continue
            idx += 1
            while idx < len(lines):
                math_lines.append(lines[idx])
                if lines[idx].strip().endswith("$$"):
                    idx += 1
                    break
                idx += 1
            blocks.append('<div class="pv-math-block">{}</div>'.format(escape("\n".join(math_lines))))
            continue

        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            raw_title = heading.group(2).strip()
            anchor = None
            anchor_match = re.search(r"\s*\{#([^}]+)\}\s*$", raw_title)
            if anchor_match:
                anchor = anchor_match.group(1).strip()
                raw_title = re.sub(r"\s*\{#([^}]+)\}\s*$", "", raw_title).strip()
            anchor = anchor or slugify_title(raw_title)
            anchor = "{}{}".format(anchor_prefix, anchor)
            if level <= 3:
                toc.append({"id": anchor, "title": raw_title, "level": level})
            blocks.append(
                '<h{level} id="{id}">{title}</h{level}>'.format(
                    level=level, id=escape(anchor, quote=True), title=format_inline(raw_title)
                )
            )
            idx += 1
            continue

        if re.match(r"^[-*]\s+", stripped):
            items = []
            while idx < len(lines) and re.match(r"^[-*]\s+", lines[idx].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[idx].strip()))
                idx += 1
            blocks.append(
                "<ul>{}</ul>".format(
                    "".join("<li>{}</li>".format(format_inline(item)) for item in items)
                )
            )
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while idx < len(lines) and re.match(r"^\d+\.\s+", lines[idx].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[idx].strip()))
                idx += 1
            blocks.append(
                "<ol>{}</ol>".format(
                    "".join("<li>{}</li>".format(format_inline(item)) for item in items)
                )
            )
            continue

        paragraph = [line]
        idx += 1
        while idx < len(lines):
            lookahead = lines[idx].strip()
            if not lookahead:
                break
            if (
                lookahead.startswith(":::")
                or lookahead.startswith("```")
                or lookahead == "---"
                or lookahead.startswith("#")
                or lookahead.startswith("$$")
                or re.match(r"^[-*]\s+", lookahead)
                or re.match(r"^\d+\.\s+", lookahead)
            ):
                break
            paragraph.append(lines[idx])
            idx += 1
        flush_paragraph(paragraph)

    return "\n".join(blocks), toc


def render_quality(quality, lang):
    if not quality:
        return '<div class="meta-empty">{}</div>'.format("暂无" if lang == "zh" else "None")
    title = "质量评估" if lang == "zh" else "Quality"
    items = []
    tier = quality.get("tier")
    sig = quality.get("significance_score")
    sig_max = quality.get("significance_max")
    if tier:
        items.append("<li><strong>Tier</strong><span>{}</span></li>".format(escape(str(tier))))
    if sig is not None:
        items.append(
            "<li><strong>{}</strong><span>{}/{}</span></li>".format(
                "显著性" if lang == "zh" else "Significance",
                escape(str(sig)),
                escape(str(sig_max if sig_max is not None else "")),
            )
        )
    verdict = quality.get("critic_verdict")
    if verdict:
        items.append(
            "<li><strong>{}</strong><span>{}</span></li>".format(
                "评语" if lang == "zh" else "Verdict", escape(str(verdict))
            )
        )
    return '<section class="meta-card"><h3>{}</h3><ul class="meta-list">{}</ul></section>'.format(
        title, "".join(items)
    )


def render_prereqs(items, lang):
    title = "先修知识" if lang == "zh" else "Prerequisites"
    if not items:
        return '<section class="meta-card"><h3>{}</h3><div class="meta-empty">{}</div></section>'.format(
            title, "暂无" if lang == "zh" else "None"
        )
    body = []
    for item in items:
        why = item.get("why", "")
        body.append(
            '<li><strong>{}</strong><span class="pill">{}</span><p>{}</p></li>'.format(
                escape(item.get("topic_id", "")),
                escape(item.get("level", "")),
                format_inline(why),
            )
        )
    return '<section class="meta-card"><h3>{}</h3><ul class="stack-list">{}</ul></section>'.format(
        title, "".join(body)
    )


def render_related(items, papers_lookup, lang, current_slug):
    title = "关联论文" if lang == "zh" else "Related Papers"
    related = [item for item in items if item.get("slug") and item.get("slug") != current_slug]
    if not related:
        return '<section class="meta-card"><h3>{}</h3><div class="meta-empty">{}</div></section>'.format(
            title, "暂无" if lang == "zh" else "None"
        )
    body = []
    for item in related:
        slug = item.get("slug")
        paper = papers_lookup.get(slug, {})
        short_title = paper.get("short_title", {})
        note = item.get("note", "")
        label = short_title.get(lang) or short_title.get("en") or slug
        body.append(
            '<li><a href="/aimath/papers/{}/">{}</a><p>{}</p></li>'.format(
                escape(slug, quote=True), escape(label), format_inline(note)
            )
        )
    return '<section class="meta-card"><h3>{}</h3><ul class="stack-list">{}</ul></section>'.format(
        title, "".join(body)
    )


def render_toc(items):
    if not items:
        return '<div class="meta-empty">No sections</div>'
    return '<ul class="toc-list">{}</ul>'.format(
        "".join(
            '<li class="lv-{}"><a href="#{}">{}</a></li>'.format(
                item["level"], escape(item["id"], quote=True), escape(item["title"])
            )
            for item in items
        )
    )


def page_template(title, body, extra_head="", extra_script=""):
    return """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <link rel="stylesheet" href="/aimath/assets/aimath.css" />
    <link rel="stylesheet" href="/aimath/vendor/katex/katex.min.css" />
    {extra_head}
  </head>
  <body>
    {body}
    <script defer src="/aimath/vendor/katex/katex.min.js"></script>
    <script defer src="/aimath/vendor/katex/contrib/auto-render.min.js"></script>
    {extra_script}
  </body>
</html>
""".format(
        title=escape(title),
        body=body,
        extra_head=extra_head,
        extra_script=extra_script,
    )


def build_detail_page(paper, meta, zh_html, zh_toc, en_html, en_toc, papers_lookup):
    short_title = meta.get("short_title", {})
    full_title = meta.get("title", {})
    title = short_title.get("zh") or short_title.get("en") or meta.get("slug")
    quality = meta.get("quality") or {}
    status = meta.get("status", "")
    repo = paper.get("repo") or meta.get("repo") or ""
    abstract = meta.get("abstract", {})

    slug = meta.get("slug", "")

    header = """
    <header class="pv-topbar">
      <div class="topbar-inner">
        <a class="brand" href="/aimath/">
          <span class="brand-kicker">aimath.billfan.cn</span>
          <span class="brand-title">Paper Visualizer</span>
        </a>
        <div class="topbar-actions">
          <button type="button" class="lang-btn" data-set-lang="zh">中文</button>
          <button type="button" class="lang-btn" data-set-lang="en">English</button>
          <button type="button" class="lang-btn" id="chat-toggle">AI Q&amp;A</button>
        </div>
      </div>
    </header>
    """

    hero = """
    <section class="paper-hero">
      <div class="hero-main" data-lang-panel="zh">
        <p class="eyebrow">研究解读</p>
        <h1>{zh_title}</h1>
        <p class="hero-summary">{zh_abstract}</p>
      </div>
      <div class="hero-main" data-lang-panel="en">
        <p class="eyebrow">Research Guide</p>
        <h1>{en_title}</h1>
        <p class="hero-summary">{en_abstract}</p>
      </div>
      <div class="hero-meta">
        <span class="status-pill">{status}</span>
        {repo}
        <a class="ghost-btn" href="/content/{slug}/source.pdf" target="_blank" rel="noreferrer">PDF</a>
        <a class="ghost-btn" href="/content/{slug}/source.tex" target="_blank" rel="noreferrer">TeX</a>
      </div>
    </section>
    """.format(
        zh_title=escape(short_title.get("zh") or full_title.get("zh") or title),
        zh_abstract=escape(abstract.get("zh") or abstract.get("tex") or ""),
        en_title=escape(short_title.get("en") or full_title.get("en") or title),
        en_abstract=escape(abstract.get("en") or abstract.get("tex") or ""),
        status=escape(status.replace("_", " ") if status else "draft"),
        repo='<span class="meta-chip">{}</span>'.format(escape(repo)) if repo else "",
        slug=escape(slug, quote=True),
    )

    main = """
    <main class="paper-layout">
      <article class="paper-article">
        <div class="markdown-body" data-lang-panel="zh">{zh_html}</div>
        <div class="markdown-body" data-lang-panel="en">{en_html}</div>
      </article>
      <aside class="paper-sidebar">
        <section class="meta-card" data-lang-panel="zh"><h3>目录</h3>{zh_toc}</section>
        <section class="meta-card" data-lang-panel="en"><h3>Contents</h3>{en_toc}</section>
        <div data-lang-panel="zh">{zh_quality}{zh_prereqs}{zh_related}</div>
        <div data-lang-panel="en">{en_quality}{en_prereqs}{en_related}</div>
      </aside>
    </main>
    """.format(
        zh_html=zh_html,
        en_html=en_html,
        zh_toc=render_toc(zh_toc),
        en_toc=render_toc(en_toc),
        zh_quality=render_quality(quality, "zh"),
        en_quality=render_quality(quality, "en"),
        zh_prereqs=render_prereqs(meta.get("prerequisites", []), "zh"),
        en_prereqs=render_prereqs(meta.get("prerequisites", []), "en"),
        zh_related=render_related(meta.get("related_papers", []), papers_lookup, "zh", meta.get("slug")),
        en_related=render_related(meta.get("related_papers", []), papers_lookup, "en", meta.get("slug")),
    )

    chat_panel = """
    <section class="chat-shell" id="chat-shell" hidden>
      <div class="chat-card">
        <div class="chat-head">
          <div>
            <strong>Paper Chat</strong>
            <p>Ask about the current paper only.</p>
          </div>
          <button type="button" class="ghost-btn" id="chat-close">Close</button>
        </div>
        <div class="chat-log" id="chat-log">
          <div class="chat-msg assistant">
            <div class="chat-role">assistant</div>
            <div class="chat-body">Ask about definitions, theorem intuition, proof steps, or numerical validation.</div>
          </div>
        </div>
        <form class="chat-form" id="chat-form">
          <textarea id="chat-input" placeholder="Ask a question about this paper..." required></textarea>
          <div class="chat-actions">
            <span class="chat-status" id="chat-status"></span>
            <button type="submit" class="lang-btn is-active" id="chat-send">Send</button>
          </div>
        </form>
      </div>
    </section>
    """

    script = """
    <script>
      (function () {
        var paperSlug = __PAPER_SLUG__;
        var current = localStorage.getItem("aimath-lang") || "zh";
        var history = [];
        var chatShell = document.getElementById("chat-shell");
        var chatLog = document.getElementById("chat-log");
        var chatStatus = document.getElementById("chat-status");
        var chatInput = document.getElementById("chat-input");
        var chatSend = document.getElementById("chat-send");

        function applyLang(lang) {
          current = lang;
          localStorage.setItem("aimath-lang", lang);
          var panels = document.querySelectorAll("[data-lang-panel]");
          for (var i = 0; i < panels.length; i += 1) {
            panels[i].style.display = panels[i].getAttribute("data-lang-panel") === lang ? "" : "none";
          }
          var buttons = document.querySelectorAll("[data-set-lang]");
          for (var j = 0; j < buttons.length; j += 1) {
            var active = buttons[j].getAttribute("data-set-lang") === lang;
            buttons[j].classList.toggle("is-active", active);
          }
        }
        var buttons = document.querySelectorAll("[data-set-lang]");
        for (var i = 0; i < buttons.length; i += 1) {
          buttons[i].addEventListener("click", function (event) {
            applyLang(event.currentTarget.getAttribute("data-set-lang"));
          });
        }

        function setChatVisible(opened) {
          if (!chatShell) return;
          chatShell.hidden = !opened;
        }

        function appendChatMessage(role, content) {
          if (!chatLog) return null;
          var message = document.createElement("div");
          message.className = "chat-msg " + role;
          var roleNode = document.createElement("div");
          roleNode.className = "chat-role";
          roleNode.textContent = role;
          var bodyNode = document.createElement("div");
          bodyNode.className = "chat-body";
          bodyNode.textContent = content || "";
          message.appendChild(roleNode);
          message.appendChild(bodyNode);
          chatLog.appendChild(message);
          chatLog.scrollTop = chatLog.scrollHeight;
          return bodyNode;
        }

        function currentSection() {
          var activeHash = window.location.hash || "";
          if (!activeHash) return "";
          var target = document.querySelector(activeHash);
          if (!target) return activeHash.replace(/^#/, "");
          return target.textContent || activeHash.replace(/^#/, "");
        }

        function setBusy(busy, text) {
          if (chatStatus) {
            chatStatus.textContent = text || "";
          }
          if (chatSend) {
            chatSend.disabled = !!busy;
          }
          if (chatInput) {
            chatInput.disabled = !!busy;
          }
        }

        function parseSSEChunk(chunk, onToken, onDone, onError) {
          var events = chunk.split("\\n\\n");
          for (var i = 0; i < events.length; i += 1) {
            var ev = events[i];
            if (!ev) continue;
            var lines = ev.split("\\n");
            var kind = "";
            var dataLine = "";
            for (var j = 0; j < lines.length; j += 1) {
              if (lines[j].indexOf("event: ") === 0) kind = lines[j].slice(7).trim();
              if (lines[j].indexOf("data: ") === 0) dataLine = lines[j].slice(6);
            }
            if (!kind || !dataLine) continue;
            try {
              var payload = JSON.parse(dataLine);
              if (kind === "token") onToken(payload.text || "");
              if (kind === "done") onDone();
              if (kind === "error") onError(payload.message || "Unknown chat error");
            } catch (err) {
              onError("Failed to parse chat response");
            }
          }
        }

        async function sendChat(message) {
          var assistantBody = appendChatMessage("assistant", "");
          setBusy(true, "Thinking...");
          var response;
          var contentType = "";
          try {
            response = await fetch("/api/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                paper_slug: paperSlug,
                message: message,
                history: history,
                lang: current,
                current_section: currentSection()
              })
            });
          } catch (err) {
            if (assistantBody) assistantBody.textContent = String(err);
            setBusy(false, "Network error");
            return;
          }

          contentType = (response.headers.get("content-type") || "").toLowerCase();
          if (!response.ok) {
            if (assistantBody) assistantBody.textContent = "Chat endpoint unavailable (" + response.status + ")";
            setBusy(false, "Unavailable");
            return;
          }

          if (!response.body || contentType.indexOf("text/event-stream") === -1) {
            if (assistantBody) {
              assistantBody.textContent = "Chat endpoint unavailable on current host.";
            }
            setBusy(false, contentType ? "Unexpected " + contentType : "Unavailable");
            return;
          }

          var reader = response.body.getReader();
          var decoder = new TextDecoder("utf-8");
          var buffer = "";
          var finalText = "";
          var done = false;

          while (!done) {
            var chunk = await reader.read();
            if (chunk.done) break;
            buffer += decoder.decode(chunk.value, { stream: true });
            var parts = buffer.split("\\n\\n");
            buffer = parts.pop() || "";
            parseSSEChunk(parts.join("\\n\\n"), function (text) {
              finalText += text;
              if (assistantBody) assistantBody.textContent = finalText;
              if (chatLog) chatLog.scrollTop = chatLog.scrollHeight;
            }, function () {
              done = true;
            }, function (message) {
              done = true;
              if (assistantBody && !finalText) assistantBody.textContent = message;
              setBusy(false, message);
            });
          }

          if (finalText) {
            history.push({ role: "user", content: message });
            history.push({ role: "assistant", content: finalText });
          } else if (assistantBody && !assistantBody.textContent) {
            assistantBody.textContent = "No streamed content returned.";
          }
          setBusy(false, finalText ? "" : "No content");
        }

        var chatToggle = document.getElementById("chat-toggle");
        var chatClose = document.getElementById("chat-close");
        if (chatToggle) {
          chatToggle.addEventListener("click", function () {
            setChatVisible(true);
          });
        }
        if (chatClose) {
          chatClose.addEventListener("click", function () {
            setChatVisible(false);
          });
        }
        var chatForm = document.getElementById("chat-form");
        if (chatForm) {
          chatForm.addEventListener("submit", function (event) {
            event.preventDefault();
            var text = (chatInput && chatInput.value || "").trim();
            if (!text) return;
            appendChatMessage("user", text);
            if (chatInput) chatInput.value = "";
            sendChat(text);
            if (chatLog) chatLog.scrollTop = chatLog.scrollHeight;
          });
        }

        applyLang(current);
        window.addEventListener("load", function () {
          if (window.renderMathInElement) {
            window.renderMathInElement(document.body, {
              delimiters: [
                { left: "$$", right: "$$", display: true },
                { left: "\\\\[", right: "\\\\]", display: true },
                { left: "$", right: "$", display: false },
                { left: "\\\\(", right: "\\\\)", display: false }
              ],
              throwOnError: false
            });
          }
        });
      })();
    </script>
    """.replace("__PAPER_SLUG__", json.dumps(slug, ensure_ascii=False))

    body = '<div class="site-shell">{header}<div class="page-wrap">{hero}{main}{chat_panel}</div></div>'.format(
        header=header, hero=hero, main=main, chat_panel=chat_panel
    )
    return page_template(title, body, extra_script=script)


def build_home_js(index_payload):
    data_json = json.dumps(index_payload, ensure_ascii=False)
    return """const AIMATH_DATA = {data};

function getLang() {{
  return localStorage.getItem("aimath-lang") || "zh";
}}

function setLang(lang) {{
  localStorage.setItem("aimath-lang", lang);
}}

function normalize(text) {{
  return (text || "").toLowerCase();
}}

function chipButton(label, group, value, active) {{
  return `<button class="chip ${{active ? "is-active" : ""}}" data-group="${{group}}" data-value="${{value}}">${{label}}</button>`;
}}

function render() {{
  const root = document.getElementById("aimath-home");
  if (!root) return;

  const lang = getLang();
  const queryInput = document.getElementById("aimath-query");
  const query = normalize(queryInput ? queryInput.value : "");
  const activeDomains = Array.prototype.slice.call(document.querySelectorAll('[data-group="domain"].is-active')).map((el) => el.getAttribute("data-value"));
  const activeTools = Array.prototype.slice.call(document.querySelectorAll('[data-group="tool"].is-active')).map((el) => el.getAttribute("data-value"));

  const filtered = AIMATH_DATA.papers.filter((paper) => {{
    const haystack = [
      paper.slug,
      paper.short_title.zh,
      paper.short_title.en,
      typeof paper.one_liner === "string" ? paper.one_liner : paper.one_liner.zh,
      typeof paper.one_liner === "string" ? paper.one_liner : paper.one_liner.en
    ].join(" ").toLowerCase();
    if (query && haystack.indexOf(query) === -1) return false;
    if (activeDomains.length && !activeDomains.every((item) => paper.domain.indexOf(item) !== -1)) return false;
    if (activeTools.length && !activeTools.every((item) => paper.math_tools.indexOf(item) !== -1)) return false;
    return true;
  }});

  const cards = filtered.map((paper) => {{
    const quality = paper.quality || {{}};
    const oneLiner = typeof paper.one_liner === "string"
      ? paper.one_liner
      : (paper.one_liner[lang] || paper.one_liner.en || paper.one_liner.zh || "");
    const title = paper.short_title[lang] || paper.short_title.en || paper.short_title.zh || paper.slug;
    return `
      <a class="paper-card" href="/aimath/papers/${{paper.slug}}/">
        <div class="paper-card-head">
          <span class="status-pill">${{paper.status || "draft"}}</span>
          ${{quality.tier ? `<span class="meta-chip">Tier ${{quality.tier}}</span>` : ""}}
          ${{quality.significance_score != null ? `<span class="meta-chip">S ${{quality.significance_score}}/${{quality.significance_max || ""}}</span>` : ""}}
        </div>
        <h3>${{title}}</h3>
        <p>${{oneLiner || ""}}</p>
        <div class="tag-row">
          ${{paper.domain.map((item) => `<span class="tag">${{item}}</span>`).join("")}}
        </div>
        <div class="tag-row subtle">
          ${{paper.math_tools.slice(0, 4).map((item) => `<span class="tag subtle">${{item}}</span>`).join("")}}
        </div>
      </a>
    `;
  }}).join("");

  const domainChips = AIMATH_DATA.domains.map((item) => {{
    const active = activeDomains.indexOf(item.key) !== -1;
    return chipButton(item.label[lang] || item.label.en || item.key, "domain", item.key, active);
  }}).join("");

  const toolChips = AIMATH_DATA.math_tools.map((item) => {{
    const active = activeTools.indexOf(item.key) !== -1;
    return chipButton(item.label[lang] || item.label.en || item.key, "tool", item.key, active);
  }}).join("");

  root.innerHTML = `
    <div class="site-shell">
      <header class="hero-shell">
        <div class="hero-grid">
          <div>
            <p class="eyebrow">aimath.billfan.cn</p>
            <h1>${{lang === "zh" ? "AI 数学论文可视化讲义" : "AI Teaching Layer for Math Papers"}}</h1>
            <p class="hero-copy">${{lang === "zh"
              ? "这里不是论文上传工具，而是一个面向阅读与教学的静态研究站。当前收录 11 篇计算金融与数学研究论文，支持双语讲义、标签过滤、目录跳转与原始 PDF / TeX 浏览。"
              : "This host is a reading-oriented teaching site. It bundles 11 computational-finance and mathematical research papers with bilingual notes, filters, deep links, and direct PDF / TeX access."}}</p>
          </div>
          <div class="hero-panel">
            <div class="lang-switch">
              <button class="lang-btn ${{lang === "zh" ? "is-active" : ""}}" data-home-lang="zh">中文</button>
              <button class="lang-btn ${{lang === "en" ? "is-active" : ""}}" data-home-lang="en">English</button>
            </div>
            <div class="hero-stats">
              <div><strong>${{AIMATH_DATA.papers.length}}</strong><span>${{lang === "zh" ? "篇论文" : "papers"}}</span></div>
              <div><strong>${{AIMATH_DATA.domains.length}}</strong><span>${{lang === "zh" ? "研究主题" : "domains"}}</span></div>
              <div><strong>${{AIMATH_DATA.math_tools.length}}</strong><span>${{lang === "zh" ? "数学工具" : "math tools"}}</span></div>
            </div>
            <a class="ghost-btn wide" href="/content/" target="_blank" rel="noreferrer">${{lang === "zh" ? "查看原始内容目录" : "Browse raw content tree"}}</a>
          </div>
        </div>
      </header>

      <main class="home-layout">
        <aside class="filters-card">
          <div class="control-block">
            <label for="aimath-query">${{lang === "zh" ? "检索论文" : "Search papers"}}</label>
            <input id="aimath-query" class="query-input" placeholder="${{lang === "zh" ? "标题、slug、摘要关键词" : "title, slug, or abstract keywords"}}" value="${{query.replace(/"/g, "&quot;")}}" />
          </div>
          <div class="control-block">
            <h2>${{lang === "zh" ? "研究主题" : "Domains"}}</h2>
            <div class="chip-wrap">${{domainChips}}</div>
          </div>
          <div class="control-block">
            <h2>${{lang === "zh" ? "数学工具" : "Math Tools"}}</h2>
            <div class="chip-wrap">${{toolChips}}</div>
          </div>
        </aside>

        <section class="results-shell">
          <div class="results-head">
            <h2>${{lang === "zh" ? "论文卡片" : "Paper cards"}}</h2>
            <span>${{filtered.length}} / ${{AIMATH_DATA.papers.length}}</span>
          </div>
          <div class="cards-grid">${{cards || `<div class="empty-state">${{lang === "zh" ? "没有匹配结果" : "No results"}}</div>`}}</div>
        </section>
      </main>
    </div>
  `;

  const nextInput = document.getElementById("aimath-query");
  if (nextInput) {{
    nextInput.addEventListener("input", render);
  }}
  Array.prototype.forEach.call(document.querySelectorAll("[data-group]"), function (button) {{
    button.addEventListener("click", function () {{
      button.classList.toggle("is-active");
      render();
    }});
  }});
  Array.prototype.forEach.call(document.querySelectorAll("[data-home-lang]"), function (button) {{
    button.addEventListener("click", function () {{
      setLang(button.getAttribute("data-home-lang"));
      render();
    }});
  }});

  window.setTimeout(function () {{
    if (window.renderMathInElement) {{
      window.renderMathInElement(root, {{
        delimiters: [
          {{ left: "$$", right: "$$", display: true }},
          {{ left: "\\\\[", right: "\\\\]", display: true }},
          {{ left: "$", right: "$", display: false }},
          {{ left: "\\\\(", right: "\\\\)", display: false }}
        ],
        throwOnError: false
      }});
    }}
  }}, 0);
}}

document.addEventListener("DOMContentLoaded", render);
""".format(data=data_json)


def build_home_page():
    return page_template(
        "Paper Visualizer",
        '<div id="aimath-home"></div>',
        extra_script='<script defer src="/aimath/assets/home.js"></script>',
    )


def build_css():
    return """
:root {
  --bg: #f5efe4;
  --panel: rgba(255, 250, 240, 0.88);
  --panel-strong: rgba(255, 247, 232, 0.98);
  --ink: #1f2a30;
  --muted: #627078;
  --line: rgba(31, 42, 48, 0.12);
  --accent: #c44f2d;
  --accent-strong: #9f3518;
  --accent-soft: rgba(196, 79, 45, 0.12);
  --chip: rgba(47, 78, 90, 0.08);
  --shadow: 0 24px 60px rgba(39, 28, 18, 0.12);
  --radius: 20px;
  --content-width: min(1380px, calc(100vw - 32px));
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  color: var(--ink);
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
  background:
    radial-gradient(circle at top left, rgba(196, 79, 45, 0.18), transparent 26%),
    radial-gradient(circle at top right, rgba(53, 90, 100, 0.18), transparent 24%),
    linear-gradient(180deg, #f8f1e5 0%, #efe2cd 58%, #e7dac4 100%);
  min-height: 100vh;
}

a {
  color: inherit;
}

.site-shell {
  width: var(--content-width);
  margin: 0 auto;
  padding: 20px 0 48px;
}

.hero-shell,
.paper-hero,
.filters-card,
.results-shell,
.meta-card,
.paper-card,
.markdown-body,
.paper-sidebar {
  backdrop-filter: blur(18px);
}

.hero-shell,
.paper-hero {
  background: linear-gradient(135deg, rgba(255, 249, 239, 0.94), rgba(247, 236, 217, 0.92));
  border: 1px solid rgba(31, 42, 48, 0.09);
  border-radius: calc(var(--radius) + 6px);
  box-shadow: var(--shadow);
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(300px, 0.9fr);
  gap: 24px;
  padding: 28px;
}

.eyebrow,
.brand-kicker {
  margin: 0 0 8px;
  color: var(--accent-strong);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}

h1,
h2,
h3,
h4 {
  margin: 0;
  line-height: 1.12;
}

.hero-grid h1,
.paper-hero h1 {
  font-size: clamp(32px, 4.6vw, 56px);
  letter-spacing: -0.04em;
  max-width: 16ch;
}

.hero-copy,
.hero-summary {
  margin-top: 14px;
  color: var(--muted);
  font-size: 17px;
  line-height: 1.7;
  max-width: 72ch;
}

.hero-panel,
.paper-sidebar,
.filters-card,
.results-shell,
.markdown-body,
.meta-card,
.paper-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.hero-panel {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.hero-stats div {
  border-radius: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.55);
}

.hero-stats strong {
  display: block;
  font-size: 28px;
}

.hero-stats span {
  color: var(--muted);
  font-size: 13px;
}

.lang-switch,
.topbar-actions {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
}

.lang-btn,
.ghost-btn,
.chip {
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.76);
  color: var(--ink);
  border-radius: 999px;
  padding: 10px 16px;
  cursor: pointer;
  font: inherit;
  text-decoration: none;
  transition: transform 180ms ease, background 180ms ease, color 180ms ease, border-color 180ms ease;
}

.lang-btn:hover,
.ghost-btn:hover,
.chip:hover {
  transform: translateY(-1px);
  border-color: rgba(196, 79, 45, 0.35);
}

.lang-btn.is-active,
.chip.is-active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff5ef;
}

.ghost-btn.wide {
  justify-content: center;
  text-align: center;
}

.home-layout,
.paper-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 22px;
  margin-top: 22px;
}

.filters-card,
.paper-sidebar {
  position: sticky;
  top: 20px;
  align-self: start;
  padding: 18px;
}

.control-block + .control-block,
.meta-card + .meta-card {
  margin-top: 18px;
}

.control-block h2,
.meta-card h3 {
  font-size: 16px;
  margin-bottom: 12px;
}

.query-input {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.8);
  font: inherit;
  color: var(--ink);
}

.chip-wrap,
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.results-shell {
  padding: 18px;
}

.results-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.results-head span,
.meta-empty,
.paper-card p,
.stack-list p,
.toc-list a {
  color: var(--muted);
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.paper-card {
  padding: 18px;
  text-decoration: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 250px;
}

.paper-card:hover {
  transform: translateY(-2px);
}

.paper-card-head {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.paper-card h3 {
  font-size: 24px;
}

.paper-card p {
  margin: 0;
  line-height: 1.65;
  flex: 1;
}

.status-pill,
.meta-chip,
.tag,
.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}

.status-pill {
  background: rgba(31, 42, 48, 0.86);
  color: #fff7eb;
}

.meta-chip,
.tag,
.pill {
  background: var(--chip);
  color: var(--ink);
}

.tag.subtle {
  background: rgba(47, 78, 90, 0.06);
  color: var(--muted);
}

.paper-hero {
  padding: 24px 26px;
  margin-top: 8px;
}

.hero-meta {
  margin-top: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.paper-article {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.markdown-body {
  padding: 28px;
  line-height: 1.75;
  font-size: 17px;
}

.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin-top: 30px;
  margin-bottom: 12px;
  letter-spacing: -0.02em;
}

.markdown-body p {
  margin: 14px 0;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 24px;
  margin: 12px 0;
}

.markdown-body li {
  margin: 8px 0;
}

.markdown-body code,
.pv-code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.markdown-body code {
  background: rgba(31, 42, 48, 0.08);
  padding: 2px 6px;
  border-radius: 6px;
}

.pv-code {
  background: rgba(31, 42, 48, 0.94);
  color: #f7ead9;
  padding: 16px;
  border-radius: 18px;
  overflow-x: auto;
}

.pv-rule {
  border: 0;
  border-top: 1px solid var(--line);
  margin: 30px 0;
}

.pv-math-block {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 18px;
  border: 1px solid rgba(31, 42, 48, 0.08);
  padding: 14px;
  overflow-x: auto;
}

.pv-callout {
  padding: 18px 18px 16px;
  border-radius: 18px;
  border: 1px solid rgba(196, 79, 45, 0.18);
  background: linear-gradient(180deg, rgba(255, 250, 240, 0.95), rgba(247, 239, 227, 0.82));
  margin: 20px 0;
}

.pv-proof {
  border-color: rgba(53, 90, 100, 0.18);
  background: linear-gradient(180deg, rgba(247, 251, 252, 0.96), rgba(236, 244, 246, 0.86));
}

.pv-callout-title,
.pv-proof summary {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent-strong);
  cursor: pointer;
}

.pv-proof summary {
  color: #28596b;
  margin-bottom: 10px;
}

.stack-list,
.meta-list,
.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.stack-list li + li,
.meta-list li + li {
  border-top: 1px solid var(--line);
  margin-top: 10px;
  padding-top: 10px;
}

.meta-list li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.stack-list p {
  margin: 6px 0 0;
}

.toc-list li + li {
  margin-top: 8px;
}

.toc-list .lv-3 {
  padding-left: 14px;
}

.topbar-inner {
  width: var(--content-width);
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
}

.chat-shell {
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 60;
  width: min(460px, calc(100vw - 24px));
}

.chat-card {
  background: rgba(255, 249, 239, 0.98);
  border: 1px solid var(--line);
  border-radius: 24px;
  box-shadow: 0 22px 70px rgba(24, 18, 12, 0.18);
  padding: 16px;
}

.chat-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.chat-head p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.chat-log {
  margin-top: 14px;
  max-height: min(54vh, 520px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-msg {
  border-radius: 18px;
  padding: 12px 14px;
}

.chat-msg.user {
  background: rgba(196, 79, 45, 0.11);
}

.chat-msg.assistant {
  background: rgba(47, 78, 90, 0.08);
}

.chat-role {
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent-strong);
  margin-bottom: 6px;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
}

.chat-body {
  white-space: pre-wrap;
  line-height: 1.7;
}

.chat-form {
  margin-top: 14px;
}

.chat-form textarea {
  width: 100%;
  min-height: 110px;
  resize: vertical;
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--ink);
  font: inherit;
}

.chat-actions {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.chat-status {
  color: var(--muted);
  font-size: 13px;
}

.pv-topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  backdrop-filter: blur(20px);
  background: rgba(245, 239, 228, 0.75);
  border-bottom: 1px solid rgba(31, 42, 48, 0.08);
  padding: 14px 0;
}

.brand {
  text-decoration: none;
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 22px;
  letter-spacing: -0.04em;
}

.empty-state {
  border: 1px dashed var(--line);
  border-radius: 18px;
  padding: 28px;
  color: var(--muted);
  text-align: center;
}

@media (max-width: 1100px) {
  .home-layout,
  .paper-layout,
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .filters-card,
  .paper-sidebar {
    position: static;
  }

  .cards-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .site-shell {
    width: min(100vw - 20px, 100%);
  }

  .hero-grid,
  .paper-hero,
  .results-shell,
  .filters-card,
  .markdown-body,
  .paper-sidebar {
    padding: 16px;
  }

  .hero-grid h1,
  .paper-hero h1 {
    max-width: none;
  }

  .topbar-inner {
    width: min(100vw - 20px, 100%);
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-stats {
    grid-template-columns: 1fr;
  }
}
"""


def build_root_loader():
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>billfan.cn</title>
    <script>
      (function () {
        var host = window.location.hostname;
        var path = window.location.pathname;
        var isAimath = host === "aimath.billfan.cn";
        if (isAimath) {
          var target = "/aimath/";
          if (path !== target) {
            window.location.replace(target);
          }
          return;
        }
        document.write('<link rel="stylesheet" crossorigin href="/assets/index-BaVWdeoZ.css">');
      })();
    </script>
  </head>
  <body>
    <div id="root"></div>
    <script>
      (function () {
        if (window.location.hostname === "aimath.billfan.cn") {
          return;
        }
        var script = document.createElement("script");
        script.type = "module";
        script.crossOrigin = "anonymous";
        script.src = "/assets/index-DhDVtbga.js";
        document.body.appendChild(script);
      })();
    </script>
  </body>
</html>
"""


def build_home_index_payload(index_data, tags):
    domains = []
    for key, item in sorted(tags.get("domains", {}).items()):
        domains.append({"key": key, "label": item.get("label", {})})
    math_tools = []
    for key, item in sorted(tags.get("math_tools", {}).items()):
        math_tools.append({"key": key, "label": item.get("label", {})})
    return {
        "generated_at": index_data.get("generated_at"),
        "papers": index_data.get("papers", []),
        "domains": domains,
        "math_tools": math_tools,
    }


def copy_katex():
    if not KATEX_SRC.exists():
        return
    if KATEX_DST.exists():
        shutil.rmtree(str(KATEX_DST))
    shutil.copytree(str(KATEX_SRC), str(KATEX_DST))


def link_content():
    target = DIST_DIR / "content"
    if target.is_symlink() or target.exists():
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(str(target))
    os.symlink(str(CONTENT_DIR), str(target))


def main():
    ensure_dir(ASSETS_DIR)
    ensure_dir(PAPERS_DIR)
    ensure_dir(API_DIR)

    index_data = read_json(CONTENT_DIR / "papers.json")
    tags = read_json(CONTENT_DIR / "tags.json")
    papers_lookup = {item["slug"]: item for item in index_data.get("papers", [])}

    (DIST_DIR / "index.html").write_text(build_root_loader(), encoding="utf-8")
    (AIMATH_DIR / "index.html").write_text(build_home_page(), encoding="utf-8")
    (ASSETS_DIR / "aimath.css").write_text(build_css(), encoding="utf-8")
    (ASSETS_DIR / "home.js").write_text(
        build_home_js(build_home_index_payload(index_data, tags)), encoding="utf-8"
    )
    (API_DIR / "health.json").write_text(
        json.dumps({"status": "ok", "papers_count": len(index_data.get("papers", []))}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (API_DIR / "papers.json").write_text(
        json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (API_DIR / "tags.json").write_text(
        json.dumps(tags, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for paper in index_data.get("papers", []):
        slug = paper["slug"]
        meta = read_json(CONTENT_DIR / slug / "meta.json")
        zh_html, zh_toc = md_to_html(read_text(CONTENT_DIR / slug / "zh.md"), anchor_prefix="zh-")
        en_html, en_toc = md_to_html(read_text(CONTENT_DIR / slug / "en.md"), anchor_prefix="en-")
        detail_payload = {
            "meta": meta,
            "content": {
                "zh": read_text(CONTENT_DIR / slug / "zh.md"),
                "en": read_text(CONTENT_DIR / slug / "en.md"),
            },
        }
        detail_html = build_detail_page(
            paper=paper,
            meta=meta,
            zh_html=zh_html,
            zh_toc=zh_toc,
            en_html=en_html,
            en_toc=en_toc,
            papers_lookup=papers_lookup,
        )
        page_dir = PAPERS_DIR / slug
        ensure_dir(page_dir)
        (page_dir / "index.html").write_text(detail_html, encoding="utf-8")
        api_page_dir = API_DIR / "papers"
        ensure_dir(api_page_dir)
        (api_page_dir / "{}.json".format(slug)).write_text(
            json.dumps(detail_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    copy_katex()
    link_content()

    print("aimath static site built at {}".format(AIMATH_DIR))


if __name__ == "__main__":
    main()
