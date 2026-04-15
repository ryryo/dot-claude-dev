import { revalidateTag } from 'next/cache'
import { NextResponse } from 'next/server'

import { GITHUB_CACHE_TAG } from '@/lib/github'

export async function POST() {
  revalidateTag(GITHUB_CACHE_TAG, { expire: 0 })
  return NextResponse.json({ ok: true, revalidatedAt: new Date().toISOString() })
}
