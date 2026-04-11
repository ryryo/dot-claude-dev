import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

describe("auth", () => {
  const originalPassword = process.env.DASHBOARD_PASSWORD
  const originalCookieSecret = process.env.DASHBOARD_COOKIE_SECRET

  beforeEach(() => {
    vi.resetModules()
    vi.restoreAllMocks()
    process.env.DASHBOARD_PASSWORD = "shared-pass"
    process.env.DASHBOARD_COOKIE_SECRET = "cookie-secret-a"
    vi.spyOn(Date, "now").mockReturnValue(1_775_905_853_153)
  })

  afterEach(() => {
    if (originalPassword === undefined) {
      delete process.env.DASHBOARD_PASSWORD
    } else {
      process.env.DASHBOARD_PASSWORD = originalPassword
    }

    if (originalCookieSecret === undefined) {
      delete process.env.DASHBOARD_COOKIE_SECRET
    } else {
      process.env.DASHBOARD_COOKIE_SECRET = originalCookieSecret
    }
  })

  it("cookie secret が変わると同じ timestamp でも署名が変わる", async () => {
    const auth = await import("../lib/auth")

    const first = await auth.createSessionCookie()

    process.env.DASHBOARD_COOKIE_SECRET = "cookie-secret-b"
    vi.resetModules()
    const changedAuth = await import("../lib/auth")

    const second = await changedAuth.createSessionCookie()

    expect(first).not.toBe(second)
    await expect(changedAuth.verifySessionCookie(first)).resolves.toBe(false)
  })

  it("cookie secret が未設定ならセッション生成は失敗し、検証は false を返す", async () => {
    const auth = await import("../lib/auth")
    delete process.env.DASHBOARD_COOKIE_SECRET
    vi.resetModules()

    const withoutSecret = await import("../lib/auth")

    await expect(withoutSecret.createSessionCookie()).rejects.toThrow(
      "DASHBOARD_COOKIE_SECRET is not set",
    )
    await expect(withoutSecret.verifySessionCookie("123.invalid")).resolves.toBe(false)
    expect(withoutSecret.verifyPassword("shared-pass")).toBe(true)
    expect(auth.verifyPassword("shared-pass")).toBe(true)
  })
})
