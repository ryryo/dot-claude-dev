"use client"

import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"

import {
  Dialog,
  DialogContent,
} from "@/components/ui/dialog"

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
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl sm:max-w-3xl">
        <div className="prose prose-sm dark:prose-invert max-w-none max-h-[80vh] overflow-y-auto">
          <Markdown remarkPlugins={[remarkGfm]}>{markdown}</Markdown>
        </div>
      </DialogContent>
    </Dialog>
  )
}
