import { NextResponse } from 'next/server';

import { loadProjectsConfig } from '@/lib/config';
import { scanAllProjects } from '@/lib/project-scanner';

export async function GET() {
  try {
    const config = loadProjectsConfig();
    const plans = scanAllProjects(config);

    return NextResponse.json({
      projects: config.projects,
      plans,
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to load plans' },
      { status: 500 },
    );
  }
}
