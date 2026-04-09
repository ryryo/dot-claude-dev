import type { ReactNode } from "react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
} from "@/components/ui/sidebar"

interface AppSidebarProps {
  dateFilterContent: ReactNode
  filterContent: ReactNode
  statsContent: ReactNode
}

export function AppSidebar({
  dateFilterContent,
  filterContent,
  statsContent,
}: AppSidebarProps) {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <h1 className="text-heading-3 px-2 group-data-[collapsible=icon]:hidden">
          PLAN Dashboard
        </h1>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>フィルター</SidebarGroupLabel>
          <SidebarGroupContent className="group-data-[collapsible=icon]:hidden">
            {dateFilterContent}
          </SidebarGroupContent>
          <div className="px-2 py-1">
            {filterContent}
          </div>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel>統計</SidebarGroupLabel>
          <SidebarGroupContent className="group-data-[collapsible=icon]:hidden">
            {statsContent}
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter />
    </Sidebar>
  )
}
