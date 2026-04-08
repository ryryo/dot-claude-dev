import type { Metadata } from "next"
import "./globals.css"
import { Noto_Sans } from "next/font/google";
import { cn } from "@/lib/utils";

const notoSans = Noto_Sans({subsets:['latin'],variable:'--font-sans'});

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
    <html lang="ja" className={cn("font-sans", notoSans.variable)}>
      <body>{children}</body>
    </html>
  )
}
