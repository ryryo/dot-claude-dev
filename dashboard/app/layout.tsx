import type { Metadata } from "next"
import "./globals.css"
import { Inter, Noto_Sans_JP, IBM_Plex_Mono } from "next/font/google"
import { cn } from "@/lib/utils"
import { Toaster } from "@/components/ui/sonner"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
})

const notoSansJP = Noto_Sans_JP({
  subsets: ["latin"],
  variable: "--font-jp",
  display: "swap",
  weight: ["400", "500", "600", "700"],
})

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
})

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
    <html lang="ja" className={cn(inter.variable, notoSansJP.variable, ibmPlexMono.variable)}>
      <body suppressHydrationWarning>
        {children}
        <Toaster richColors closeButton position="top-right" />
      </body>
    </html>
  )
}
