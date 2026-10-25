import * as React from "react"
import { cn } from "@/lib/cn"

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "h-10 w-full rounded-lg border border-slate-700 bg-[#0c1220] px-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-500 focus:outline-none",
      className
    )}
    {...props}
  />
))
Input.displayName = "Input"
