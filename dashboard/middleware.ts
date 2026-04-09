import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

import { verifySessionCookie, COOKIE_NAME } from "@/lib/auth"

export async function middleware(request: NextRequest) {
  const cookie = request.cookies.get(COOKIE_NAME)?.value

  if (cookie && (await verifySessionCookie(cookie))) {
    return NextResponse.next()
  }

  return NextResponse.redirect(new URL("/login", request.url))
}

export const config = {
  matcher: ["/((?!login|api/auth|_next|favicon.ico).*)"],
}
