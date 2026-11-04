# 其华论文管理助手 Frontend

前端技术栈：React + Vite + Tailwind CSS + TypeScript。

## 开发

```bash
npm install
npm run dev
```

默认开发地址：`http://127.0.0.1:5173`，并代理 `/api` 到 `http://127.0.0.1:8000`。

## 构建

```bash
npm run build
```

产物输出在 `frontend/dist/`。

## 环境变量（可选）

- `VITE_API_BASE`：API 基础前缀，默认空字符串（同域 `/api`）。
