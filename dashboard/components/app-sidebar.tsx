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
        <SidebarGroup className="pb-2">
          <SidebarGroupLabel>期間</SidebarGroupLabel>
          <SidebarGroupContent className="group-data-[collapsible=icon]:hidden">
            {dateFilterContent}
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup className="py-2">
          <SidebarGroupLabel>リポジトリ</SidebarGroupLabel>
          <SidebarGroupContent className="group-data-[collapsible=icon]:hidden">
            {filterContent}
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup className="pt-2">
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
