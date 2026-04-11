"use client"

import { useMemo, useState } from 'react'
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from '@tanstack/react-table'

import { Badge } from '@/components/ui/badge'
import { getPlanSize, getSizeBin } from '@/lib/plan-size'
import { cn } from '@/lib/utils'
import type { PlanFile, PlanStatus } from '@/lib/types'

const STATUS_LABEL: Record<PlanStatus, string> = {
  'not-started': '未着手',
  'in-progress': '進行中',
  'in-review': 'レビュー中',
  completed: '完了',
}

const STATUS_BG_CLASS: Record<PlanStatus, string> = {
  'not-started': 'bg-status-not-started',
  'in-progress': 'bg-status-in-progress',
  'in-review': 'bg-status-in-review',
  completed: 'bg-status-completed',
}

interface PlanTableProps {
  plans: PlanFile[]
}

export function PlanTable({ plans }: PlanTableProps) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'size', desc: false }])

  const columns = useMemo<ColumnDef<PlanFile>[]>(() => [
    {
      id: 'projectName',
      accessorFn: (row) => row.projectName,
      header: 'プロジェクト',
      cell: (info) => (
        <Badge variant="outline" className="max-w-[160px] truncate">
          {info.getValue<string>()}
        </Badge>
      ),
    },
    {
      id: 'title',
      accessorKey: 'title',
      header: 'PLAN',
      cell: (info) => (
        <span className="line-clamp-1 text-sm font-medium">{info.getValue<string>()}</span>
      ),
    },
    {
      id: 'status',
      accessorKey: 'status',
      header: 'ステータス',
      cell: (info) => {
        const s = info.getValue<PlanStatus>()
        return (
          <span className={cn('inline-flex rounded-md px-2 py-0.5 text-xs', STATUS_BG_CLASS[s])}>
            {STATUS_LABEL[s]}
          </span>
        )
      },
    },
    {
      id: 'size',
      accessorFn: (row) => getPlanSize(row).total,
      header: '規模',
      cell: (info) => {
        const total = info.getValue<number>()
        const bin = getSizeBin(total)
        const maxBar = 20
        const widthPct = Math.min(100, (total / maxBar) * 100)
        return (
          <div className="flex items-center gap-2">
            <span className="w-6 text-right tabular-nums text-muted-foreground">{total}</span>
            <div className="h-2 w-20 overflow-hidden rounded-full bg-muted">
              <div className="h-full bg-primary/70" style={{ width: `${widthPct}%` }} />
            </div>
            <span className="w-6 text-xs text-muted-foreground">{bin}</span>
          </div>
        )
      },
      sortingFn: 'basic',
    },
    {
      id: 'progress',
      accessorFn: (row) => row.progress.percentage,
      header: '進捗',
      cell: (info) => {
        const p = info.getValue<number>()
        return (
          <div className="flex items-center gap-2">
            <span className="w-9 text-right tabular-nums text-muted-foreground">{p}%</span>
            <div className="h-2 w-16 overflow-hidden rounded-full bg-muted">
              <div className="h-full bg-primary" style={{ width: `${p}%` }} />
            </div>
          </div>
        )
      },
    },
    {
      id: 'createdDate',
      accessorFn: (row) => row.createdDate ?? '',
      header: '作成日',
      cell: (info) => {
        const v = info.getValue<string>()
        return <span className="tabular-nums text-muted-foreground">{v || '–'}</span>
      },
    },
  ], [])

  const table = useReactTable({
    data: plans,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div className="overflow-hidden rounded-lg border">
      <table className="w-full text-sm">
        <thead className="bg-muted/40">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((h) => (
                <th
                  key={h.id}
                  onClick={h.column.getToggleSortingHandler()}
                  className="cursor-pointer px-3 py-2 text-left font-semibold text-muted-foreground"
                >
                  {flexRender(h.column.columnDef.header, h.getContext())}
                  {{ asc: ' ▲', desc: ' ▼' }[h.column.getIsSorted() as string] ?? null}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="border-t hover:bg-muted/30">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-3 py-2 align-middle">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
          {plans.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-3 py-6 text-center text-muted-foreground">
                PLAN がありません
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
