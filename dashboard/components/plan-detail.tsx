"use client"

import { Check, ChevronDown, X } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Separator } from "@/components/ui/separator"
import type { Gate, GateReview, PlanFile } from "@/lib/types"
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
                <div className="flex items-center gap-2 min-w-0">
                  <p className="text-nav font-semibold truncate">
                    {gate.id}: {gate.title}
                  </p>
                  <ReviewBadge gate={gate} />
                </div>
                <ChevronDown
                  className={cn(
                    "text-muted-foreground size-4 shrink-0 transition-transform",
                    "group-data-[panel-open]:rotate-180"
                  )}
                />
              </CollapsibleTrigger>

              <CollapsibleContent className="space-y-4 px-4 pb-4">
                <Separator className="mb-1" />

                {(gate.goal.what || gate.goal.why) && (
                  <section className="space-y-1.5">
                    <h4 className="text-xs font-semibold uppercase text-muted-foreground">Goal</h4>
                    {gate.goal.what && (
                      <p className="text-sm">
                        <span className="text-muted-foreground">What: </span>
                        {gate.goal.what}
                      </p>
                    )}
                    {gate.goal.why && (
                      <p className="text-sm">
                        <span className="text-muted-foreground">Why: </span>
                        {gate.goal.why}
                      </p>
                    )}
                  </section>
                )}

                {gate.constraints.must.length > 0 && (
                  <section className="space-y-1.5">
                    <h4 className="text-xs font-semibold uppercase text-muted-foreground">MUST</h4>
                    <ul className="list-disc space-y-1 pl-5 text-sm">
                      {gate.constraints.must.map((item, i) => (
                        <li key={`must-${i}`}>{item}</li>
                      ))}
                    </ul>
                  </section>
                )}

                {gate.constraints.mustNot.length > 0 && (
                  <section className="space-y-1.5">
                    <h4 className="text-xs font-semibold uppercase text-muted-foreground">MUST NOT</h4>
                    <ul className="list-disc space-y-1 pl-5 text-sm">
                      {gate.constraints.mustNot.map((item, i) => (
                        <li key={`mustnot-${i}`}>{item}</li>
                      ))}
                    </ul>
                  </section>
                )}

                {gate.acceptanceCriteria.length > 0 && (
                  <section className="space-y-1.5">
                    <h4 className="text-xs font-semibold uppercase text-muted-foreground">
                      Acceptance Criteria
                    </h4>
                    <ul className="space-y-1.5">
                      {gate.acceptanceCriteria.map((ac) => (
                        <li key={ac.id} className="flex items-start gap-2 text-sm">
                          <span
                            className={cn(
                              "mt-0.5 inline-flex size-4 shrink-0 items-center justify-center rounded border",
                              ac.checked ? "border-primary bg-primary text-primary-foreground" : "border-muted-foreground/40"
                            )}
                            aria-label={ac.checked ? "完了" : "未完了"}
                          >
                            {ac.checked && <Check className="size-3" />}
                          </span>
                          <span className="min-w-0">
                            <span className="font-mono text-xs text-muted-foreground">{ac.id}</span>{" "}
                            {ac.description}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}

                <ReviewSection gate={gate} />
              </CollapsibleContent>
            </Collapsible>

            {gateIndex < plan.gates.length - 1 ? <Separator /> : null}
          </div>
        ))
      )}
    </div>
  )
}

function ReviewBadge({ gate }: { gate: Gate }) {
  if (gate.review !== null) {
    return <ResultBadge result={gate.review.result} />
  }
  const total = gate.acceptanceCriteria.length
  const passed = gate.acceptanceCriteria.filter((ac) => ac.checked).length
  if (total === 0 || passed < total) {
    return (
      <Badge variant="outline" className="text-muted-foreground border-dashed">
        未レビュー
      </Badge>
    )
  }
  return (
    <Badge variant="secondary" className="bg-amber-500/15 text-amber-700 dark:text-amber-300">
      レビュー待ち
    </Badge>
  )
}

function ResultBadge({ result }: { result: GateReview["result"] }) {
  switch (result) {
    case "PASSED":
      return (
        <Badge className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30" variant="outline">
          ✅ PASSED
        </Badge>
      )
    case "FAILED":
      return (
        <Badge variant="destructive">
          <X className="mr-1 size-3" />
          FAILED
        </Badge>
      )
    case "SKIPPED":
      return (
        <Badge variant="outline" className="text-muted-foreground">
          SKIPPED
        </Badge>
      )
    case "IN_PROGRESS":
    default:
      return (
        <Badge variant="outline" className="text-blue-600 dark:text-blue-400 border-blue-500/30">
          進行中
        </Badge>
      )
  }
}

function ReviewSection({ gate }: { gate: Gate }) {
  if (gate.review === null) {
    const total = gate.acceptanceCriteria.length
    const passed = gate.acceptanceCriteria.filter((ac) => ac.checked).length
    const isReadyForReview = total > 0 && passed === total
    return (
      <section className="space-y-1.5">
        <h4 className="text-xs font-semibold uppercase text-muted-foreground">Review</h4>
        <p className="text-sm text-muted-foreground">
          {isReadyForReview ? "チェック項目を全て満たしています。レビュー待ち。" : "未レビュー (チェック項目 未充足)"}
        </p>
      </section>
    )
  }

  return (
    <section className="space-y-1.5">
      <div className="flex items-center gap-2">
        <h4 className="text-xs font-semibold uppercase text-muted-foreground">Review</h4>
        <ResultBadge result={gate.review.result} />
        {gate.review.fixCount > 0 && (
          <span className="text-xs text-muted-foreground">fix: {gate.review.fixCount}</span>
        )}
      </div>
      {gate.review.summary && (
        <p className="text-sm whitespace-pre-wrap">{gate.review.summary}</p>
      )}
    </section>
  )
}
