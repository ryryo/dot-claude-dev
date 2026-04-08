import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "PLAN Dashboard",
  description: "プロジェクト横断 PLAN 管理ダッシュボード",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  )
}
