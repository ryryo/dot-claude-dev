import { NextResponse } from "next/server"

import {
  verifyPassword,
  createSessionCookie,
  COOKIE_NAME,
  MAX_AGE,
} from "@/lib/auth"
import {
  clearFailures,
  getClientKey,
  getRateLimitState,
  recordFailure,
} from "@/lib/login-rate-limit"

export async function POST(request: Request) {
  const clientKey = getClientKey(request.headers)
  const rateLimitState = getRateLimitState(clientKey)

  if (rateLimitState.blocked) {
    return NextResponse.json(
      {
        error: "試行回数が多すぎます。しばらく待ってから再試行してください。",
        retryAfter: rateLimitState.retryAfter,
      },
      {
        status: 429,
        headers: {
          "Retry-After": String(rateLimitState.retryAfter),
        },
      },
    )
  }

  let password: string
  try {
    const body = await request.json()
    password = typeof body?.password === "string" ? body.password : ""
  } catch {
    return NextResponse.json({ error: "不正なリクエストです" }, { status: 400 })
  }

  if (!verifyPassword(password)) {
    const failedState = recordFailure(clientKey)

    if (failedState.blocked) {
      return NextResponse.json(
        {
          error: "試行回数が多すぎます。しばらく待ってから再試行してください。",
          retryAfter: failedState.retryAfter,
        },
        {
          status: 429,
          headers: {
            "Retry-After": String(failedState.retryAfter),
          },
        },
      )
    }

    return NextResponse.json(
      { error: "パスワードが正しくありません" },
      { status: 401 },
    )
  }

  clearFailures(clientKey)

  const cookie = await createSessionCookie()
  const isProduction = process.env.NODE_ENV === "production"
  const cookieValue = `${COOKIE_NAME}=${cookie}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${MAX_AGE}${isProduction ? "; Secure" : ""}`

  const response = NextResponse.json({ ok: true })
  response.headers.set("Set-Cookie", cookieValue)
  return response
}
