# 阶段0：环境配置与搭建（Production）

本目录用于完成上线前的服务器环境准备，目标是让 `billfan.cn` + `www.billfan.cn` 在当前公网机器上具备可运行的 FastAPI + nginx + HTTPS 基础设施。

## 你现在的状态

你已完成 DNS 解析（`@` 与 `www` 指向公网 IP），可以直接执行本阶段。

## 目录说明

- `deploy/env/app.env.example`：应用环境变量模板
- `deploy/nginx/billfan.cn.http.conf`：HTTP 模式 nginx 模板（申请证书前）
- `deploy/nginx/billfan.cn.https.conf`：HTTPS 模式 nginx 模板（申请证书后）
- `deploy/systemd/qh-paper-assistant.service`：FastAPI systemd 服务模板
- `scripts/deploy/phase0_install_system_deps.sh`：安装系统依赖
- `scripts/deploy/phase0_prepare_runtime.sh`：准备目录、env、Python 虚拟环境
- `scripts/deploy/phase0_deploy_configs.sh`：下发 nginx + systemd 配置
- `scripts/deploy/phase0_enable_https.sh`：申请证书并切到 HTTPS
- `scripts/deploy/phase0_verify.sh`：环境验收检查
- `scripts/deploy/phase0_all.sh`：一键串行执行（到 HTTP 模式）

## 推荐执行顺序

> 所有命令建议 root 执行。

### 1) 安装系统依赖

```bash
cd /var/www
./scripts/deploy/phase0_install_system_deps.sh
```

### 2) 准备运行时

```bash
cd /var/www
./scripts/deploy/phase0_prepare_runtime.sh
```

然后编辑：`/etc/qh-paper-assistant/app.env`

至少修改这些值：

- `JWT_SECRET_KEY`
- `DASHSCOPE_API_KEY`
- `EXA_API_KEY`

### 3) 下发 HTTP 配置（先通站点）

```bash
cd /var/www
NGINX_MODE=http ENABLE_APP_SERVICE=0 ./scripts/deploy/phase0_deploy_configs.sh
```

### 4) 申请证书并切 HTTPS

```bash
cd /var/www
EMAIL=admin@billfan.cn ./scripts/deploy/phase0_enable_https.sh
```

### 5) 验收

```bash
cd /var/www
./scripts/deploy/phase0_verify.sh
```

## 一键执行（可选）

```bash
cd /var/www
./scripts/deploy/phase0_all.sh
```

这会执行到 HTTP 阶段，证书步骤仍建议单独执行：

```bash
EMAIL=admin@billfan.cn ./scripts/deploy/phase0_enable_https.sh
```

## 与后续模块衔接

阶段0完成后，即可开始 M1（`app/db.py`）开发。后续业务模块只需要复用：

- `/var/www/.venv`（Python 运行环境）
- `/etc/qh-paper-assistant/app.env`（配置）
- `nginx + systemd`（已就位）

## 注意事项

- 当前 systemd 模板中的 `User=root` 是最稳妥默认值；后续可再收敛为专用低权限用户。
- `phase0_prepare_runtime.sh` 会安装基础 Python 包，后续项目 `requirements` 固定后应替换为锁定版本安装。
- 若证书申请失败，优先检查：
  - 80 端口是否对公网开放
  - DNS 是否生效
  - nginx 是否正常加载了 HTTP 模板
