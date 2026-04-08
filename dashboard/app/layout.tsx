import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Next.js dashboard bootstrap with shadcn/ui Base UI components.",
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
