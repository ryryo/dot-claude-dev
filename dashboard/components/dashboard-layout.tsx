import type { ReactNode } from "react"

import { AppSidebar } from "@/components/app-sidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"

interface DashboardLayoutProps {
  dateFilterContent: ReactNode
  filterContent: ReactNode
  sizeFilterContent: ReactNode
  statsContent: ReactNode
  headerContent?: ReactNode
  children: ReactNode
}

export function DashboardLayout({
  dateFilterContent,
  filterContent,
  sizeFilterContent,
  statsContent,
  headerContent,
  children,
}: DashboardLayoutProps) {
  return (
    <SidebarProvider>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        メインコンテンツへスキップ
      </a>
      <AppSidebar
        dateFilterContent={dateFilterContent}
        filterContent={filterContent}
        sizeFilterContent={sizeFilterContent}
        statsContent={statsContent}
      />
      <SidebarInset>
        <header className="flex items-center gap-4 border-b px-4 py-3">
          <SidebarTrigger />
          {headerContent && <div className="flex flex-1 items-center">{headerContent}</div>}
        </header>
        <main id="main-content" className="flex-1 overflow-auto p-4 md:p-6">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
