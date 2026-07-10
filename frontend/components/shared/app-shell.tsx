import Link from "next/link"
import { MenuIcon } from "lucide-react"
import type { ReactNode } from "react"

import { WorkspaceSwitcher } from "@/features/households"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"

import { SignOutButton } from "./sign-out-button"

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/yearly", label: "Yearly" },
  { href: "/categories", label: "Categories" },
  { href: "/settings", label: "Settings" },
]

function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col bg-background text-foreground">
      <header className="sticky top-0 z-10 border-b bg-card">
        <nav className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-6">
            <span className="text-sm font-semibold tracking-tight">
              Expense Tracker
            </span>
            <div className="hidden items-center gap-6 md:flex">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="hidden items-center gap-3 md:flex">
            <WorkspaceSwitcher />
            <SignOutButton />
          </div>
          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                aria-label="Open menu"
              >
                <MenuIcon />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="flex flex-col">
              <SheetHeader>
                <SheetTitle>Menu</SheetTitle>
              </SheetHeader>
              <div className="flex flex-col gap-1 px-6">
                {NAV_LINKS.map((link) => (
                  <SheetClose asChild key={link.href}>
                    <Link
                      href={link.href}
                      className="rounded-md px-2 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                    >
                      {link.label}
                    </Link>
                  </SheetClose>
                ))}
              </div>
              <SheetFooter className="items-start gap-3">
                <WorkspaceSwitcher />
                <SignOutButton />
              </SheetFooter>
            </SheetContent>
          </Sheet>
        </nav>
      </header>
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-8 sm:px-6">
        {children}
      </div>
    </div>
  )
}

export { AppShell }
