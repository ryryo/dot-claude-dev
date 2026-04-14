"use client"

import { useState } from "react"
import { ChevronDown, FileText, ListChecks } from "lucide-react"

import { PlanDetail } from "@/components/plan-detail"
import { PlanMarkdownModal } from "@/components/plan-markdown-modal"
import { TasksDetailSheet } from "@/components/tasks-detail-sheet"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import type { PlanFile } from "@/lib/types"
import { cn } from "@/lib/utils"

interface PlanCardProps {
  plan: PlanFile
  expanded: boolean
  onToggle: () => void
  isNarrow?: boolean
  narrowFadeBg?: string
}

export function PlanCard({ plan, expanded, onToggle, isNarrow, narrowFadeBg }: PlanCardProps) {
  const [modalOpen, setModalOpen] = useState(false)
  const [tasksOpen, setTasksOpen] = useState(false)
  const [owner, repo] = plan.projectName.split('/')
  const slug = plan.filePath.split('/')[2] ?? ''

  return (
    <Collapsible open={expanded} onOpenChange={onToggle}>
      <Card className="relative gap-0 overflow-hidden py-0" style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
        {/* アイコングループ: FileText + ChevronDown をまとめて絶対配置 */}
        <div className={cn("pointer-events-none absolute top-4 right-3 z-10 flex items-center gap-2", isNarrow && "hidden")}>
          {plan.hasV2Tasks && (
            <button
              type="button"
              aria-label={`${plan.title} のタスク詳細を開く`}
              onClick={(e) => {
                e.stopPropagation()
                setTasksOpen(true)
              }}
              className="text-muted-foreground hover:text-foreground pointer-events-auto cursor-pointer transition-colors"
            >
              <ListChecks className="size-4 shrink-0" />
            </button>
          )}
          <button
            type="button"
            aria-label={`${plan.title} の全文を読む`}
            onClick={(e) => {
              e.stopPropagation()
              setModalOpen(true)
            }}
            className="text-muted-foreground hover:text-foreground pointer-events-auto cursor-pointer transition-colors"
          >
            <FileText className="size-4 shrink-0" />
          </button>
          <ChevronDown
            className={cn(
              "text-muted-foreground size-4 shrink-0 transition-transform",
              expanded && "rotate-180"
            )}
          />
        </div>
        <CardHeader className="px-0 py-0">
          <CollapsibleTrigger className="w-full cursor-pointer" aria-label={`${plan.title} の詳細を${expanded ? '閉じる' : '開く'}`}>
            <div className="hover:bg-muted/40 flex w-full flex-col gap-4 px-4 py-4 text-left transition-colors">
              <div className={cn("pr-14", isNarrow && "pr-2")}>
                <div className="min-w-0 space-y-2">
                  <Badge variant="outline" className="max-w-full">
                    <span className="max-w-[180px] truncate">{plan.projectName}</span>
                  </Badge>

                  <div className="space-y-1">
                    <p className="text-muted-foreground text-mono-label uppercase">
                      PLAN
                    </p>
                    <CardTitle className="line-clamp-2 text-sm leading-5 whitespace-normal">
                      {plan.title}
                    </CardTitle>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2 text-xs">
                  <span className="text-muted-foreground">進捗</span>
                  <span className="font-medium tabular-nums">
                    {plan.progress.completed}/{plan.progress.total}
                  </span>
                </div>

                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="bg-primary h-full rounded-full transition-[width]"
                    style={{ width: `${plan.progress.percentage}%` }}
                  />
                </div>

                <p className="text-muted-foreground text-xs break-all">{plan.fileName}</p>
              </div>
            </div>
          </CollapsibleTrigger>
        </CardHeader>

        {narrowFadeBg && (
          <div
            className="pointer-events-none absolute inset-y-0 right-0 z-20 w-8"
            style={{ background: `linear-gradient(to right, transparent, ${narrowFadeBg})` }}
          />
        )}
        <CollapsibleContent>
          <CardContent className="border-t px-4 py-4">
            <PlanDetail plan={plan} />
          </CardContent>
        </CollapsibleContent>
      </Card>
      <PlanMarkdownModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        title={plan.title}
        markdown={plan.rawMarkdown}
      />
      {plan.hasV2Tasks && owner && repo && slug && (
        <TasksDetailSheet
          open={tasksOpen}
          onOpenChange={setTasksOpen}
          owner={owner}
          repo={repo}
          slug={slug}
          fallbackTitle={plan.title}
        />
      )}
    </Collapsible>
  )
}
