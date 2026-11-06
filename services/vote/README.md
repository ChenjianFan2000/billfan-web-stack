# 旦口喜剧大赛投票站

运行域名：`https://vote.billfan.cn`。这是 `billfan-web-stack` 中独立的投票服务：FastAPI + SQLite WAL + 原生 HTML/CSS/JavaScript，使用 Nginx 与 systemd 原生部署。前端没有 Node 构建步骤，所有图片、脚本和样式从本站提供。

投票站使用自己的端口、系统账户、虚拟环境、数据库和密码。现有 `billfan.cn`、`tongnian.billfan.cn` 的应用代码、数据库、Nginx 配置和 systemd 服务均无需更改。

## 页面和功能

| 地址 | 用途 |
| --- | --- |
| `/` | 当前选手、补充组别、投票/取消投票按钮、全场弹幕 |
| `/players` | 全部选手、出场状态、开锁票状态、我的投票记录、已公布的结果 |
| `/admin#key=管理员密码` | 管理入口；首次访问交换管理员 Cookie，随后移除地址中的密码 |
| `/api/health` | 无需登录的健康检查 |

管理端支持选手管理和批量导入、切换当前选手、单人开票/锁票、一键锁票、批量公布/隐藏票数、公开或隐藏的票数调整、醒目弹幕、删除弹幕、按时长禁言及解禁、CSV 导出和操作审计。

生产安装初始名单为空、没有当前选手，且尚未开票。应在管理端录入真实参赛选手，再选择并开票；部署脚本不会导入演示名单或测试数据库。选手票数默认隐藏，管理员公布后才显示。已开票且未锁票的选手，即使不再是当前选手，观众仍可从名单页修改自己的选择。切换选手时可以选择同时锁定上一位。

### 管理员链接

示例仅表示格式：

```text
https://vote.billfan.cn/admin#key=YOUR_ADMIN_PASSWORD
```

`#key=` 后是明文密码，符合“持有链接即可使用”的方式。浏览器的 fragment 不进入 HTTP 请求路径，也不会进入 Nginx 访问日志；页面换取 12 小时的 HttpOnly 管理会话后会移除 fragment。多个管理端可同时使用这条链接。

持有链接的人可以执行管理员操作，应只发给主持和工作人员。实际密码由部署脚本随机生成并保存在服务器，不在 GitHub 中设置默认密码。不要把真实链接写入公开文档、Issue 或截图。修改管理员密码会阻止旧链接再次登录，但不会立刻撤销已签发的管理会话；这些会话最长 12 小时到期，正常退出会在服务端撤销当前会话。轮换 `VOTE_SECRET_KEY` 会使旧管理签名失效，同时影响已有指纹关联，因此应由维护人员安排。现有有效的观众 token 和原始投票不会因为更换该密钥而被删除。

## 首次部署

### 1. DNS 和系统前提

将 `vote.billfan.cn` 的 A 记录指向已有服务器的公网 IPv4。只有服务器确实提供 IPv6 时才添加 AAAA 记录。公网 80/443 端口需要可访问；80 端口用于证书验证和跳转 HTTPS。

服务器需要 Linux + systemd、现有 Nginx、Python 3.10 或以上，以及 curl、flock、git、certbot 和 Python venv。Debian/Ubuntu 可按需安装缺失组件：

```bash
sudo apt-get update
sudo apt-get install -y python3-venv curl git certbot util-linux
```

服务器可以访问 Python 包源，以安装 `services/vote/requirements.txt` 中锁定的依赖：FastAPI 0.162.0、Starlette 1.7.0、Pydantic 2.14.3、Uvicorn 0.54.0。四个固定版本均声明支持 Python 3.10 或以上；安装时其余依赖由 pip 按实际解释器版本解析。脚本只建立投票服务专属虚拟环境，不升级主站的 Python 依赖。

### 2. 取得源码并安装

把仓库放在独立的源码目录。不要把现有 `/var/www` 初始化为 Git 仓库，也不要覆盖其中的运行数据。下列源码目录位于 `/root`，请先在服务器执行 `sudo -i` 进入 root shell，再运行：

