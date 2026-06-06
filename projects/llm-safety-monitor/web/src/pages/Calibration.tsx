import { useCalibration } from '@/api/metrics'
import { CalibrationChart } from '@/components/CalibrationChart'
import { ErrorMessage } from '@/components/ErrorMessage'
import { Skeleton } from '@/components/Skeleton'

export function Calibration() {
  const { data, isLoading, isError } = useCalibration()

  if (isLoading) return <Skeleton className="h-60 w-full" />
  if (isError) return <ErrorMessage message="Failed to load calibration data" />

  const models = data?.models ?? []

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-500">
        Reliability diagrams per model. A well-calibrated model follows the diagonal (confidence = actual positive rate).
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {models.map((m) => (
          <CalibrationChart key={m.model_name} data={m} />
        ))}
      </div>
      {models.length === 0 && (
        <p className="text-center text-gray-400 py-12">No calibration data yet. Ground-truth labels required.</p>
      )}
    </div>
  )
}
