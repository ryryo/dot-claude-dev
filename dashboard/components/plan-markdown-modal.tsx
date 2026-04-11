"use client"

import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"

interface PlanMarkdownModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  markdown: string
}

export function PlanMarkdownModal({
  open,
  onOpenChange,
  title,
  markdown,
}: PlanMarkdownModalProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="flex flex-col p-0"
        style={{ maxWidth: "48rem" }}
      >
        <SheetHeader className="border-b px-6 py-4 shrink-0">
          <SheetTitle>{title}</SheetTitle>
        </SheetHeader>
        <ScrollArea className="flex-1 min-h-0">
          <div className="prose prose-sm dark:prose-invert max-w-none px-6 py-4">
            <Markdown remarkPlugins={[remarkGfm]}>{markdown}</Markdown>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}
