# 密钥与 MCP 启动命令（本地存档）

> 创建时间：2026-03-01
> 说明：本文件包含明文密钥，仅用于当前项目本地开发，请勿上传到公开仓库。

## 1) 模型与网关配置

- Qwen 模型：`qwen3.5-plus`（支持图片理解）
- DashScope 兼容网关：`https://coding.dashscope.aliyuncs.com/apps/anthropic/v1`
- DashScope API Key：`sk-sp-aefe6305c53f49ce90362623974f0fd7`

## 2) Exa 配置

- Exa API Key：`1d9defe8-8d2b-43e8-ba2a-1ae83c993e51`
- Exa MCP URL：`https://mcp.exa.ai/mcp`

## 3) paper_search MCP（openags/paper-search-mcp）

推荐本地目录：`/var/www/services/paper-search-mcp`

- 安装 uv（若未安装）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

- 克隆仓库

```bash
git clone https://github.com/openags/paper-search-mcp.git /var/www/services/paper-search-mcp
```

- 安装依赖（建议固定 Python 3.12，避免 3.14 轮子缺失）

```bash
uv sync --directory /var/www/services/paper-search-mcp --python 3.12
```

- 启动命令（stdio MCP）

```bash
uv run --directory /var/www/services/paper-search-mcp -m paper_search_mcp.server
```

- 可选环境变量（如你后续提供）

```bash
export SEMANTIC_SCHOLAR_API_KEY=""
```

## 4) Exa MCP（Codex）

- 直接添加 Exa 远程 MCP

```bash
codex mcp add exa --url https://mcp.exa.ai/mcp
```

## 5) 在 Codex 中注册 paper_search MCP

```bash
codex mcp add paper_search -- \
  uv run --directory /var/www/services/paper-search-mcp -m paper_search_mcp.server
```

## 6) 自动化脚本（已实现）

项目中已新增：

- `scripts/mcp/setup_mcp.sh`
- `scripts/mcp/start_paper_search_mcp.sh`

一键执行：

```bash
# 完整安装 + 注册（默认会执行 uv sync）
./scripts/mcp/setup_mcp.sh

# 若只想先注册 MCP（跳过依赖安装）
SKIP_PAPER_SYNC=1 ./scripts/mcp/setup_mcp.sh

# 单独启动 paper_search MCP
./scripts/mcp/start_paper_search_mcp.sh
```

## 7) 检查是否配置成功

```bash
codex mcp list
codex mcp get exa
codex mcp get paper_search
```

## 8) FastAPI 对接可行性

结论：`FastAPI` 可以直接对接这两个 MCP。

推荐方式：在 `app/agent.py` 中封装 MCP 客户端，向 `exa` 和 `paper_search` 发起 `tools/list` 与 `tools/call`，将结果回灌到 Agent tool-use 循环。

## 9) 常见依赖问题

如果 `uv sync` 报 `lxml` 编译失败（提示缺少 `libxml2/libxslt` 头文件），请安装：

```bash
apt-get update && apt-get install -y libxml2-dev libxslt1-dev
```

然后重试：

```bash
uv sync --directory /var/www/services/paper-search-mcp --python 3.12
```

## 10) 命令来源（官方）

- Exa MCP 官方文档：<https://exa.ai/docs/reference/exa-mcp>
- Exa MCP 官方仓库：<https://github.com/exa-labs/exa-mcp-server>
- paper-search MCP 官方仓库：<https://github.com/openags/paper-search-mcp>
