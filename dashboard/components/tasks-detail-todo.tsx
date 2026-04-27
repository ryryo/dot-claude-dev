"use client"

import {
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import type { TasksJsonV3Todo } from "@/lib/types"

interface TasksDetailTodoProps {
  todo: TasksJsonV3Todo
}

export function TasksDetailTodo({ todo }: TasksDetailTodoProps) {
  return (
    <AccordionItem value={todo.id} className="border rounded mb-2">
      <AccordionTrigger className="px-3 py-2 text-left hover:no-underline">
        <div className="flex items-center gap-2 min-w-0">
          <Badge variant="outline">{todo.id}</Badge>
          {todo.tdd && <Badge variant="secondary">TDD</Badge>}
          <span className="font-medium truncate">{todo.title}</span>
        </div>
      </AccordionTrigger>
      <AccordionContent className="px-3 py-3 space-y-4">
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
      </AccordionContent>
    </AccordionItem>
  )
}
