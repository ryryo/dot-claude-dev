import { NextResponse } from "next/server"

import {
  verifyPassword,
  createSessionCookie,
  COOKIE_NAME,
  MAX_AGE,
} from "@/lib/auth"

export async function POST(request: Request) {
  const { password } = (await request.json()) as { password: string }

  if (!verifyPassword(password)) {
    return NextResponse.json(
      { error: "パスワードが正しくありません" },
      { status: 401 },
    )
  }

  const cookie = await createSessionCookie()
  const isProduction = process.env.NODE_ENV === "production"
  const cookieValue = `${COOKIE_NAME}=${cookie}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${MAX_AGE}${isProduction ? "; Secure" : ""}`

  const response = NextResponse.json({ ok: true })
  response.headers.set("Set-Cookie", cookieValue)
  return response
}
