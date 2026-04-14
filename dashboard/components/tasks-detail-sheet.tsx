"use client"

import { AlertCircle, ListChecks, RefreshCw } from "lucide-react"

import { TasksDetailTodo } from "@/components/tasks-detail-todo"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { useTasksJson } from "@/lib/use-tasks-json"

interface TasksDetailSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  owner: string
  repo: string
  slug: string
  fallbackTitle: string
}

export function TasksDetailSheet({
  open,
  onOpenChange,
  owner,
  repo,
  slug,
  fallbackTitle,
}: TasksDetailSheetProps) {
  const { state, reload } = useTasksJson({ owner, repo, slug, enabled: open })

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="flex flex-col p-0"
        style={{ maxWidth: "56rem" }}
      >
        <SheetHeader className="shrink-0 border-b px-6 py-4">
          <SheetTitle className="flex items-center gap-2">
            <ListChecks className="size-5" />
            {state.status === "success" ? state.data.spec.title : fallbackTitle}
          </SheetTitle>
        </SheetHeader>
        <ScrollArea className="min-h-0 flex-1">
          <div className="space-y-6 px-6 py-4">
            {state.status === "idle" && null}
            {state.status === "loading" && (
              <div className="space-y-3">
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
              </div>
            )}
            {state.status === "error" && (
              <div className="flex flex-col items-start gap-3 rounded border border-destructive/30 bg-destructive/5 p-4">
                <div className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="size-4" />
                  <span className="font-medium">タスク詳細の取得に失敗しました</span>
                </div>
                <p className="break-all text-muted-foreground text-xs">{state.message}</p>
                <Button size="sm" variant="outline" onClick={reload}>
                  <RefreshCw className="mr-1 size-3" />
                  再試行
                </Button>
              </div>
            )}
            {state.status === "success" && <SuccessView tasks={state.data} />}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}

function SuccessView({ tasks }: { tasks: import("@/lib/types").TasksJsonV2 }) {
  return (
    <>
      <section className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{tasks.spec.slug}</Badge>
          <Badge variant="secondary">{tasks.status}</Badge>
          {tasks.spec.createdDate && (
            <span className="text-muted-foreground text-xs">{tasks.spec.createdDate}</span>
          )}
          <span className="text-muted-foreground text-xs tabular-nums">
            {tasks.progress.completed}/{tasks.progress.total}
          </span>
        </div>
        {tasks.spec.summary && <p className="text-muted-foreground text-sm">{tasks.spec.summary}</p>}
      </section>

      {tasks.preflight.length > 0 && (
        <section className="space-y-2">
          <h3 className="text-sm font-semibold">Preflight</h3>
          <ul className="space-y-2">
            {tasks.preflight.map((p) => (
              <li key={p.id} className="space-y-1 rounded border px-3 py-2 text-xs">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{p.id}</Badge>
                  {p.manual && <Badge variant="secondary">手動</Badge>}
                  <span className="font-medium">{p.title}</span>
                </div>
                {p.command && (
                  <pre className="overflow-x-auto rounded bg-muted px-2 py-1">{p.command}</pre>
                )}
                {p.reason && <p className="text-muted-foreground">{p.reason}</p>}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="space-y-2">
        <h3 className="text-sm font-semibold">Gates</h3>
        <Accordion multiple className="w-full">
          {tasks.gates.map((gate) => {
            const todos = tasks.todos.filter((t) => t.gate === gate.id)

            return (
              <AccordionItem key={gate.id} value={gate.id}>
                <AccordionTrigger className="text-left">
                  <div className="flex items-center gap-2">
                    <Badge>{gate.id}</Badge>
                    <span className="font-medium">{gate.title}</span>
                    <span className="text-muted-foreground text-xs">({todos.length} todos)</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="space-y-3">
                  {gate.description && (
                    <p className="text-muted-foreground text-xs">{gate.description}</p>
                  )}
                  {gate.dependencies.length > 0 && (
                    <p className="text-xs">
                      <span className="text-muted-foreground">依存: </span>
                      {gate.dependencies.join(", ")}
                    </p>
                  )}
                  <p className="text-xs">
                    <span className="text-muted-foreground">通過条件: </span>
                    {gate.passCondition}
                  </p>
                  <Accordion multiple className="w-full">
                    {todos.map((todo) => (
                      <TasksDetailTodo key={todo.id} todo={todo} />
                    ))}
                  </Accordion>
                </AccordionContent>
              </AccordionItem>
            )
          })}
        </Accordion>
      </section>
    </>
  )
}
