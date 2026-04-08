"use client"

import { ChevronDown } from "lucide-react"

import { PlanDetail } from "@/components/plan-detail"
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
}

export function PlanCard({ plan, expanded, onToggle }: PlanCardProps) {
  return (
    <Collapsible open={expanded} onOpenChange={onToggle}>
      <Card className="gap-0 overflow-hidden py-0" style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
        <CardHeader className="px-0 py-0">
          <CollapsibleTrigger className="w-full cursor-pointer">
            <div className="hover:bg-muted/40 flex w-full flex-col gap-4 px-4 py-4 text-left transition-colors">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-2">
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

                <ChevronDown
                  className={cn(
                    "text-muted-foreground mt-0.5 size-4 shrink-0 transition-transform",
                    expanded && "rotate-180"
                  )}
                />
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

        <CollapsibleContent>
          <CardContent className="border-t px-4 py-4">
            <PlanDetail plan={plan} />
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  )
}
