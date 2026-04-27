"use client"

import { ChevronDown } from "lucide-react"

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
  return (
    <div className="space-y-3">
      {plan.summary ? (
        <>
          <p className="text-muted-foreground text-sm whitespace-pre-wrap">{plan.summary}</p>
          <Separator />
        </>
      ) : null}
      {plan.gates.length === 0 ? (
        <div className="text-muted-foreground rounded-xl border border-dashed px-4 py-6 text-sm">
          Gate 情報がありません。
        </div>
      ) : (
        plan.gates.map((gate, gateIndex) => (
          <div
            key={`${plan.projectName}/${plan.filePath}-gate-${gateIndex}`}
            className="rounded-xl border bg-background/70"
          >
            <Collapsible defaultOpen>
              <CollapsibleTrigger
                className="group flex w-full cursor-pointer items-center justify-between gap-3 px-4 py-3 text-left"
                aria-label={`${gate.title} を開閉`}
              >
                <p className="text-nav font-semibold">
                  {gate.id}: {gate.title}
                </p>
                <ChevronDown
                  className={cn(
                    "text-muted-foreground size-4 shrink-0 transition-transform",
                    "group-data-[panel-open]:rotate-180"
                  )}
                />
              </CollapsibleTrigger>

              <CollapsibleContent className="px-4 pb-4">
                <Separator className="mb-3" />
                <p className="text-muted-foreground text-sm">
                  Todo: {gate.todos.length} 件 / AC: {gate.acceptanceCriteria.length} 件
                </p>
              </CollapsibleContent>
            </Collapsible>

            {gateIndex < plan.gates.length - 1 ? <Separator /> : null}
          </div>
        ))
      )}
    </div>
  )
}
