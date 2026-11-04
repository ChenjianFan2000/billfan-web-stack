import { useEffect, useState } from "react"
import { login, listUsers } from "../api/paperAssistant"
import { Spinner } from "../components/ui/Spinner"

type Props = {
  onLoggedIn: () => void
}

export function LoginPage({ onLoggedIn }: Props) {
  const [users, setUsers] = useState<Array<{ username: string }>>([])
  const [selectedUser, setSelectedUser] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const [loadingUsers, setLoadingUsers] = useState(true)

  useEffect(() => {
    listUsers()
      .then(setUsers)
      .catch(() => setError("加载用户失败"))
      .finally(() => setLoadingUsers(false))
  }, [])

  return (
    <main className="flex min-h-screen items-center justify-center bg-bg p-4">
      <div className="w-full max-w-xl rounded-2xl border border-slate-700/60 bg-panel p-6 shadow-panel">
        <h1 className="mb-2 text-2xl font-semibold text-cyan">其华的论文管理小助手</h1>
        <p className="mb-4 text-sm text-slate-400">请选择用户并输入密码进入系统。</p>

        {loadingUsers ? (
          <div className="mb-4 rounded border border-slate-700/50 bg-slate-900/70 p-3 text-sm text-slate-300">
            <span className="inline-flex items-center gap-2">
              <Spinner />
              正在加载用户列表...
            </span>
          </div>
        ) : null}

        <div className="mb-4 grid gap-2 sm:grid-cols-2">
          {users.map((user) => (
            <button
              key={user.username}
              className={`rounded-xl border px-4 py-3 text-left transition ${
                selectedUser === user.username
                  ? "border-cyan bg-cyan/10 text-cyan"
                  : "border-slate-700 bg-slate-900/50 text-slate-200 hover:border-slate-500"
              }`}
              disabled={busy}
              onClick={() => {
                setSelectedUser(user.username)
                setError("")
              }}
              type="button"
            >
              <div className="text-sm">{user.username}</div>
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            className="flex-1 rounded-lg border border-slate-600 bg-slate-950 px-3 py-2 text-sm"
            disabled={busy}
            onChange={(event) => setPassword(event.target.value)}
            placeholder={selectedUser ? `请输入 ${selectedUser} 的密码` : "请先选择用户"}
            type="password"
            value={password}
          />
          <button
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan/20 px-4 py-2 text-sm text-cyan hover:bg-cyan/30 disabled:cursor-not-allowed disabled:opacity-40"
            disabled={!selectedUser || !password || busy}
            onClick={async () => {
              if (!selectedUser) {
                return
              }
              setBusy(true)
              setError("")
              try {
                await login(selectedUser, password)
                onLoggedIn()
              } catch {
                setError("登录失败，请检查密码")
              } finally {
                setBusy(false)
              }
            }}
            type="button"
          >
            {busy ? <Spinner /> : null}
            登录
          </button>
        </div>

        {error ? <p className="mt-3 text-sm text-red-400">{error}</p> : null}
      </div>
    </main>
  )
}
