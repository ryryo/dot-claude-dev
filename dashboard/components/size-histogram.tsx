"use client"

import { getSizeHistogram, SIZE_BINS, SIZE_BIN_LABEL, SizeBin } from '@/lib/plan-size'
import type { PlanFile } from '@/lib/types'
import { cn } from '@/lib/utils'

interface SizeHistogramProps {
  plans: PlanFile[]
  activeBin: SizeBin | null
  onBinClick: (bin: SizeBin) => void
}

export function SizeHistogram({ plans, activeBin, onBinClick }: SizeHistogramProps) {
  const counts = getSizeHistogram(plans)
  const max = Math.max(1, ...SIZE_BINS.map((b) => counts[b]))

  return (
    <div className="rounded-lg border bg-muted/20 p-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground">規模分布（クリックで絞込）</p>
        {activeBin && (
          <button
            type="button"
            onClick={() => onBinClick(activeBin)}
            className="text-xs text-primary underline"
          >
            絞込解除
          </button>
        )}
      </div>
      <div className="flex items-end gap-3">
        {SIZE_BINS.map((bin) => {
          const count = counts[bin]
          const heightPct = (count / max) * 100
          const isActive = activeBin === bin
          return (
            <button
              key={bin}
              type="button"
              onClick={() => onBinClick(bin)}
              aria-pressed={isActive}
              className={cn('group flex flex-1 flex-col items-center gap-1', 'cursor-pointer')}
            >
              <span className="text-xs tabular-nums text-muted-foreground">{count}</span>
              <div className="flex h-16 w-full items-end">
                <div
                  className={cn(
                    'w-full rounded-t transition-colors',
                    isActive ? 'bg-primary' : 'bg-primary/40 group-hover:bg-primary/60'
                  )}
                  style={{ height: `${Math.max(4, heightPct)}%` }}
                />
              </div>
              <span
                className={cn(
                  'text-xs',
                  isActive ? 'font-semibold text-foreground' : 'text-muted-foreground'
                )}
              >
                {SIZE_BIN_LABEL[bin]}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
