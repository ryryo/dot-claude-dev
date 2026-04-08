import type { ReactNode } from "react"

import { AppSidebar } from "@/components/app-sidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"

interface DashboardLayoutProps {
  filterContent: ReactNode
  statsContent: ReactNode
  children: ReactNode
}

export function DashboardLayout({
  filterContent,
  statsContent,
  children,
}: DashboardLayoutProps) {
  return (
    <SidebarProvider>
      <AppSidebar filterContent={filterContent} statsContent={statsContent} />
      <SidebarInset>
        <header className="flex items-center gap-2 border-b px-4 py-3">
          <SidebarTrigger />
        </header>
        <main id="main-content" className="flex-1 overflow-auto p-4 md:p-6">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
