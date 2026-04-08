import { Skeleton } from "@/components/ui/skeleton"

export function SkeletonDashboard() {
  return (
    <div className="flex h-svh">
      <aside className="hidden w-[280px] shrink-0 border-r p-6 lg:block">
        <div className="space-y-6">
          <div className="space-y-3">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-4 w-48" />
          </div>
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))}
        </div>
      </aside>
      <main className="flex-1 p-6">
        <div className="space-y-6">
          <Skeleton className="h-8 w-48" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-96 rounded-xl" />
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
