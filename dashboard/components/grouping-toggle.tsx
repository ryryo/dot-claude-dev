"use client"

import { Layers } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface GroupingToggleProps {
  enabled: boolean
  onToggle: (next: boolean) => void
}

export function GroupingToggle({ enabled, onToggle }: GroupingToggleProps) {
  return (
    <Button
      type="button"
      variant={enabled ? 'default' : 'outline'}
      size="sm"
      aria-pressed={enabled}
      onClick={() => onToggle(!enabled)}
      className={cn('h-8 gap-1.5')}
    >
      <Layers className="size-4" />
      Project でグループ化
    </Button>
  )
}
