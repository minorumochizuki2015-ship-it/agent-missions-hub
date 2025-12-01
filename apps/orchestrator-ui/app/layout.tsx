import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import ContextDrawer from "../components/ContextDrawer"
import FooterStatus from "../components/FooterStatus"
import NavPhase from "../components/NavPhase"
import { Toaster } from "sonner"

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SafeOps Orchestrator Dashboard',
  description: 'Monitor SafeOps KPI, approvals, and CI status',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen antialiased bg-gradient-to-br from-[#0B1220] via-[#0A1328] to-[#0E172D] text-slate-200`}>
        <div className="min-h-screen flex justify-center">
          <div className="w-full max-w-8xl flex text-slate-100">
            <aside className="w-52 lg:w-60 border-r border-white/20 bg-white/10 backdrop-blur-2xl shadow-[0_18px_80px_rgba(15,23,42,0.80)] rounded-r-3xl my-4" role="complementary" aria-label="Docked sidebar">
              <div className="px-4 pt-4 pb-3 text-lg font-semibold tracking-tight text-white/90 drop-shadow-[0_2px_4px_rgba(0,0,0,0.35)]">SafeOps</div>
              <nav className="px-2 pb-4 space-y-1" role="navigation" aria-label="Primary">
                <NavPhase location="sidebar" />
              </nav>
            </aside>
            <div className="flex-1 flex flex-col mx-2 lg:mx-4">
              <header className="border-b border-white/20 bg-white/10 backdrop-blur-2xl shadow-[0_18px_80px_rgba(15,23,42,0.80)] rounded-b-3xl sticky top-0 z-40" role="banner" aria-label="Header">
                <div className="max-w-5xl mx-auto px-4 lg:px-6 py-3 flex items-center justify-between">
                  <div className="font-bold text-lg tracking-tight text-white/90 drop-shadow-[0_2px_4px_rgba(0,0,0,0.35)]">SafeOps Orchestrator</div>
                  <NavPhase location="header" />
                </div>
              </header>
              <main role="main" className="flex-1 flex justify-center px-4 lg:px-6 py-6 lg:py-8">
                <div className="w-full max-w-6xl">{children}</div>
              </main>
              <footer className="border-t border-white/20 bg-white/10 backdrop-blur-2xl shadow-[0_-12px_48px_rgba(15,23,42,0.70)] rounded-t-3xl mb-4" role="contentinfo" aria-label="Footer">
                <div className="max-w-5xl mx-auto px-4 lg:px-6 py-3">
                  <FooterStatus />
                </div>
              </footer>
            </div>
            <aside className="hidden md:block w-56 xl:w-64 border-l border-white/20 bg-white/10 backdrop-blur-2xl shadow-[0_18px_80px_rgba(15,23,42,0.80)] rounded-l-3xl my-4" role="region" aria-label="Context drawer">
              <div className="h-full px-3 py-4 overflow-hidden">
                <ContextDrawer />
              </div>
            </aside>
          </div>
        </div>
        <Toaster />
      </body>
    </html>
  )
}
