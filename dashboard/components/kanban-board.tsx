"use client"

import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { PlanCard } from "@/components/plan-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { PlanFile, PlanStatus } from "@/lib/types"
import { cn } from "@/lib/utils"

const COLUMNS: { status: PlanStatus; label: string; color: string }[] = [
  { status: "not-started", label: "未実装", color: "bg-gray-100" },
  { status: "in-progress", label: "実装中", color: "bg-blue-50" },
  { status: "in-review", label: "レビュー待ち", color: "bg-yellow-50" },
  { status: "completed", label: "完了", color: "bg-green-50" },
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

  return (
    <ScrollArea className="w-full whitespace-nowrap rounded-2xl border bg-background shadow-sm">
      <div className="grid min-w-max grid-cols-4 gap-4 p-4">
        {COLUMNS.map((column) => {
          const columnPlans = plansByStatus[column.status]

          return (
            <Card
              key={column.status}
              className={cn(
                "min-h-[420px] min-w-[280px] shrink-0 gap-4 border-none shadow-none",
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
                      key={plan.filePath}
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
                  <div className="text-muted-foreground flex min-h-32 flex-1 items-center justify-center rounded-xl border border-dashed bg-background/70 px-4 text-center text-sm whitespace-normal">
                    このステータスの PLAN はありません。
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </ScrollArea>
  )
}