```bash
mkdir -p /root/src
git clone https://github.com/ChenjianFan2000/billfan-web-stack.git /root/src/billfan-web-stack
cd /root/src/billfan-web-stack
bash scripts/deploy/deploy_vote.sh --email YOUR_EMAIL
```

将 `YOUR_EMAIL` 换成接收证书通知的邮箱。`--email` 可以省略，脚本会让 certbot 在未提供邮箱的情况下注册。

脚本执行以下步骤：

1. 检查现有 Nginx 配置并取得部署互斥锁。
2. 建立独立账户 `dankou-vote` 和运行目录；首次随机生成管理员密码及签名密钥。重复部署保留它们。
3. 将源码复制到新的版本目录，建立独立虚拟环境并安装依赖。
4. 使用 SQLite 在线备份 API 备份已有数据库，包含 WAL 中已经提交的数据；备份后保持数据库及 WAL/SHM 文件归专用服务账户所有。
5. 如无证书，暂时启用仅提供 ACME 验证的 HTTP 站点并申请 Let's Encrypt 证书。
6. 切换 `current` 符号链接，安装/重启 `dankou-vote` 服务，验证本机 API 健康。
7. 安装 HTTPS vhost，执行 `nginx -t`，通过后 reload Nginx，再验证页面和代理。

部署失败时，脚本恢复部署前的代码链接、投票站配置和服务状态。已有投票数据库与密码会保留，失败版本和诊断备份也会保留；不会通过恢复旧数据库覆盖部署期间新产生的投票。

### 3. 获取管理员地址

部署脚本不会把密码打印到安装日志。仅在可信终端执行：

```bash
sudo cat /etc/dankou-vote/admin-url.txt
```

用输出的地址打开管理端，录入选手并进行演练。

### 4. 验收

```bash
sudo bash scripts/deploy/verify_vote.sh
```

这个脚本只检查服务、静态路由、TLS、HTTP 跳转和凭证文件权限，并校验健康响应确实来自 `dankou-vote`，不会建立观众身份、投票或修改比赛状态。

使用至少两台手机和两个管理页面演练：开票、投票/取消、切后台返回、锁票时点击、断网重连、管理员同时操作、发送/删除弹幕、禁言/解禁，以及公布/隐藏结果。真正在现场使用前，还应按预计人数做压测；开发环境的通过结果不能代替服务器和场地网络的容量验证。

> GitHub 提交只更新仓库。这个仓库没有已配置的服务器自动发布流水线，GitHub 插件本身不能替代服务器上的安装命令。首次部署和后续更新仍需在有服务器权限的终端执行上述脚本；不要把“已推送 GitHub”当成“域名已上线”。

## 后续更新

仍在服务器的 root shell 中执行：

```bash
cd /root/src/billfan-web-stack
git pull --ff-only
bash scripts/deploy/deploy_vote.sh
bash scripts/deploy/verify_vote.sh
```

每次更新产生一个新版本目录，并保留上一个成功版本链接。投票状态在版本目录之外，更新不会清空选手、票数、观众身份、弹幕或审计数据。选择比赛间歇更新；重启期间流会短暂断开，客户端随后取得最新快照。

## 目录与配置

| 路径/资源 | 内容 |
| --- | --- |
| `/opt/dankou-vote/releases/<版本>/` | 当前版本完整代码和独立 `.venv` |
| `/opt/dankou-vote/current` | 当前运行版本的符号链接 |
| `/opt/dankou-vote/previous` | 上一次成功版本链接 |
| `/var/lib/dankou-vote/vote.sqlite3` | 持久 SQLite 数据库；同目录的 `-wal`、`-shm` 属正常运行文件 |
| `/etc/dankou-vote/vote.env` | 环境配置，root 可读 |
| `/etc/dankou-vote/admin-url.txt` | 明文管理员链接，root 可读 |
| `/var/backups/dankou-vote/<部署时间>/` | 部署前配置、上版路径及数据库一致性快照 |
| `/etc/nginx/conf.d/vote.billfan.cn.conf` | 投票域名的活动 Nginx 配置 |
| `/etc/systemd/system/dankou-vote.service` | 独立 systemd 服务 |
| `127.0.0.1:8020` | 仅本机可访问的应用端口 |

