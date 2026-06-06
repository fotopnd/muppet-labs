export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
      {message}
    </div>
  )
}
