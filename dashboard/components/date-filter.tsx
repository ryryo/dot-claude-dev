"use client"

import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"

interface DateFilterProps {
  days: number
  onChange: (days: number) => void
}

const PRESETS = [
  { label: "1週間", days: 7 },
  { label: "1ヶ月", days: 30 },
  { label: "3ヶ月", days: 90 },
  { label: "すべて", days: 0 },
] as const

export function DateFilter({ days, onChange }: DateFilterProps) {
  const sliderValue = days === 0 ? 7 : Math.min(Math.max(days, 1), 90)

  return (
    <section aria-label="期間フィルター" className="space-y-3">
      <div className="flex flex-wrap gap-1.5">
        {PRESETS.map((preset) => (
          <Button
            key={preset.days}
            size="sm"
            type="button"
            variant={days === preset.days ? "default" : "outline"}
            onClick={() => onChange(preset.days)}
          >
            {preset.label}
          </Button>
        ))}
      </div>

      <div className="space-y-1.5">
        <Slider
          min={1}
          max={90}
          step={1}
          value={sliderValue}
          disabled={days === 0}
          onValueChange={(value) => onChange(value)}
          aria-label="表示期間"
        />
        <p className="text-muted-foreground text-xs">
          {days === 0 ? "すべての期間" : `過去 ${days} 日間`}
        </p>
      </div>
    </section>
  )
}
