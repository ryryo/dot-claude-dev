"use client"

import { type FormEvent, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

export default function LoginPage() {
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError("")
    setLoading(true)

    try {
      const response = await fetch("/api/auth", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password }),
      })

      if (response.ok) {
        window.location.href = "/"
        return
      }

      if (response.status === 429) {
        const body = (await response.json().catch(() => null)) as { retryAfter?: number } | null
        const retryAfter = typeof body?.retryAfter === "number" ? body.retryAfter : null
        setError(
          retryAfter
            ? `試行回数が多すぎます。${Math.max(1, Math.ceil(retryAfter / 60))}分ほど待ってから再試行してください。`
            : "試行回数が多すぎます。しばらく待ってから再試行してください。"
        )
        return
      }

      setError("パスワードが正しくありません")
    } catch {
      setError("パスワードが正しくありません")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-svh items-center justify-center bg-muted/30 px-6">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-2 text-center">
          <CardTitle className="text-heading-2">PLAN Dashboard</CardTitle>
          <CardDescription>
            ダッシュボードを表示するにはパスワードを入力してください。
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label htmlFor="password" className="text-label text-foreground">
                パスワード
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                disabled={loading}
                aria-invalid={Boolean(error)}
                aria-describedby="login-error"
              />
            </div>

            <p
              id="login-error"
              aria-live="polite"
              className={cn(
                "min-h-5 text-sm text-destructive",
                !error && "text-muted-foreground/0"
              )}
            >
              {error || " "}
            </p>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "ログイン中..." : "ログイン"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  )
}
