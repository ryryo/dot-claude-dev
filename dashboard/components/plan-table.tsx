"use client"

import { Fragment, ReactNode, useMemo, useState } from 'react'
import {
  ColumnDef,
  ExpandedState,
  flexRender,
  getCoreRowModel,
  getExpandedRowModel,
  getSortedRowModel,
  Row,
  SortingState,
  useReactTable,
} from '@tanstack/react-table'
import { ChevronRight, FileText } from 'lucide-react'

import { PlanMarkdownModal } from '@/components/plan-markdown-modal'
import { Badge } from '@/components/ui/badge'
import { getPlanSize, getSizeBin, SizeBin } from '@/lib/plan-size'
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
  sizeBinFilter: SizeBin | null
  groupByProject: boolean
}

export function PlanTable({ plans, sizeBinFilter, groupByProject }: PlanTableProps) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'size', desc: false }])
  const [expanded, setExpanded] = useState<ExpandedState>({})
  const [modalPlan, setModalPlan] = useState<PlanFile | null>(null)

  const data = useMemo(() => {
    if (!sizeBinFilter) return plans
    return plans.filter((p) => getSizeBin(getPlanSize(p).total) === sizeBinFilter)
  }, [plans, sizeBinFilter])

  const columns = useMemo<ColumnDef<PlanFile>[]>(() => [
    {
      id: 'expander',
      header: () => null,
      cell: ({ row }) => (
        <button
          type="button"
          onClick={row.getToggleExpandedHandler()}
          aria-label={row.getIsExpanded() ? '閉じる' : '開く'}
          className="flex size-6 items-center justify-center rounded hover:bg-muted"
        >
          <ChevronRight
            className={cn(
              'size-4 text-muted-foreground transition-transform',
              row.getIsExpanded() && 'rotate-90'
            )}
          />
        </button>
      ),
    },
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
    {
      id: 'actions',
      header: () => null,
      cell: ({ row }) => (
        <button
          type="button"
          aria-label={`${row.original.title} の全文を読む`}
          onClick={(e) => {
            e.stopPropagation()
            setModalPlan(row.original)
          }}
          className="text-muted-foreground hover:text-foreground"
        >
          <FileText className="size-4" />
        </button>
      ),
    },
  ], [])

  const table = useReactTable({
    data,
    columns,
    state: { sorting, expanded },
    onSortingChange: setSorting,
    onExpandedChange: setExpanded,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowCanExpand: () => true,
  })

  const rows = table.getRowModel().rows

  function renderRow(row: Row<PlanFile>) {
    return (
      <Fragment key={row.id}>
        <tr className="border-t hover:bg-muted/30">
          {row.getVisibleCells().map((cell) => (
            <td key={cell.id} className="px-3 py-2 align-middle">
              {flexRender(cell.column.columnDef.cell, cell.getContext())}
            </td>
          ))}
        </tr>
        {row.getIsExpanded() && (
          <tr className="bg-muted/20">
            <td colSpan={row.getVisibleCells().length} className="px-6 py-3">
              <PlanGateRows plan={row.original} />
            </td>
          </tr>
        )}
      </Fragment>
    )
  }

  let body: ReactNode
  if (groupByProject) {
    const groups = new Map<string, Row<PlanFile>[]>()
    for (const r of rows) {
      const key = r.original.projectName
      const arr = groups.get(key) ?? []
      arr.push(r)
      groups.set(key, arr)
    }
    body = Array.from(groups.entries()).map(([projectName, groupRows]) => (
      <Fragment key={projectName}>
        <tr className="bg-muted/40">
          <td
            colSpan={columns.length}
            className="px-3 py-1.5 text-xs font-semibold text-muted-foreground"
          >
            {projectName} <span className="tabular-nums">({groupRows.length})</span>
          </td>
        </tr>
        {groupRows.map(renderRow)}
      </Fragment>
    ))
  } else {
    body = rows.map(renderRow)
  }

  return (
    <>
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
          {body}
          {data.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-3 py-6 text-center text-muted-foreground">
                {sizeBinFilter
                  ? `規模 ${sizeBinFilter} に該当する PLAN はありません`
                  : 'PLAN がありません'}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
    <PlanMarkdownModal
      open={modalPlan !== null}
      onOpenChange={(open) => {
        if (!open) setModalPlan(null)
      }}
      title={modalPlan?.title ?? ''}
      markdown={modalPlan?.rawMarkdown ?? ''}
    />
    </>
  )
}

function PlanGateRows({ plan }: { plan: PlanFile }) {
  if (plan.gates.length === 0) {
    return <p className="text-xs text-muted-foreground">Gate 情報がありません</p>
  }
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-muted-foreground">
          <th className="w-24 text-left font-medium">Gate</th>
          <th className="text-left font-medium">タイトル</th>
          <th className="w-32 text-right font-medium">Todo 進捗</th>
        </tr>
      </thead>
      <tbody>
        {plan.gates.map((g) => {
          const total = g.todos.length
          const done = g.todos.filter((t) => t.steps.every((s) => s.checked)).length
          return (
            <tr key={g.id} className="border-t border-border/60">
              <td className="py-1 font-mono">{g.id}</td>
              <td className="py-1">{g.title}</td>
              <td className="py-1 text-right tabular-nums">
                {done}/{total}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
