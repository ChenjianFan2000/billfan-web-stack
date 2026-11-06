# 投票接口与同步契约

独立进程：`uvicorn services.vote.app:app --host 127.0.0.1 --port 8020 --workers 1`。
所有时间为 Unix 毫秒，字段采用 camelCase。写入请求必须使用 JSON。同源 Cookie 与
`Authorization: Bearer <token>` 均可鉴别观众；管理员使用独立 HttpOnly Cookie。

## 观众

- `POST /api/session`：`{tokens?: string[], fingerprint?: "64位小写hex", fingerprintVersion?: "v1", fingerprintQualified?: boolean, identityHint?: string, recoveryCode?: string}`。优先使用显式恢复码，再检查冗余 tokens 与 Cookie；全部失效时，只有独立冗余保存的 `identityHint`（此前返回的 userId）与合格指纹同时匹配，才恢复原身份；否则建立新观众。绝不凭裸指纹自动合并两位新观众。
  返回 `{token,userId,recoveryCode,restored,snapshot}`。`recoveryCode` 是高熵恢复凭证，应只保存在本机或用户自行保存的恢复链接，不发送给其他人。
- `GET /api/snapshot`：返回下述快照。
- `PUT /api/votes/{contestantId}`：`{voted:boolean,epoch:number,requestId:string}`；每次操作生成新的 requestId，网络重试沿用同一个。返回 `{voted,contestantId,me,revision,replayed?}`。
- `POST /api/messages`：`{text:string,requestId:string}`；返回 `{message,replayed?}`。
- `GET /api/events`：SSE，可使用带 Bearer 的 fetch 流式读取。每次连接先发送 `snapshot`，随后按需发送 `state`、`counts`、`messages` (`{messages:[...]}`)、`message_deleted` (`{id}`)、`me`、`heartbeat` (`{serverTime}`)。`resync` 表示慢客户端或凭证过期，重新建立会话/快照和连接。断线期间以重新取得的快照为准，不重放所有历史弹幕。

```json
{
  "revision": 3,
  "streamId": "每次启动改变的随机标识",
  "serverTime": 1793952000000,
  "title": "旦口喜剧大赛",
  "currentId": "选手ID或null",
  "contestants": [{
    "id": "...", "name": "...", "group": "...", "order": 0,
    "status": "upcoming|performing|performed",
    "voting": "pending|open|locked", "epoch": 1,
    "published": false, "votes": null,
    "adjustments": [{"id":"...","delta":1,"reason":"...","createdAt":0}]
  }],
  "messages": [{"id":"...","text":"...","highlight":false,"createdAt":0}],
  "limits": {"voteMs":800,"messageMs":5000,"maxMessageLength":80},
  "me": {"id":"...","votes":["选手ID"],"bannedUntil":0,"version":1}
}
```

`state` 与快照结构相同但不含 `me`，绝不把一位观众的投票状态广播给其他人。
票数隐藏时 `votes=null`、`adjustments=[]`；公布后只暴露公开调整理由，隐藏调整和原始票数仅管理员可见。
已公布计数最多每 3 秒以紧凑 `counts` 增量推送：
`{revision,streamId,serverTime,counts:[{id,votes}]}`，仅包含已公布选手。
客户端仅对同 streamId、同 revision、更新 serverTime 的计数增量生效；否则等待完整状态或重连。
开票、锁票、切换和公布等所有管理操作立即推送完整状态，不能被旧快照覆盖。
锁票最终由事务内的状态与 epoch 裁决，网页的显示时间不能作为成功依据。
切换选手默认不锁上一位，所有 `voting=open` 的选手均可继续修改。

## 管理员

- `POST /api/admin/session`：`{password:string}`，成功设置 12 小时 HttpOnly Cookie 并返回 `{ok:true,state}`。
- `POST /api/admin/logout`：`{}`，清除管理员 Cookie。
- `GET /api/admin/state`：管理员快照。
- `GET /api/admin/events`：初始及更新为 `admin_state`，还有 `heartbeat` / `resync`。完整状态里每位选手附 `rawVotes`、`adjustmentTotal`，所有调整附 `public`，消息附 `userId`、`deleted`；`audit` 为最近 100 条操作记录。
- `GET /api/admin/export`：CSV 结果导出。
- `POST /api/admin/action`：所有操作携带 `{action,expectedRevision,requestId,...}`。成功返回 `{ok:true,state,replayed?}`。普通投票不递增 revision，因此同一 revision 的计数更新也应接收。

| action | 参数 |
| --- | --- |
| `upsert_contestant` | `contestant:{id?:string,name,group,order?:number}` |
| `import_contestants` | `contestants:[{name,group,order?:number}]`，只追加 |
| `remove_contestant` | `contestantId`，只允许无投票/调整记录、非当前的选手 |
| `select` | `contestantId`，可加 `lockPrevious:true`；上一位标记已演出 |
| `open` / `lock` | `contestantId` |
| `lock_all` | 无 |
| `set_status` | `contestantId,status` (`upcoming/performing/performed`) |
| `publish` | `contestantIds:string[],visible:boolean` |
| `adjust` | `contestantId,delta:integer,reason:string,public:boolean`；公开必须提供理由 |
| `message` | `text,highlight?:boolean`，默认醒目 |
| `delete_message` | `messageId` |
| `ban` | `userId,seconds`，0 为解禁，最多 7 天 |
| `settings` | `title` |

修改票数不会更改任何观众的原始投票。显示总数为 `max(0, 原始票数 + 调整总数)`，
因此观众后续取消投票仍然允许，总数不会成为负数；新增负调整不能直接造成负数。
所有调整，包括隐藏调整，都保留管理员审计记录。

## 错误

统一返回 `{error:{code,message,retryAfterMs?}}`。
`409 revision_conflict` 另带当前管理员 `state`，请刷新并由管理员重新确认操作。
`409 vote_locked`、`409 stale_epoch` 返回当前公共 `state`；禁止客户端把该请求当作投票成功。
`429 rate_limited` 带 `Retry-After` 及 `retryAfterMs`。同一 requestId 的成功重试不再次写票或改票；
同一 requestId 换用其他内容返回 `409 request_id_conflict`。

## 运行配置

`VOTE_DB_PATH`（默认 `data/vote.sqlite3`）、`VOTE_ADMIN_PASSWORD`（至少 16 字符）、
`VOTE_SECRET_KEY`（至少 32 字符）、`VOTE_COOKIE_SECURE`（默认 true）、
`VOTE_ALLOWED_ORIGINS`（默认 `https://vote.billfan.cn`，逗号分隔）、
`VOTE_FINGERPRINT_RECOVERY`（默认 true）、`VOTE_VOTE_INTERVAL_MS`（默认 800）、
`VOTE_MESSAGE_INTERVAL_MS`（默认 5000）、`VOTE_EVENT_TITLE`。

数据库使用 WAL；单进程锁可阻止误开多个 worker。数据和密钥必须持久保存。
指纹只能辅助恢复：同型号设备可能碰撞，因此没有 identityHint 时不会按指纹合并身份。
跨浏览器、无痕模式和清空全部存储无法保证自动恢复，需要使用用户已保存的恢复链接。
可关闭指纹兜底；正常 token 和恢复码仍可使用。
