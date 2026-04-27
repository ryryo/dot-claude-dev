"use client"

import { useEffect, useMemo, useRef, useState } from "react"

import { Check, Copy } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { PlanCard } from "@/components/plan-card"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { SizeBin } from "@/lib/plan-size"
import { getPlanSize, getSizeBin } from "@/lib/plan-size"
import { getPlanDirectoryPath } from "@/lib/plan-path"
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
  const [activeIndex, setActiveIndex] = useState(0)
  const sectionRefs = useRef<(HTMLDivElement | null)[]>([])
  const wrapperRef = useRef<HTMLDivElement>(null)
  const dotNavRef = useRef<HTMLDivElement>(null)

  const filteredPlans = sizeBinFilter
    ? plans.filter((p) => getSizeBin(getPlanSize(p).total) === sizeBinFilter)
    : plans

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)")
    // eslint-disable-next-line react-hooks/set-state-in-effect
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

  useEffect(() => {
    if (!groupByProject || !projects) return
    const main = document.getElementById("main-content")
    if (!main) return

    const updateLeft = () => {
      if (!wrapperRef.current || !dotNavRef.current) return
      dotNavRef.current.style.left = `${wrapperRef.current.getBoundingClientRect().left}px`
    }

    updateLeft()
    const ro = new ResizeObserver(updateLeft)
    ro.observe(main)
    window.addEventListener("resize", updateLeft)

    return () => {
      ro.disconnect()
      window.removeEventListener("resize", updateLeft)
    }
  }, [groupByProject, projects])

  useEffect(() => {
    if (!groupByProject || !projects) return

    const handleScroll = () => {
      let active = 0
      sectionRefs.current.forEach((ref, index) => {
        if (!ref) return
        const rect = ref.getBoundingClientRect()
        if (rect.top <= window.innerHeight * 0.4) {
          active = index
        }
      })
      setActiveIndex(active)
    }

    const main = document.getElementById("main-content")
    window.addEventListener("scroll", handleScroll, { passive: true })
    main?.addEventListener("scroll", handleScroll, { passive: true })
    return () => {
      window.removeEventListener("scroll", handleScroll)
      main?.removeEventListener("scroll", handleScroll)
    }
  }, [groupByProject, projects])

  const scrollToProject = (index: number) => {
    sectionRefs.current[index]?.scrollIntoView({ behavior: "smooth", block: "start" })
  }

  if (groupByProject && projects) {
    return (
      <div ref={wrapperRef}>
        {/* Fixed dot navigation */}
        <div
          ref={dotNavRef}
          className="fixed top-1/2 z-20 -translate-y-1/2 flex flex-col items-center rounded-full bg-background/70 px-1.5 py-2 shadow-sm backdrop-blur-sm"
        >
          {projects.map(([projectName], index) => (
            <div key={projectName} className="flex flex-col items-center">
              {index > 0 && (
                <div className="w-px h-5 bg-primary/30" />
              )}
              <button
                onClick={() => scrollToProject(index)}
                title={projectName}
                className={cn(
                  "size-2.5 rounded-full transition-all duration-200 hover:scale-125",
                  activeIndex === index
                    ? "bg-primary"
                    : "bg-primary/30 hover:bg-primary/60"
                )}
              />
            </div>
          ))}
        </div>

        {/* Project sections */}
        <div className="space-y-4">
          {projects.map(([projectName, projectPlans], index) => (
            <div
              key={projectName}
              ref={(el) => { sectionRefs.current[index] = el }}
              className="space-y-2"
            >
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
                <div className="flex items-center gap-2">
                  <ColumnCopyButton plans={columnPlans} label={column.label} />
                  <Badge variant="secondary" className="tabular-nums">
                    {columnPlans.length}
                  </Badge>
                </div>
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

function ColumnCopyButton({ plans, label }: { plans: PlanFile[]; label: string }) {
  const [copied, setCopied] = useState(false)
  const disabled = plans.length === 0

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (disabled) return
    const text = plans
      .map((p) => getPlanDirectoryPath(p.filePath))
      .join('\n')
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch (err) {
      console.error('Failed to copy plan paths:', err)
    }
  }

  return (
    <button
      type="button"
      aria-label={`${label}${plans.length}件のパスをコピー`}
      aria-disabled={disabled}
      onClick={handleClick}
      disabled={disabled}
      className={cn(
        "text-muted-foreground hover:text-foreground cursor-pointer transition-colors",
        disabled && "cursor-not-allowed opacity-40 hover:text-muted-foreground"
      )}
    >
      {copied ? (
        <Check className="size-4 shrink-0" />
      ) : (
        <Copy className="size-4 shrink-0" />
      )}
    </button>
  )
}
