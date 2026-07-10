import type { Metadata } from "next"
import { Geist_Mono, Inter } from "next/font/google"

import "./globals.css"
import { cn } from "@/lib/utils"
import { Providers } from "@/providers/providers"

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" })

export const metadata: Metadata = {
  title: "Expense Tracker",
  description:
    "Private budgeting for you and your household: multi-currency expense tracking, monthly budget insights, and shared household budgets.",
}

const fontMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn("antialiased", fontMono.variable, "font-sans", inter.variable)}
    >
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
