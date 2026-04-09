"use client"

import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { PlanCard } from "@/components/plan-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { PlanFile, PlanStatus } from "@/lib/types"
import { cn } from "@/lib/utils"

const COLUMNS: { status: PlanStatus; label: string; color: string }[] = [
  { status: "not-started", label: "未実装", color: "bg-status-not-started" },
  { status: "in-progress", label: "実装中", color: "bg-status-in-progress" },
  { status: "in-review", label: "レビュー待ち", color: "bg-status-in-review" },
  { status: "completed", label: "完了", color: "bg-status-completed" },
]

interface KanbanBoardProps {
  plans: PlanFile[]
}

export function KanbanBoard({ plans }: KanbanBoardProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const plansByStatus = COLUMNS.reduce<Record<PlanStatus, PlanFile[]>>(
    (accumulator, column) => {
      accumulator[column.status] = plans.filter((plan) => plan.status === column.status)
      return accumulator
    },
    {
      "not-started": [],
      "in-progress": [],
      "in-review": [],
      completed: [],
    }
  )

  const expandedStatus = expandedId
    ? plans.find((p) => p.filePath === expandedId)?.status ?? null
    : null

  return (
    <div className="flex snap-x snap-mandatory gap-4 overflow-x-auto pb-4 md:overflow-x-visible md:snap-none">
      {COLUMNS.map((column) => {
        const columnPlans = plansByStatus[column.status]
        const isExpanded = expandedStatus === column.status

        return (
          <div
            key={column.status}
            className="w-[85vw] shrink-0 snap-center transition-all duration-300 ease-in-out md:w-auto md:shrink md:min-w-[120px]"
            style={{ flex: expandedStatus === null ? '1 1 0%' : isExpanded ? '2 1 0%' : '1 1 0%' }}
          >
            <Card
              className={cn(
                "min-h-[200px] shrink-0 gap-4 border-none shadow-none",
                column.color
              )}
            >
              <CardHeader className="flex flex-row items-center justify-between gap-3 px-4 pt-4 pb-0">
                <CardTitle className="text-base font-semibold">{column.label}</CardTitle>
                <Badge variant="secondary" className="tabular-nums">
                  {columnPlans.length}
                </Badge>
              </CardHeader>

              <CardContent className="flex flex-1 flex-col gap-3 px-4 pb-4">
                {columnPlans.length > 0 ? (
                  columnPlans.map((plan) => (
                    <PlanCard
                      key={`${plan.projectName}/${plan.filePath}`}
                      plan={plan}
                      expanded={expandedId === plan.filePath}
                      onToggle={() =>
                        setExpandedId((current) =>
                          current === plan.filePath ? null : plan.filePath
                        )
                      }
                    />
                  ))
                ) : (
                  <div className="flex min-h-24 items-center justify-center rounded-lg border border-dashed px-4 py-6 text-center text-sm text-muted-foreground">
                    このステータスの PLAN はありません
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )
      })}
    </div>
  )
}
