'use client';

import { useState } from 'react';
import { Copy, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  PromptInput,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from '@/components/ai-elements/prompt-input';
import type { GitHubRepo } from '@/lib/types';

interface SessionLauncherDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  candidateRepos: GitHubRepo[];
}

type LaunchState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; sessionUrl: string }
  | { status: 'error'; message: string; cookieExpired?: boolean };

export function SessionLauncherDialog({
  open,
  onOpenChange,
  candidateRepos,
}: SessionLauncherDialogProps) {
  const [selectedRepoRaw, setSelectedRepo] = useState<string>(
    candidateRepos[0]?.full_name ?? ''
  );
  const [prompt, setPrompt] = useState('');
  const [state, setState] = useState<LaunchState>({ status: 'idle' });

  const selectedRepo =
    candidateRepos.find((r) => r.full_name === selectedRepoRaw)?.full_name ??
    candidateRepos[0]?.full_name ??
    '';

  const handleOpenChange = (next: boolean) => {
    if (!next) {
      setPrompt('');
      setState({ status: 'idle' });
    }
    onOpenChange(next);
  };

  const repo = candidateRepos.find((r) => r.full_name === selectedRepo);
  const branch = repo?.default_branch ?? '';
  const isLoading = state.status === 'loading';
  const canSubmit = !!repo && prompt.trim().length > 0 && !isLoading;

  const handleSubmit = async (text: string) => {
    if (!repo) return;
    const body = text.trim();
    if (!body) return;

    setState({ status: 'loading' });
    try {
      const res = await fetch('/api/sessions/launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo: repo.full_name,
          branch: repo.default_branch,
          prompt: body,
        }),
      });
      const json = (await res.json()) as {
        sessionUrl?: string;
        error?: string;
        cookieExpired?: boolean;
      };
      if (!res.ok) {
        const message = json.error ?? `HTTP ${res.status}`;
        const cookieExpired = Boolean(json.cookieExpired);
        setState({ status: 'error', message, cookieExpired });
        if (cookieExpired) {
          toast.error('Cookie が期限切れです', {
            description:
              'ターミナルで `/refresh-claude-web-cookie` を実行してから再試行してください',
            duration: 10000,
          });
        } else {
          toast.error('セッション起動に失敗しました', { description: message });
        }
        return;
      }
      const sessionUrl = json.sessionUrl ?? '';
      setState({ status: 'success', sessionUrl });
      toast.success('Claude Code Web セッションを起動しました', {
        description: '新規タブで開きます',
      });
      window.open(sessionUrl, '_blank', 'noopener,noreferrer');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'unknown error';
      setState({ status: 'error', message });
      toast.error('通信エラー', { description: message });
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Claude Code Web セッション起動</DialogTitle>
          <DialogDescription>
            選択したリポジトリのデフォルトブランチで新しいセッションを開始します。
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="repo-select" className="text-sm font-medium">
              リポジトリ
            </label>
            <select
              id="repo-select"
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              disabled={candidateRepos.length === 0}
            >
              {candidateRepos.map((r) => (
                <option key={r.full_name} value={r.full_name}>
                  {r.full_name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <p className="text-sm font-medium">ブランチ</p>
            <p className="rounded-md border border-dashed bg-muted/30 px-3 py-2 text-sm font-mono">
              {branch || '—'}
              <span className="ml-2 text-xs text-muted-foreground">
                (デフォルトブランチから起動)
              </span>
            </p>
          </div>

          <PromptInput onSubmit={(msg) => handleSubmit(msg.text)}>
            <PromptInputTextarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Claude に依頼するタスクを入力..."
              disabled={isLoading}
            />
            <PromptInputFooter>
              <PromptInputTools />
              <PromptInputSubmit
                disabled={!canSubmit}
                status={isLoading ? 'submitted' : undefined}
              />
            </PromptInputFooter>
          </PromptInput>

          {state.status === 'success' && (
            <div className="rounded-md border border-green-500/30 bg-green-500/10 p-3">
              <p className="text-sm font-medium text-green-700 dark:text-green-300">
                セッション URL
              </p>
              <div className="mt-2 flex items-center gap-2">
                <code className="flex-1 truncate text-xs">{state.sessionUrl}</code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => navigator.clipboard.writeText(state.sessionUrl)}
                  aria-label="URL をコピー"
                >
                  <Copy className="h-3 w-3" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    window.open(state.sessionUrl, '_blank', 'noopener,noreferrer')
                  }
                  aria-label="新しいタブで開く"
                >
                  <ExternalLink className="h-3 w-3" />
                </Button>
              </div>
            </div>
          )}

          {state.status === 'error' && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {state.cookieExpired
                ? 'Cookie が期限切れです。ターミナルで `/refresh-claude-web-cookie` を実行してから再試行してください。'
                : state.message}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            閉じる
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
