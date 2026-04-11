import { afterEach, describe, expect, it } from "vitest"

import {
  clearFailures,
  getClientKey,
  getRateLimitState,
  RATE_LIMIT_BLOCK_MS,
  RATE_LIMIT_MAX_FAILURES,
  RATE_LIMIT_WINDOW_MS,
  recordFailure,
  resetRateLimitStore,
} from "../lib/login-rate-limit"

describe("login-rate-limit", () => {
  afterEach(() => {
    resetRateLimitStore()
  })

  it("x-forwarded-for の先頭 IP を client key に使う", () => {
    const headers = new Headers({
      "x-forwarded-for": "203.0.113.10, 10.0.0.1",
      "user-agent": "test-agent",
    })

    expect(getClientKey(headers)).toBe("ip:203.0.113.10")
  })

  it("window 内で最大失敗回数に達すると block される", () => {
    const clientKey = "ip:203.0.113.20"
    const now = 1_700_000_000_000

    for (let i = 0; i < RATE_LIMIT_MAX_FAILURES - 1; i++) {
      const state = recordFailure(clientKey, now + i * 1000)
      expect(state.blocked).toBe(false)
    }

    const blocked = recordFailure(clientKey, now + RATE_LIMIT_MAX_FAILURES * 1000)

    expect(blocked.blocked).toBe(true)
    expect(blocked.retryAfter).toBeGreaterThan(0)
    expect(getRateLimitState(clientKey, now + RATE_LIMIT_MAX_FAILURES * 1000).blocked).toBe(true)
  })

  it("window を超えると失敗回数がリセットされる", () => {
    const clientKey = "ip:203.0.113.30"
    const now = 1_700_000_000_000

    recordFailure(clientKey, now)
    recordFailure(clientKey, now + 1000)

    const resetState = recordFailure(clientKey, now + RATE_LIMIT_WINDOW_MS + 1000)

    expect(resetState.blocked).toBe(false)
    expect(resetState.failures).toBe(1)
    expect(resetState.remaining).toBe(RATE_LIMIT_MAX_FAILURES - 1)
  })

  it("成功時に state をクリアできる", () => {
    const clientKey = "ua:test-agent"
    const now = 1_700_000_000_000

    recordFailure(clientKey, now)
    recordFailure(clientKey, now + 1000)

    clearFailures(clientKey)

    expect(getRateLimitState(clientKey, now + 2000)).toEqual({
      blocked: false,
      retryAfter: 0,
      failures: 0,
      remaining: RATE_LIMIT_MAX_FAILURES,
    })
  })

  it("block 期間を過ぎると再試行できる", () => {
    const clientKey = "ip:203.0.113.40"
    const now = 1_700_000_000_000

    for (let i = 0; i < RATE_LIMIT_MAX_FAILURES; i++) {
      recordFailure(clientKey, now + i * 1000)
    }

    const recovered = getRateLimitState(clientKey, now + RATE_LIMIT_BLOCK_MS + 1000)

    expect(recovered.blocked).toBe(false)
    expect(recovered.failures).toBe(0)
  })
})
