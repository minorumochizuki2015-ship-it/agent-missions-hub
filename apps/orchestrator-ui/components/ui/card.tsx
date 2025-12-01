import * as React from "react"

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className = "", children, ...props }, ref) => (
  <div
    ref={ref}
    className={`relative rounded-3xl border border-white/40 bg-white/20 backdrop-blur-2xl shadow-[0_8px_32px_rgba(0,0,0,0.35)] ring-1 ring-white/10 ${className}`}
    {...props}
  >
    <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-white/40 to-white/5 opacity-60 pointer-events-none" />
    <div className="relative">
      {children}
    </div>
  </div>
))
Card.displayName = "Card"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className = "", ...props }, ref) => (
  <div ref={ref} className={`relative flex flex-col space-y-1.5 p-6 md:p-8 ${className}`} {...props} />
))
CardHeader.displayName = "CardHeader"

interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: number
}

const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  CardTitleProps
>(({ className = "", level = 2, role = "heading", ...props }, ref) => (
  <h2
    ref={ref}
    role={role}
    aria-level={level}
    className={`text-2xl md:text-3xl font-semibold leading-none tracking-tight text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)] ${className}`}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className = "", ...props }, ref) => (
  <div ref={ref} className={`relative p-6 md:p-8 pt-0 md:pt-0 space-y-4 text-slate-200/90 ${className}`} {...props} />
))
CardContent.displayName = "CardContent"

export { Card, CardHeader, CardTitle, CardContent }
