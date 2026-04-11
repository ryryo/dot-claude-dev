"use client"

import { LayoutGrid, Table } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export type ViewType = 'kanban' | 'table'

interface ViewSwitcherProps {
  activeView: ViewType
  onViewChange: (view: ViewType) => void
}

const VIEWS: { id: ViewType; label: string; icon: typeof LayoutGrid }[] = [
  { id: 'kanban', label: 'Kanban', icon: LayoutGrid },
  { id: 'table', label: 'Table', icon: Table },
]

export function ViewSwitcher({ activeView, onViewChange }: ViewSwitcherProps) {
  return (
    <div
      role="tablist"
      aria-label="ビュー切替"
      className="inline-flex items-center gap-1 rounded-lg border bg-muted/40 p-1"
    >
      {VIEWS.map((v) => {
        const Icon = v.icon
        const isActive = activeView === v.id
        return (
          <Button
            key={v.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            variant={isActive ? 'default' : 'ghost'}
            size="sm"
            className={cn('h-8 gap-1.5 px-3', !isActive && 'text-muted-foreground')}
            onClick={() => onViewChange(v.id)}
          >
            <Icon className="size-4" />
            {v.label}
          </Button>
        )
      })}
    </div>
  )
}
