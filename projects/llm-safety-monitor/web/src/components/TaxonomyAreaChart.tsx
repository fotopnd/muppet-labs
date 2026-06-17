import {
  Area,
  AreaChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TaxonomyBucket } from '@/types'
import { CATEGORY_SHORT_LABELS } from '@/lib/taxonomy-groups'

function formatBucket(iso: string): string {
  return new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit' }).format(
    new Date(iso),
  )
}

type PivotedBucket = { bucket: string; [key: string]: string | number }

function pivotBuckets(buckets: TaxonomyBucket[], categories: string[]): PivotedBucket[] {
  return buckets.map((b) => {
    const row: PivotedBucket = { bucket: b.bucket }
    for (const cat of categories) {
      row[cat] = b.counts[cat] ?? 0
    }
    return row
  })
}

type Props = {
  title: string
  buckets: TaxonomyBucket[]
  categories: string[]
  colors: string[]      // one color per category; recharts requires raw hex
  height?: number
  yMax?: number         // fixed axis ceiling — pass the same value to all sub-charts for comparability
}

export function TaxonomyAreaChart({ title, buckets, categories, colors, height = 160, yMax }: Props) {
  const data = pivotBuckets(buckets, categories)
  const hasData = data.some((b) => categories.some((cat) => ((b[cat] as number) ?? 0) > 0))

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 flex flex-col gap-2">
      <span className="font-sans text-xs font-semibold text-slate-700 uppercase tracking-wide">
        {title}
      </span>
      {!hasData ? (
        <div
          className="flex items-center justify-center"
          style={{ height }}
        >
          <span className="font-sans text-xs text-slate-400">No data yet</span>
        </div>
      ) : (
        <div style={{ height }} className="w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 20, left: 0 }}>
              <XAxis
                dataKey="bucket"
                tickFormatter={formatBucket}
                tick={{ fontSize: 9 }}
                interval="preserveStartEnd"
                angle={-20}
                textAnchor="end"
              />
              <YAxis
                tick={{ fontSize: 9 }}
                width={30}
                domain={yMax !== undefined ? [0, yMax] : [0, 'auto']}
              />
              <Tooltip
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                labelFormatter={(iso: any) => formatBucket(String(iso)) as any}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                formatter={(v: any, name: any) => [v as number, CATEGORY_SHORT_LABELS[String(name)] ?? String(name)] as any}
              />
              <Legend
                wrapperStyle={{ fontSize: 9 }}
                formatter={(value: string) => CATEGORY_SHORT_LABELS[value] ?? value}
              />
              {categories.map((cat, i) => (
                <Area
                  key={cat}
                  type="monotone"
                  dataKey={cat}
                  stackId="1"
                  fill={colors[i % colors.length]}
                  stroke={colors[i % colors.length]}
                  fillOpacity={0.65}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
