import { Skeleton } from './Skeleton'

export function ModelCardSkeleton() {
  return (
    <article className="bg-surface rounded-lg border border-border p-5 flex flex-col gap-4">
      <div className="flex justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-5 w-16" />
      </div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-3">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </div>
      <Skeleton className="h-12 w-full" />
    </article>
  )
}
