import { useEffect, useState } from "react"
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom"
import { me } from "./api/paperAssistant"
import { Spinner } from "./components/ui/Spinner"
import { LoginPage } from "./pages/LoginPage"
import { AppPage } from "./pages/AppPage"

type SessionState =
  | { loading: true; username: string }
  | { loading: false; username: string; authenticated: boolean }

function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg text-sm text-slate-300">
      <span className="inline-flex items-center gap-2 rounded border border-slate-700/50 bg-slate-900/70 px-3 py-2">
        <Spinner />
        正在检查登录状态...
      </span>
    </div>
  )
}

function resolveAimathRedirect(): string | null {
  const host = window.location.hostname.toLowerCase()
  if (host === "aimath.billfan.cn") {
    return "/aimath/"
  }

  const referrer = document.referrer.toLowerCase()
  if ((host === "billfan.cn" || host === "www.billfan.cn") && referrer.includes("://aimath.billfan.cn")) {
    return "https://aimath.billfan.cn/aimath/"
  }

  return null
}

export default function App() {
  const [session, setSession] = useState<SessionState>({ loading: true, username: "" })
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const redirect = resolveAimathRedirect()
    if (redirect && window.location.pathname !== "/aimath/") {
      window.location.replace(redirect)
    }
  }, [])

  const checkSession = async () => {
    try {
      const user = await me()
      setSession({ loading: false, username: user.username, authenticated: true })
      return true
    } catch {
      setSession({ loading: false, username: "", authenticated: false })
      return false
    }
  }

  useEffect(() => {
    checkSession().catch(() => undefined)
  }, [])

  useEffect(() => {
    if (session.loading) {
      return
    }
    if (session.authenticated && location.pathname === "/login") {
      navigate("/app", { replace: true })
    }
    if (!session.authenticated && location.pathname.startsWith("/app")) {
      navigate("/login", { replace: true })
    }
  }, [location.pathname, navigate, session])

  if (session.loading) {
    return <LoadingScreen />
  }

  return (
    <Routes>
      <Route
        element={
          session.authenticated ? (
            <Navigate replace to="/app" />
          ) : (
            <LoginPage
              onLoggedIn={() => {
                checkSession()
                  .then(() => navigate("/app", { replace: true }))
                  .catch(() => undefined)
              }}
            />
          )
        }
        path="/login"
      />

      <Route
        element={
          session.authenticated ? (
            <AppPage
              onLoggedOut={() => {
                setSession({ loading: false, username: "", authenticated: false })
                navigate("/login", { replace: true })
              }}
              username={session.username}
            />
          ) : (
            <Navigate replace to="/login" />
          )
        }
        path="/app"
      />

      <Route element={<Navigate replace to={session.authenticated ? "/app" : "/login"} />} path="*" />
    </Routes>
  )
}
