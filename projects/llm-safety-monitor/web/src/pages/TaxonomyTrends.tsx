import { useTaxonomyTimeseries } from '@/api/metrics'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Skeleton } from '@/components/Skeleton'
import { TaxonomyAreaChart } from '@/components/TaxonomyAreaChart'
import { TAXONOMY_GROUPS } from '@/lib/taxonomy-groups'
import type { TaxonomyBucket } from '@/types'

// Build top-level overview data: each bucket sums subcategory counts per group
function buildOverviewData(
  buckets: TaxonomyBucket[],
): Array<{ bucket: string; [key: string]: string | number }> {
  return buckets.map((b) => {
    const row: { bucket: string; [key: string]: string | number } = { bucket: b.bucket }
    for (const group of TAXONOMY_GROUPS) {
      row[group.label] = group.categories.reduce((sum, cat) => sum + (b.counts[cat] ?? 0), 0)
    }
    return row
  })
}

export function TaxonomyTrends() {
  const { data, isLoading, isError } = useTaxonomyTimeseries()

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-52 w-full" />
        <div className="grid grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return <ErrorMessage message="Failed to load taxonomy trends" />
  }

  const buckets = data?.buckets ?? []

  // Overview chart uses the aggregated group-level data — passed as synthetic TaxonomyBucket[]
  // We convert back to TaxonomyBucket format so TaxonomyAreaChart's pivot works uniformly
  const overviewBuckets: TaxonomyBucket[] = buckets.map((b) => ({
    bucket: b.bucket,
    counts: Object.fromEntries(
      TAXONOMY_GROUPS.map((g) => [
        g.label,
        g.categories.reduce((sum, cat) => sum + (b.counts[cat] ?? 0), 0),
      ]),
    ),
  }))

  const overviewCategories = TAXONOMY_GROUPS.map((g) => g.label)
  const overviewColors = TAXONOMY_GROUPS.map((g) => g.color)

  // Shared Y-axis ceiling for all 4 sub-charts: max stacked total across any group/bucket
  const subChartYMax = Math.max(
    1,
    ...TAXONOMY_GROUPS.flatMap((group) =>
      buckets.map((b) =>
        group.categories.reduce((sum, cat) => sum + (b.counts[cat] ?? 0), 0),
      ),
    ),
  )

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="font-sans text-base font-semibold text-slate-900">
          Harm Category Trends
        </h2>
        <span className="font-sans text-xs text-slate-400">Daily buckets</span>
      </div>

      {/* Top chart: 4 top-level groups as stacked areas */}
      <TaxonomyAreaChart
        title="All Groups"
        buckets={overviewBuckets}
        categories={overviewCategories}
        colors={overviewColors}
        height={200}
      />

      {/* 4 sub-charts: one per group, shared Y axis for direct comparability */}
      <div className="grid grid-cols-2 gap-4">
        {TAXONOMY_GROUPS.map((group) => (
          <TaxonomyAreaChart
            key={group.id}
            title={group.label}
            buckets={buckets}
            categories={group.categories as unknown as string[]}
            colors={group.subColors as unknown as string[]}
            height={160}
            yMax={subChartYMax}
          />
        ))}
      </div>
    </div>
  )
}