环境模板见 [`deploy/env/vote.env.example`](../../deploy/env/vote.env.example)。实际值由部署脚本在服务器生成。

| 环境变量 | 用途/默认值 |
| --- | --- |
| `VOTE_DB_PATH` | 生产安装固定为 `/var/lib/dankou-vote/vote.sqlite3` |
| `VOTE_ADMIN_PASSWORD` | 至少 16 字符，首次部署随机生成 |
| `VOTE_SECRET_KEY` | 至少 32 字符，持久保存 |
| `VOTE_COOKIE_SECURE` | 生产必须 `true`；仅本地 HTTP 测试可用 `false` |
| `VOTE_ALLOWED_ORIGINS` | `https://vote.billfan.cn`，多个来源用逗号分隔 |
| `VOTE_FINGERPRINT_RECOVERY` | `true`；可改为 `false` 禁用指纹兜底 |
| `VOTE_VOTE_INTERVAL_MS` | `800`，每位观众投票操作最小间隔 |
| `VOTE_MESSAGE_INTERVAL_MS` | `5000`，每位观众弹幕最小间隔 |
| `VOTE_MAX_CONNECTIONS` | `5000`，应用层 SSE 连接上限，不代表服务器已验证容量 |
| `VOTE_EVENT_TITLE` | 比赛标题，也可在管理端修改 |

修改生产配置后执行 `sudo systemctl restart dankou-vote`。正常部署不轮换密钥；更换密钥前应确认对观众身份和管理员会话的影响。

## 匿名身份和恢复

观众没有账号注册、手机号、密码或登录页。首次进入时服务器签发高熵 token，前端冗余保存在 localStorage、sessionStorage 和 IndexedDB，服务器同时设置 Cookie。再次进入时会把可用凭证交给服务器恢复原来的观众与所有投票记录。

前端还会把服务器返回的随机身份提示 `identityHint` 独立保存在上述存储的其他键中。当可用 token 全部丢失时，只有这个身份提示仍在、与原身份一致，且合格设备指纹匹配最近 30 天使用过的记录，才尝试自动恢复。身份提示本身不能单独登录。没有身份提示时，服务器绝不凭裸指纹合并身份，因此两台同型号的新手机即使产生相同指纹，也会分别获得自己的观众身份。

指纹来源是浏览器渲染与设备特征的哈希，在服务端再以本站密钥处理后保存，不以 IP 地址认定一个人；一场活动里多人共用 Wi-Fi 不会被按 IP 合并。

这些措施能覆盖常见的关闭页面、刷新、切后台和部分存储被清理，但浏览器不会提供不可清除的设备身份。清空全部数据会连同身份提示一起删除，更换浏览器、无痕模式、设备或隐私设置改变也可能使自动恢复失败。需要可靠恢复时，应预先保存页面提供的个人恢复入口；当前 token 和恢复凭证有效期为签发起 400 天。恢复凭证代表该观众身份，不应公开分享。

本方案按正常观众使用场景设计。它不是实名“一人一票”证明，也不能阻止恶意访客伪造指纹、清除凭证或使用多台设备。

## 锁票、同步和低吞吐策略

投票变更是“把我的选择设为已投/未投”的幂等操作。数据库对“观众 + 选手”保持唯一记录，重复网络请求不会增加多张票。客户端携带该选手的开票轮次 `epoch`；锁票或轮次变化时，服务器在同一事务中检查并拒绝过期请求。最终结果以服务器响应为准。

锁票在数据库提交后立即广播状态。正在显示页面的客户端尽快更新按钮；后台、断网或系统冻结的网页不能被服务器强制唤醒，返回后会先同步状态再允许操作。即使页面暂时还显示可投，服务器也不会接受锁票后的请求。这里的“精准”是服务端裁决精准，不是承诺所有手机同一毫秒重绘。

每个活动页面使用一条 SSE 长连接。普通弹幕按约 0.8 秒批量推送，计数按最多约 3 秒聚合推送，心跳约 25 秒；开票、锁票、切换选手、公布状态立即推送。客户端切到后台会暂停连接，返回时拉取快照；断线采用退避重连。慢客户端使用有界队列并重新同步，避免无限积压。

