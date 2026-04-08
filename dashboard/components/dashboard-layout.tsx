import type { ReactNode } from "react"

import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"

interface DashboardLayoutProps {
  sidebar: ReactNode
  children: ReactNode
}

export function DashboardLayout({
  sidebar,
  children,
}: DashboardLayoutProps) {
  return (
    <div className="bg-muted/30">
      <div className="flex h-screen overflow-hidden">
        <aside className="w-[280px] shrink-0 bg-background">
          <ScrollArea className="h-screen">
            <div className="space-y-6 p-6">{sidebar}</div>
          </ScrollArea>
        </aside>

        <Separator orientation="vertical" />

        <main className="min-w-0 flex-1 bg-muted/20">
          <ScrollArea className="h-screen">
            <div className="min-h-screen p-6">{children}</div>
          </ScrollArea>
        </main>
      </div>
    </div>
  )
}
