import { Skeleton } from './Skeleton'

export function FeedItemSkeleton() {
  return (
    <li className="flex items-center gap-3 py-3 border-b border-border">
      <Skeleton className="h-4 w-28" />
      <Skeleton className="h-5 w-12" />
      <Skeleton className="h-4 w-16 ml-auto" />
    </li>
  )
}