前端优先用 Fetch 流读取 SSE；不能读取 Fetch 流时改用同源 Cookie 鉴权的原生 `EventSource`。这些长连接方式不可用时才降级为约 14–17 秒一次的快照轮询。轮询模式会显示同步状态，锁票按钮的外观可能延后刷新，但服务器仍立即拒绝已经锁票的请求。实现面向现代手机浏览器，不能据此宣称适配所有历史浏览器版本。

Nginx 对 `/api/` 关闭响应缓冲、代理缓存、gzip 和访问日志。应用不逐条打印访问请求。未对公网 IP 做低额度限流，以免场地共享网络误伤全体观众。投票和弹幕频率在服务器按观众身份控制。

部署模板固定单 worker。SSE 广播器和订阅关系在进程内；不要直接改为多个 uvicorn worker 或启动多个副本。需要水平扩容时，应先引入共享广播通道与跨进程协调，再做容量测试。

实际容量与 CPU、SQLite 写入延迟、网络带宽、代理连接上限以及弹幕频率相关，不能仅从实现方式给出可靠的“可容纳人数”。每条经过 Nginx 的 SSE 会分别占用面向观众和面向后端的连接；现有 Nginx 的全局连接限额还要供其他站点使用，部署脚本不会自行提高这些全站参数。首场前按预计观众数量测量锁票延迟、写入延迟和重连峰值，再调整频率。

## 票数调整与审计

观众原始票和管理员调整分开记录。公开调整必须提供理由，公布票数时同时展示公开调整量及理由。隐藏调整会影响公布总数，但不会在观众接口中暴露隐藏调整记录、理由或原始票数；后台仍保留审计记录。

显示总票数为 `max(0, 原始票数 + 调整总数)`。新负调整不能直接把当前总数降到负数；之后观众取消投票仍然允许，显示总数按零封底。管理员应在锁票后处理最终裁定，避免边投边调导致理解偏差。

多个管理员修改比赛设置使用 revision 乐观并发检查。一方先完成后，另一方的过期操作会提示重新确认，避免后到的旧页面覆盖最新状态。

## 备份、回滚和故障处理

### 定期备份

SQLite 使用 WAL。运行中不要只复制 `.sqlite3` 主文件，因为已提交内容可能仍在 WAL 中。部署脚本已使用在线备份 API；手动备份也可使用相同方式：

```bash
sudo install -d -m 0700 /var/backups/dankou-vote/manual
sudo python3 - <<'PY'
import datetime, os, pwd, sqlite3
from contextlib import closing
from pathlib import Path
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
target = f'/var/backups/dankou-vote/manual/vote-{stamp}.sqlite3'
owner = pwd.getpwnam('dankou-vote')
source = Path('/var/lib/dankou-vote/vote.sqlite3')
try:
    with closing(sqlite3.connect(f'file:{source}?mode=ro', uri=True)) as src:
        with closing(sqlite3.connect(target)) as dst:
            src.backup(dst)
finally:
    for suffix in ('-wal', '-shm'):
        path = Path(str(source) + suffix)
        if path.exists() and path.is_file() and not path.is_symlink():
            os.chown(path, owner.pw_uid, owner.pw_gid, follow_symlinks=False)
print(target)
PY
```

数据库备份和 `/etc/dankou-vote/vote.env` 应存入受限备份位置，不要提交仓库。恢复数据库会覆盖较新投票，必须先停服务并保留当时数据库；不要在正在投票时自动恢复旧快照。

### 回退代码

先确认目标版本兼容当前数据库结构。首次版本的更新没有破坏式迁移，但今后的跨版本回退仍需要评估。

```bash
sudo readlink -f /opt/dankou-vote/previous
```

确认目标后，用该完整版本路径替换下例 `PREVIOUS_RELEASE_PATH`：

```bash
sudo ln -s PREVIOUS_RELEASE_PATH /opt/dankou-vote/current.next
sudo mv -Tf /opt/dankou-vote/current.next /opt/dankou-vote/current
sudo systemctl restart dankou-vote
sudo bash scripts/deploy/verify_vote.sh
```

