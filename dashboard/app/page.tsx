"use client"

import { useEffect, useMemo, useState } from "react"
import useSWR from "swr"

import { DashboardLayout } from "@/components/dashboard-layout"
import { KanbanBoard } from "@/components/kanban-board"
import { ProjectFilter } from "@/components/project-filter"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import type { PlanFile, PlanStatus, ProjectConfig } from "@/lib/types"

interface PlansResponse {
  projects: ProjectConfig[]
  plans: PlanFile[]
}

const fetcher = async (url: string): Promise<PlansResponse> => {
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error("PLAN データの取得に失敗しました。")
  }

  return response.json() as Promise<PlansResponse>
}

const STATUS_LABELS: Record<PlanStatus, string> = {
  "not-started": "未着手",
  "in-progress": "進行中",
  "in-review": "レビュー中",
  completed: "完了",
}

export default function Home() {
  const { data, error, isLoading } = useSWR<PlansResponse>("/api/plans", fetcher)
  const [selectedProjects, setSelectedProjects] = useState<string[]>([])
  const [hasInitializedSelection, setHasInitializedSelection] = useState(false)

  useEffect(() => {
    if (!data?.projects.length) {
      return
    }

    const projectNames = data.projects.map((project) => project.name)

    setSelectedProjects((current) => {
      if (!hasInitializedSelection) {
        return projectNames
      }

      return current.filter((name) => projectNames.includes(name))
    })

    if (!hasInitializedSelection) {
      setHasInitializedSelection(true)
    }
  }, [data?.projects, hasInitializedSelection])

  const handleToggleProject = (name: string) => {
    setSelectedProjects((current) =>
      current.includes(name)
        ? current.filter((projectName) => projectName !== name)
        : [...current, name]
    )
  }

  const projectNames = data?.projects.map((project) => project.name) ?? []

  const filteredPlans = useMemo(() => {
    if (!data?.plans.length) {
      return []
    }

    const selectedSet = new Set(selectedProjects)
    return data.plans.filter((plan) => selectedSet.has(plan.projectName))
  }, [data?.plans, selectedProjects])

  const planCounts = useMemo(() => {
    const counts: Record<string, number> = {}

    data?.plans.forEach((plan) => {
      counts[plan.projectName] = (counts[plan.projectName] ?? 0) + 1
    })

    return counts
  }, [data?.plans])

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
  const selectedProjectCount = projectNames.filter((name) => selectedProjects.includes(name)).length
  const kanbanComponentName = KanbanBoard.name || "KanbanBoard"

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-muted/30 px-6">
        <div className="space-y-2 text-center">
          <p className="text-lg font-semibold">PLAN Dashboard を読み込み中です</p>
          <p className="text-muted-foreground text-sm">/api/plans からデータを取得しています。</p>
        </div>
      </main>
    )
  }

  if (error || !data) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-muted/30 px-6">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle>データの取得に失敗しました</CardTitle>
            <CardDescription>
              {error instanceof Error
                ? error.message
                : "PLAN ダッシュボードを表示できませんでした。"}
            </CardDescription>
          </CardHeader>
        </Card>
      </main>
    )
  }

  return (
    <DashboardLayout
      sidebar={
        <>
          <Card>
            <CardHeader className="gap-1">
              <CardTitle className="text-base">PLAN Dashboard</CardTitle>
              <CardDescription>
                プロジェクト横断で PLAN を絞り込み、進捗状況を確認できます。
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ProjectFilter
                projects={data.projects}
                selected={selectedProjects}
                onToggle={handleToggleProject}
                planCounts={planCounts}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="gap-1">
              <CardTitle className="text-base">統計サマリー</CardTitle>
              <CardDescription>現在のフィルター条件に基づく集計です。</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border bg-muted/30 p-3">
                  <p className="text-muted-foreground text-xs">選択中プロジェクト</p>
                  <p className="mt-1 text-2xl font-semibold">{selectedProjectCount}</p>
                </div>
                <div className="rounded-xl border bg-muted/30 p-3">
                  <p className="text-muted-foreground text-xs">表示中 PLAN</p>
                  <p className="mt-1 text-2xl font-semibold">{filteredPlans.length}</p>
                </div>
              </div>

              <div className="rounded-xl border bg-muted/30 p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-muted-foreground text-xs">Todo 進捗</p>
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
            </CardContent>
          </Card>
        </>
      }
    >
      <div className="space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-2xl font-semibold tracking-tight">PLAN Board</h1>
            <p className="text-muted-foreground text-sm">
              選択中のプロジェクトに含まれる PLAN を看板形式で管理します。
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{selectedProjectCount} Projects</Badge>
            <Badge>{filteredPlans.length} Plans</Badge>
          </div>
        </div>

        <div className="rounded-2xl border border-dashed bg-background p-10 shadow-sm">
          <div className="mx-auto flex max-w-2xl flex-col items-center justify-center space-y-3 text-center">
            <Badge variant="secondary">Placeholder</Badge>
            <h2 className="text-xl font-semibold">{kanbanComponentName} は次の Todo で実装予定です</h2>
            <p className="text-muted-foreground text-sm leading-6">
              現在はプレースホルダーを表示しています。選択中の {filteredPlans.length} 件の
              PLAN は、このエリアに看板として表示される想定です。
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
