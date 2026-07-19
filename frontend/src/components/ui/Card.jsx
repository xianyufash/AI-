import { cn } from '../../lib/utils'

export function Card({ className, ...props }, ref) {
  return (
    <div
      ref={ref}
      className={cn('rounded-lg border border-gray-200 bg-white', className)}
      {...props}
    />
  )
}

export function CardHeader({ className, ...props }, ref) {
  return (
    <div
      ref={ref}
      className={cn('flex flex-col space-y-1.5 p-6', className)}
      {...props}
    />
  )
}

export function CardTitle({ className, ...props }, ref) {
  return (
    <h3
      ref={ref}
      className={cn('text-lg font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  )
}

export function CardContent({ className, ...props }, ref) {
  return (
    <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
  )
}
