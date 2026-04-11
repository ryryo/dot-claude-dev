const WINDOW_MS = 10 * 60 * 1000
const BLOCK_MS = 15 * 60 * 1000
const MAX_FAILURES = 5

interface AttemptState {
  failures: number
  firstFailureAt: number
  blockedUntil: number | null
}

export interface RateLimitState {
  blocked: boolean
  retryAfter: number
  failures: number
  remaining: number
}

const attempts = new Map<string, AttemptState>()

function normalizeState(state: AttemptState | undefined, now: number): AttemptState | undefined {
  if (!state) {
    return undefined
  }

  if (state.blockedUntil !== null && state.blockedUntil <= now) {
    return undefined
  }

  if (now - state.firstFailureAt >= WINDOW_MS) {
    return {
      failures: 0,
      firstFailureAt: now,
      blockedUntil: null,
    }
  }

  return state
}

function getEmptyState(): RateLimitState {
  return {
    blocked: false,
    retryAfter: 0,
    failures: 0,
    remaining: MAX_FAILURES,
  }
}

export function getClientKey(headers: Pick<Headers, "get">): string {
  const forwardedFor = headers.get("x-forwarded-for")

  if (forwardedFor) {
    const first = forwardedFor.split(",")[0]?.trim()
    if (first) {
      return `ip:${first}`
    }
  }

  const userAgent = headers.get("user-agent")?.trim()
  if (userAgent) {
    return `ua:${userAgent}`
  }

  return "unknown"
}

export function getRateLimitState(clientKey: string, now = Date.now()): RateLimitState {
  const rawState = attempts.get(clientKey)
  const state = normalizeState(rawState, now)

  if (!state || state.failures === 0) {
    attempts.delete(clientKey)
    return getEmptyState()
  }

  attempts.set(clientKey, state)

  const retryAfter = state.blockedUntil === null ? 0 : Math.max(0, Math.ceil((state.blockedUntil - now) / 1000))

  return {
    blocked: state.blockedUntil !== null && state.blockedUntil > now,
    retryAfter,
    failures: state.failures,
    remaining: Math.max(0, MAX_FAILURES - state.failures),
  }
}

export function recordFailure(clientKey: string, now = Date.now()): RateLimitState {
  const current = normalizeState(attempts.get(clientKey), now)

  const next: AttemptState = current
    ? {
        failures: current.failures + 1,
        firstFailureAt: current.failures === 0 ? now : current.firstFailureAt,
        blockedUntil: null,
      }
    : {
        failures: 1,
        firstFailureAt: now,
        blockedUntil: null,
      }

  if (next.failures >= MAX_FAILURES) {
    next.blockedUntil = now + BLOCK_MS
  }

  attempts.set(clientKey, next)
  return getRateLimitState(clientKey, now)
}

export function clearFailures(clientKey: string): void {
  attempts.delete(clientKey)
}

export function resetRateLimitStore(): void {
  attempts.clear()
}

export const RATE_LIMIT_WINDOW_MS = WINDOW_MS
export const RATE_LIMIT_BLOCK_MS = BLOCK_MS
export const RATE_LIMIT_MAX_FAILURES = MAX_FAILURES
