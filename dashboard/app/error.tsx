"use client"

import { useEffect } from "react"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <main className="flex h-svh items-center justify-center p-6">
      <div className="max-w-md space-y-4 text-center">
        <h1 className="text-heading-2">エラーが発生しました</h1>
        <p className="text-body text-muted-foreground">
          {error.message || "予期しないエラーが発生しました。"}
        </p>
        <button
          onClick={reset}
          className="rounded-full bg-[var(--cta)] px-6 py-2.5 text-label text-[var(--cta-foreground)] transition-opacity hover:opacity-90"
        >
          再読み込み
        </button>
      </div>
    </main>
  )
}