这只回退代码，不把旧数据库覆盖回去。需要恢复配置时，参照对应 `/var/backups/dankou-vote/<时间>/`；替换 Nginx 配置后先 `nginx -t`，通过才 reload。

### 检查状态与日志

```bash
sudo systemctl status dankou-vote --no-pager
sudo journalctl -u dankou-vote -n 100 --no-pager
sudo tail -n 100 /var/log/nginx/dankou-vote.error.log
curl -fsS http://127.0.0.1:8020/api/health
```

首次申请证书失败时，优先检查 DNS、错误的 AAAA 记录、防火墙以及 80 端口。服务健康但同步延迟大时，检查是否经过额外 CDN/反向代理及其 SSE 缓冲和超时设置。

### 证书续期

确认 certbot 的续期 timer 或既有 cron 已启用。证书续期成功后需要 reload Nginx：

```bash
sudo systemctl list-timers --all certbot.timer
sudo certbot renew --dry-run
```

若服务器尚无续期后 reload 的 hook，可创建一个仅响应本域名的脚本：

```bash
sudo install -d -m 0755 /etc/letsencrypt/renewal-hooks/deploy
sudo tee /etc/letsencrypt/renewal-hooks/deploy/dankou-vote-nginx > /dev/null <<'SH'
#!/usr/bin/env sh
case " $RENEWED_DOMAINS " in
  *" vote.billfan.cn "*) nginx -t && systemctl reload nginx ;;
esac
SH
sudo chmod 0755 /etc/letsencrypt/renewal-hooks/deploy/dankou-vote-nginx
```

## 本地开发与验证

本次开发环境缺少 `sites-previewd`，浏览器预览无法启动，因此尚未完成真实浏览器视觉检查和手机实机验收。固定依赖组合已通过接口自动化测试和 Python 3.10 的依赖解析检查；测试实际运行在 Python 3.12 环境，不将其表述为已在 Python 3.10 主机实测。部署脚本还需在目标主机执行 `nginx -t`、systemd 和 HTTPS 验收。上线前应补齐上文的多手机现场演练。

以下仅在开发目录运行，不要把测试数据库指向生产路径：

```bash
python3 -m venv .venv-vote
.venv-vote/bin/pip install -r services/vote/requirements.txt pytest httpx
VOTE_DB_PATH=/tmp/dankou-vote-dev.sqlite3 \
VOTE_ADMIN_PASSWORD=local-development-password \
VOTE_SECRET_KEY=local-development-secret-change-before-production \
VOTE_COOKIE_SECURE=false \
VOTE_ALLOWED_ORIGINS=http://localhost:8020,http://127.0.0.1:8020 \
.venv-vote/bin/python -m uvicorn services.vote.app:app --host 127.0.0.1 --port 8020 --workers 1
```

测试与脚本语法检查：

```bash
.venv-vote/bin/python -m pytest tests/test_vote.py -q
node --test tests/vote_client.test.mjs
bash -n scripts/deploy/deploy_vote.sh scripts/deploy/verify_vote.sh
```

Node 命令运行前端状态与同步测试，目前 12 项通过，包含晚到的发送响应不会恢复已删除弹幕、旧快照不会覆盖更新弹幕的检查。

另有 7 项非视觉 DOM 集成测试，加载实际 HTML 和 ES modules，并模拟 Fetch API 与 SSE。使用 JSDOM 31.0.0，在仓库根目录执行：

```bash
cd tests/vote-dom && npm ci && npm test
```

DOM 测试要求 Node 满足 `^22.22.2 || ^24.15.0 || >=26.0.0`，与该目录 `package.json` 的 `engines` 一致；本次使用 Node 24.22.1。生产服务器仅提供原生静态文件，无需安装或运行 Node、npm 或 JSDOM。

当前通过后端接口测试 21 项、前端状态测试 12 项、DOM 集成测试 7 项，共 40 项。DOM 验证使用模拟接口与消息流，不代替真实浏览器的布局、点击、手机兼容性检查或目标服务器的生产集成验收。

接口字段、错误码与 SSE 事件见 [`API.md`](API.md)。
