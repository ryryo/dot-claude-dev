import { createHmac, timingSafeEqual, createHash } from "node:crypto"

export const COOKIE_NAME = "dashboard-session"
export const MAX_AGE = 7 * 24 * 60 * 60

function getSecret() {
  const password = process.env.DASHBOARD_PASSWORD

  if (!password) {
    throw new Error("DASHBOARD_PASSWORD is not set")
  }

  return createHash("sha256").update(`cookie-secret:${password}`).digest()
}

function createSignature(timestamp: string) {
  return createHmac("sha256", getSecret()).update(timestamp).digest("hex")
}

function safeEqual(left: string, right: string) {
  const leftBuffer = Buffer.from(left)
  const rightBuffer = Buffer.from(right)
  const bufferLength = Math.max(leftBuffer.length, rightBuffer.length, 1)
  const paddedLeft = Buffer.alloc(bufferLength)
  const paddedRight = Buffer.alloc(bufferLength)

  leftBuffer.copy(paddedLeft)
  rightBuffer.copy(paddedRight)

  const valuesEqual = timingSafeEqual(paddedLeft, paddedRight)

  return leftBuffer.length === rightBuffer.length && valuesEqual
}

export function createSessionCookie() {
  const timestamp = Date.now().toString()
  const signature = createSignature(timestamp)

  return `${timestamp}.${signature}`
}

export function verifySessionCookie(value: string) {
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
    return safeEqual(signature, createSignature(timestamp))
  } catch {
    return false
  }
}

export function verifyPassword(input: string) {
  const password = process.env.DASHBOARD_PASSWORD

  if (!password) {
    safeEqual(input, "")
    return false
  }

  return safeEqual(input, password)
}
