"use client"

import { useMemo, useState } from "react"
import useSWR from "swr"

import { DashboardLayout } from "@/components/dashboard-layout"
import { DateFilter } from "@/components/date-filter"
import { KanbanBoard } from "@/components/kanban-board"
import { RepoSelector } from "@/components/repo-selector"
import { SkeletonDashboard } from "@/components/skeleton-dashboard"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardDescription,
  CardHeader,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import type { GitHubRepo, PlanFile, PlanStatus, RepoError } from "@/lib/types"

const STORAGE_KEY = "plan-dashboard-selected-repos"

interface ReposResponse {
  repos: GitHubRepo[]
}

interface PlansResponse {
  plans: PlanFile[]
  errors: RepoError[]
}

const fetcher = async (url: string) => {
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error("データの取得に失敗しました。")
  }

  return response.json()
}

const STATUS_LABELS: Record<PlanStatus, string> = {
  "not-started": "未着手",
  "in-progress": "進行中",
  "in-review": "レビュー中",
  completed: "完了",
}

export default function Home() {
  const { data: reposData, error: reposError, isLoading: reposLoading } = useSWR<ReposResponse>(
    "/api/repos",
    fetcher
  )
  const [filterDays, setFilterDays] = useState<number>(30)
  const [selectedRepos, setSelectedRepos] = useState<string[]>(() => {
    if (typeof window === "undefined") {
      return []
    }

    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved ? (JSON.parse(saved) as string[]) : []
    } catch {
      return []
    }
  })

  const plansUrl =
    selectedRepos.length > 0 ? `/api/plans?repos=${selectedRepos.join(",")}` : null

  const { data: plansData, error: plansError } = useSWR<PlansResponse>(
    plansUrl,
    fetcher
  )

  const handleToggleRepo = (fullName: string) => {
    setSelectedRepos((current) => {
      const next = current.includes(fullName)
        ? current.filter((repo) => repo !== fullName)
        : [...current, fullName]

      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      return next
    })
  }

  const filteredPlans = useMemo(() => {
    if (!plansData?.plans.length) {
      return []
    }

    const cutoff = filterDays === 0 ? null : new Date(Date.now() - filterDays * 86400000)

    return plansData.plans
      .filter((plan) => !cutoff || !plan.createdDate || new Date(plan.createdDate) >= cutoff)
  }, [filterDays, plansData?.plans])

  const planCounts = useMemo(() => {
    const counts: Record<string, number> = {}

    ;(plansData?.plans ?? []).forEach((plan) => {
      counts[plan.projectName] = (counts[plan.projectName] ?? 0) + 1
    })

    return counts
  }, [plansData?.plans])

  const statusCounts = useMemo(() => {
    return filteredPlans.reduce<Record<PlanStatus, number>>(
      (counts, plan) => {
        counts[plan.status] += 1
        return counts
      },
      {
        "not-started": 0,
        "in-progress": 0,
        "in-review": 0,
        completed: 0,
      }
    )
  }, [filteredPlans])

  const totalTodos = filteredPlans.reduce((sum, plan) => sum + plan.progress.total, 0)
  const completedTodos = filteredPlans.reduce(
    (sum, plan) => sum + plan.progress.completed,
    0
  )
  const overallProgress = totalTodos === 0 ? 0 : Math.round((completedTodos / totalTodos) * 100)
  const selectedProjectCount = selectedRepos.length

  if (reposLoading) {
    return <SkeletonDashboard />
  }

  if (reposError || !reposData || (plansError && selectedRepos.length > 0)) {
    const displayError = reposError ?? plansError

    return (
      <main className="flex min-h-svh items-center justify-center bg-muted/30 px-6">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <h2 className="text-lg font-semibold leading-none tracking-tight">データの取得に失敗しました</h2>
            <CardDescription>
              {displayError instanceof Error
                ? displayError.message
                : "PLAN ダッシュボードを表示できませんでした。"}
            </CardDescription>
          </CardHeader>
        </Card>
      </main>
    )
  }

  const filterContent = (
    <RepoSelector
      repos={reposData.repos}
      selected={selectedRepos}
      onToggle={handleToggleRepo}
      planCounts={planCounts}
      errorRepos={(plansData?.errors ?? []).map((error) => error.repo)}
    />
  )

  const dateFilterContent = <DateFilter days={filterDays} onChange={setFilterDays} />

  const statsContent = (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl border bg-muted/30 p-3">
          <p className="text-label text-muted-foreground">選択中リポジトリ</p>
          <p className="mt-1 text-heading-2 tabular-nums">{selectedProjectCount}</p>
        </div>
        <div className="rounded-xl border bg-muted/30 p-3">
          <p className="text-label text-muted-foreground">表示中 PLAN</p>
          <p className="mt-1 text-heading-2 tabular-nums">{filteredPlans.length}</p>
        </div>
      </div>

      <div className="rounded-xl border bg-muted/30 p-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-label text-muted-foreground">Todo 進捗</p>
          <Badge variant="outline">{overallProgress}%</Badge>
        </div>
        <p className="mt-2 text-sm font-medium">
          {completedTodos}/{totalTodos} 件完了
        </p>
      </div>

      <Separator />

      <div className="space-y-2">
        {(Object.entries(STATUS_LABELS) as [PlanStatus, string][]).map(
          ([status, label]) => (
            <div
              key={status}
              className="flex items-center justify-between rounded-lg border bg-muted/20 px-3 py-2"
            >
              <span className="text-sm">{label}</span>
              <Badge variant="secondary" className="tabular-nums">
                {statusCounts[status]}
              </Badge>
            </div>
          )
        )}
      </div>
    </div>
  )

  return (
    <DashboardLayout
      filterContent={filterContent}
      dateFilterContent={dateFilterContent}
      statsContent={statsContent}
    >
      <div className="space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-heading-2">PLAN Board</h1>
            <p className="text-muted-foreground text-sm">
              選択中のリポジトリに含まれる PLAN を看板形式で管理します。
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{selectedProjectCount} Repos</Badge>
            <Badge>{filteredPlans.length} Plans</Badge>
          </div>
        </div>
        <KanbanBoard plans={filteredPlans} />
      </div>
    </DashboardLayout>
  )
}
