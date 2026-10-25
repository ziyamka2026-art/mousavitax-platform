import * as React from "react"
import { cn } from "@/lib/cn"

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline"
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-lg px-4 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variant === "default"
          ? "bg-blue-600 text-white hover:bg-blue-500"
          : "border border-slate-700 bg-transparent text-slate-200 hover:bg-slate-800",
        className
      )}
      {...props}
    />
  )
)
Button.displayName = "Button"
