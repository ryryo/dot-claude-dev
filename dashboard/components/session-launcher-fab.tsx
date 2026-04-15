'use client';

import { useState } from 'react';
import { Plus } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { SessionLauncherDialog } from '@/components/session-launcher-dialog';
import type { GitHubRepo } from '@/lib/types';

interface SessionLauncherFabProps {
  selectedRepos: string[];
  repos: GitHubRepo[];
}

export function SessionLauncherFab({ selectedRepos, repos }: SessionLauncherFabProps) {
  const [open, setOpen] = useState(false);
  const candidateRepos = repos.filter((r) => selectedRepos.includes(r.full_name));
  const disabled = candidateRepos.length === 0;

  return (
    <>
      <Button
        size="icon"
        className="fixed bottom-6 right-6 z-40 h-14 w-14 rounded-full shadow-lg"
        onClick={() => setOpen(true)}
        aria-label="Claude Code Web セッションを起動"
        disabled={disabled}
        title={disabled ? 'サイドバーでリポジトリを選択してください' : 'Claude Code Web セッションを起動'}
      >
        <Plus className="h-6 w-6" />
      </Button>
      <SessionLauncherDialog
        open={open}
        onOpenChange={setOpen}
        candidateRepos={candidateRepos}
      />
    </>
  );
}
