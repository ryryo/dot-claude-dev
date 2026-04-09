"use client"

import { useMemo, useState } from "react"
import { Check, ChevronDown, Circle } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Separator } from "@/components/ui/separator"
import type { PlanFile } from "@/lib/types"
import { cn } from "@/lib/utils"

interface PlanDetailProps {
  plan: PlanFile
}

export function PlanDetail({ plan }: PlanDetailProps) {
  const defaultGateId = useMemo(() => plan.gates[0]?.id ?? null, [plan.gates])
  const [openGateId, setOpenGateId] = useState<string | null>(defaultGateId)

  if (plan.gates.length === 0) {
    return (
      <div className="text-muted-foreground rounded-xl border border-dashed px-4 py-6 text-sm">
        Gate 情報がありません。
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {plan.gates.map((gate, index) => {
        const completedCount = gate.todos.filter((todo) => todo.checked).length
        const isOpen = openGateId === gate.id

        return (
          <div key={`${plan.projectName}/${plan.filePath}-${index}`} className="rounded-xl border bg-background/70">
            <Collapsible
              open={isOpen}
              onOpenChange={(open) => setOpenGateId(open ? gate.id : null)}
            >
              <CollapsibleTrigger className="flex w-full cursor-pointer items-center justify-between gap-3 px-4 py-3 text-left" aria-label={`${gate.title} の Todo を${isOpen ? '閉じる' : '開く'}`}>
                <div className="space-y-1">
                  <p className="text-nav font-semibold">{gate.title}</p>
                  <p className="text-muted-foreground text-xs tabular-nums">
                    {completedCount}/{gate.todos.length} 完了
                  </p>
                </div>

                <ChevronDown
                  className={cn(
                    "text-muted-foreground size-4 shrink-0 transition-transform",
                    isOpen && "rotate-180"
                  )}
                />
              </CollapsibleTrigger>

              <CollapsibleContent className="px-4 pb-4">
                <Separator className="mb-3" />
                <div className="space-y-2">
                  {gate.todos.map((todo, todoIndex) => (
                    <div
                      key={`${plan.filePath}-${index}-${todoIndex}`}
                      className="flex items-start justify-between gap-3 rounded-lg bg-muted/30 px-3 py-2"
                    >
                      <div className="flex min-w-0 items-start gap-2">
                        {todo.checked ? (
                          <Check className="mt-0.5 size-4 shrink-0 text-primary" />
                        ) : (
                          <Circle className="text-muted-foreground mt-0.5 size-4 shrink-0" />
                        )}
                        <span className="text-sm whitespace-normal">{todo.title}</span>
                      </div>

                      {todo.hasReview && todo.reviewFilled ? (
                        <Badge variant="secondary" className="shrink-0">
                          Review 済
                        </Badge>
                      ) : null}
                    </div>
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>

            {index < plan.gates.length - 1 ? <Separator /> : null}
          </div>
        )
      })}
    </div>
  )
}
