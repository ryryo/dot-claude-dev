"use client"

import { CheckCircle2, Circle } from "lucide-react"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"

import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import type { TasksJsonV2Todo } from "@/lib/types"

interface TasksDetailTodoProps {
  todo: TasksJsonV2Todo
}

export function TasksDetailTodo({ todo }: TasksDetailTodoProps) {
  const completedSteps = todo.steps.filter((step) => step.checked).length

  return (
    <AccordionItem value={todo.id} className="border rounded mb-2">
      <AccordionTrigger className="px-3 py-2 text-left hover:no-underline">
        <div className="flex items-center gap-2 min-w-0">
          <Badge variant="outline">{todo.id}</Badge>
          {todo.tdd && <Badge variant="secondary">TDD</Badge>}
          <span className="font-medium truncate">{todo.title}</span>
          <span className="text-xs text-muted-foreground tabular-nums shrink-0">
            {completedSteps}/{todo.steps.length}
          </span>
        </div>
      </AccordionTrigger>
      <AccordionContent className="px-3 py-3 space-y-4">
        {todo.description && (
          <p className="text-xs text-muted-foreground">{todo.description}</p>
        )}

        {todo.dependencies.length > 0 && (
          <p className="text-xs">
            <span className="text-muted-foreground">依存: </span>
            {todo.dependencies.join(", ")}
          </p>
        )}

        {todo.affectedFiles.length > 0 && (
          <div className="space-y-1">
            <h4 className="text-xs font-semibold">変更ファイル</h4>
            <ul className="space-y-1 text-xs">
              {todo.affectedFiles.map((file, index) => (
                <li key={index} className="flex items-start gap-2">
                  <Badge variant="outline" className="shrink-0">
                    {file.operation}
                  </Badge>
                  <div className="min-w-0">
                    <code className="break-all">{file.path}</code>
                    {file.summary && (
                      <p className="text-muted-foreground">{file.summary}</p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {todo.relatedIssues.length > 0 && (
          <p className="text-xs">
            <span className="text-muted-foreground">関連 Issue: </span>
            {todo.relatedIssues.join(", ")}
          </p>
        )}

        <div className="space-y-1">
          <h4 className="text-xs font-semibold">Steps</h4>
          <ul className="space-y-1 text-xs">
            {todo.steps.map((step, index) => (
              <li key={index} className="flex items-start gap-2">
                {step.checked ? (
                  <CheckCircle2 className="size-3.5 text-green-600 shrink-0 mt-0.5" />
                ) : (
                  <Circle className="size-3.5 text-muted-foreground shrink-0 mt-0.5" />
                )}
                <div className="min-w-0">
                  <span>{step.title}</span>
                  {step.kind === "review" && step.review && (
                    <div className="mt-1 rounded bg-muted px-2 py-1 space-y-0.5">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            step.review.result === "PASSED"
                              ? "default"
                              : "destructive"
                          }
                        >
                          {step.review.result}
                        </Badge>
                        {typeof step.review.fixCount === "number" && (
                          <span className="text-muted-foreground">
                            fix: {step.review.fixCount}
                          </span>
                        )}
                      </div>
                      {step.review.summary && (
                        <p className="text-muted-foreground">
                          {step.review.summary}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>

        {todo.impl && (
          <div className="space-y-1">
            <h4 className="text-xs font-semibold">実装手順</h4>
            <div className="prose prose-sm dark:prose-invert max-w-none rounded border bg-muted/30 px-3 py-2">
              <Markdown remarkPlugins={[remarkGfm]}>{todo.impl}</Markdown>
            </div>
          </div>
        )}
      </AccordionContent>
    </AccordionItem>
  )
}
