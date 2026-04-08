import { Badge } from "@/components/ui/badge"
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
                    <Card key={plan.filePath} className="gap-3 py-4 shadow-sm">
                      <CardContent className="space-y-4 px-4">
                        <div className="space-y-2">
                          <div className="flex items-start justify-between gap-3">
                            <h3 className="line-clamp-2 text-sm font-semibold whitespace-normal">
                              {plan.title}
                            </h3>
                            <Badge variant="outline" className="max-w-full shrink-0">
                              <span className="max-w-[120px] truncate">{plan.projectName}</span>
                            </Badge>
                          </div>

                          <p className="text-muted-foreground line-clamp-1 text-xs whitespace-normal">
                            {plan.fileName}
                          </p>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between gap-2 text-xs">
                            <span className="text-muted-foreground">進捗</span>
                            <span className="font-medium tabular-nums">
                              {plan.progress.percentage}%
                            </span>
                          </div>

                          <div className="h-2 overflow-hidden rounded-full bg-muted">
                            <div
                              className="bg-primary h-full rounded-full transition-[width]"
                              style={{ width: `${plan.progress.percentage}%` }}
                            />
                          </div>

                          <p className="text-muted-foreground text-xs tabular-nums">
                            {plan.progress.completed}/{plan.progress.total} tasks
                          </p>
                        </div>
                      </CardContent>
                    </Card>
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
