"use client"

import Markdown from "react-markdown"

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="prose prose-sm dark:prose-invert max-h-[80vh] overflow-y-auto">
          <Markdown>{markdown}</Markdown>
        </div>
      </DialogContent>
    </Dialog>
  )
}
