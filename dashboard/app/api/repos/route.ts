import { NextResponse } from 'next/server'

import { fetchUserRepos } from '@/lib/github'

export async function GET() {
  try {
    const repos = await fetchUserRepos()
    return NextResponse.json({ repos })
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to fetch repos'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
