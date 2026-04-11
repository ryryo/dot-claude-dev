"use client"

import { Check, ChevronDown, Circle } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Separator } from "@/components/ui/separator"
import type { PlanFile, Step } from "@/lib/types"
import { cn } from "@/lib/utils"

interface PlanDetailProps {
  plan: PlanFile
}

export function PlanDetail({ plan }: PlanDetailProps) {
  const totalSteps = plan.gates.flatMap((gate) => gate.todos.flatMap((todo) => todo.steps)).length

  return (
    <div className="space-y-3">
      {plan.summary ? (
        <>
          <p className="text-muted-foreground text-sm whitespace-pre-wrap">{plan.summary}</p>
          <Separator />
        </>
      ) : null}
      {totalSteps === 0 ? (
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
                <div className="space-y-2">
                  {gate.todos.map((todo, todoIndex) => {
                    const completedSteps = todo.steps.filter((step) => step.checked).length
                    return (
                      <div
                        key={`${plan.filePath}-gate-${gateIndex}-todo-${todoIndex}`}
                        className="rounded-lg border bg-background/40"
                      >
                        <Collapsible defaultOpen>
                          <CollapsibleTrigger
                            className="group flex w-full cursor-pointer items-center justify-between gap-3 px-3 py-2 text-left"
                            aria-label={`${todo.title} を開閉`}
                          >
                            <div className="flex min-w-0 items-center gap-2">
                              <span className="text-sm font-medium whitespace-normal">{todo.title}</span>
                              <span className="text-muted-foreground text-xs tabular-nums">
                                ({completedSteps}/{todo.steps.length} 完了)
                              </span>
                            </div>
                            <ChevronDown
                              className={cn(
                                "text-muted-foreground size-4 shrink-0 transition-transform",
                                "group-data-[panel-open]:rotate-180"
                              )}
                            />
                          </CollapsibleTrigger>
                          <CollapsibleContent className="space-y-1.5 px-3 pb-3">
                            {todo.steps.map((step, stepIndex) => (
                              <StepRow
                                key={`${plan.filePath}-gate-${gateIndex}-todo-${todoIndex}-step-${stepIndex}`}
                                step={step}
                              />
                            ))}
                          </CollapsibleContent>
                        </Collapsible>
                      </div>
                    )
                  })}
                </div>
              </CollapsibleContent>
            </Collapsible>

            {gateIndex < plan.gates.length - 1 ? <Separator /> : null}
          </div>
        ))
      )}
    </div>
  )
}

function StepRow({ step }: { step: Step }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-md bg-muted/30 px-3 py-2">
      <div className="flex min-w-0 flex-col gap-1">
        <div className="flex items-center gap-2">
          {step.checked ? (
            <Check className="text-primary size-4 shrink-0" />
          ) : (
            <Circle className="text-muted-foreground size-4 shrink-0" />
          )}
          <span className="text-sm font-medium whitespace-normal">{step.title}</span>
        </div>
        {step.description ? (
          <p className="text-muted-foreground line-clamp-2 pl-6 text-xs">{step.description}</p>
        ) : null}
      </div>
      {step.kind === "review" && step.hasReview && step.reviewFilled ? (
        <Badge variant="secondary" className="shrink-0">
          {step.reviewResult ?? "Review済"}
          {step.reviewFixCount && step.reviewFixCount > 0 ? ` · FIX ${step.reviewFixCount}回` : ""}
        </Badge>
      ) : null}
    </div>
  )
}
