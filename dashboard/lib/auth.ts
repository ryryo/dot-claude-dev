export const COOKIE_NAME = "dashboard-session"
export const MAX_AGE = 7 * 24 * 60 * 60

const encoder = new TextEncoder()

async function deriveSecret(): Promise<ArrayBuffer> {
  const password = process.env.DASHBOARD_PASSWORD

  if (!password) {
    throw new Error("DASHBOARD_PASSWORD is not set")
  }

  const data = encoder.encode(`cookie-secret:${password}`)
  return crypto.subtle.digest("SHA-256", data)
}

async function createSignature(timestamp: string): Promise<string> {
  const secret = await deriveSecret()
  const key = await crypto.subtle.importKey(
    "raw",
    secret,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  )
  const sig = await crypto.subtle.sign("HMAC", key, encoder.encode(timestamp))
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
}

function timingSafeEqual(a: string, b: string): boolean {
  const bufA = encoder.encode(a)
  const bufB = encoder.encode(b)
  const len = Math.max(bufA.length, bufB.length)
  let result = bufA.length ^ bufB.length
  for (let i = 0; i < len; i++) {
    result |= (bufA[i] ?? 0) ^ (bufB[i] ?? 0)
  }
  return result === 0
}

export async function createSessionCookie(): Promise<string> {
  const timestamp = Date.now().toString()
  const signature = await createSignature(timestamp)
  return `${timestamp}.${signature}`
}

export async function verifySessionCookie(value: string): Promise<boolean> {
  const parts = value.split(".")

  if (parts.length !== 2) {
    return false
  }

  const [timestamp, signature] = parts

  if (!/^\d+$/.test(timestamp)) {
    return false
  }

  const issuedAt = Number(timestamp)

  if (!Number.isSafeInteger(issuedAt)) {
    return false
  }

  const age = Date.now() - issuedAt

  if (age < 0 || age > MAX_AGE * 1000) {
    return false
  }

  try {
    const expected = await createSignature(timestamp)
    return timingSafeEqual(signature, expected)
  } catch {
    return false
  }
}

export function verifyPassword(input: string): boolean {
  const password = process.env.DASHBOARD_PASSWORD

  if (!password) {
    timingSafeEqual(input, "")
    return false
  }

  return timingSafeEqual(input, password)
}
