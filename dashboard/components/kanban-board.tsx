"use client"

import { useEffect, useMemo, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { PlanCard } from "@/components/plan-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { SizeBin } from "@/lib/plan-size"
import { getPlanSize, getSizeBin } from "@/lib/plan-size"
import type { PlanFile, PlanStatus } from "@/lib/types"
import { cn } from "@/lib/utils"

const COLUMNS: { status: PlanStatus; label: string; color: string; bgVar: string }[] = [
  { status: "not-started", label: "未実装", color: "bg-status-not-started", bgVar: "var(--color-status-not-started)" },
  { status: "in-progress", label: "実装中", color: "bg-status-in-progress", bgVar: "var(--color-status-in-progress)" },
  { status: "in-review", label: "レビュー待ち", color: "bg-status-in-review", bgVar: "var(--color-status-in-review)" },
  { status: "completed", label: "完了", color: "bg-status-completed", bgVar: "var(--color-status-completed)" },
]

interface KanbanBoardProps {
  plans: PlanFile[]
  groupByProject?: boolean
  sizeBinFilter?: SizeBin | null
}

export function KanbanBoard({ plans, groupByProject = false, sizeBinFilter }: KanbanBoardProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [isMd, setIsMd] = useState(false)

  const filteredPlans = sizeBinFilter
    ? plans.filter((p) => getSizeBin(getPlanSize(p).total) === sizeBinFilter)
    : plans

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)")
    setIsMd(mq.matches)
    const handler = (e: MediaQueryListEvent) => setIsMd(e.matches)
    mq.addEventListener("change", handler)
    return () => mq.removeEventListener("change", handler)
  }, [])

  const projects = useMemo(() => {
    if (!groupByProject) return null
    const map = new Map<string, PlanFile[]>()
    for (const p of filteredPlans) {
      const arr = map.get(p.projectName) ?? []
      arr.push(p)
      map.set(p.projectName, arr)
    }
    return Array.from(map.entries())
  }, [groupByProject, filteredPlans])

  if (groupByProject && projects) {
    return (
      <div className="max-h-[calc(100vh-220px)] space-y-4 overflow-y-auto pr-1">
        {projects.map(([projectName, projectPlans]) => (
          <div key={projectName} className="space-y-2">
            <div className="sticky top-0 z-10 -mx-1 bg-background/95 px-1 py-1 backdrop-blur">
              <p className="text-sm font-semibold text-muted-foreground">
                {projectName}{" "}
                <span className="text-xs tabular-nums">({projectPlans.length})</span>
              </p>
            </div>
            <KanbanGrid
              plans={projectPlans}
              isMd={isMd}
              expandedId={expandedId}
              setExpandedId={setExpandedId}
            />
          </div>
        ))}
      </div>
    )
  }

  return (
    <KanbanGrid
      plans={filteredPlans}
      isMd={isMd}
      expandedId={expandedId}
      setExpandedId={setExpandedId}
    />
  )
}

interface KanbanGridProps {
  plans: PlanFile[]
  isMd: boolean
  expandedId: string | null
  setExpandedId: (updater: (current: string | null) => string | null) => void
}

function KanbanGrid({ plans, isMd, expandedId, setExpandedId }: KanbanGridProps) {
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
        const isNarrow = isMd && expandedId !== null && !isExpanded
        const flexStyle = isMd
          ? { flex: expandedStatus === null ? "1 1 0%" : isExpanded ? "2 1 0%" : "1 1 0%" }
          : undefined

        return (
          <div
            key={column.status}
            className="relative overflow-hidden w-[85vw] shrink-0 snap-center transition-all duration-300 ease-in-out md:w-auto md:shrink md:min-w-[120px]"
            style={flexStyle}
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
                      isNarrow={isNarrow}
                      narrowFadeBg={isNarrow ? column.bgVar : undefined}
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
