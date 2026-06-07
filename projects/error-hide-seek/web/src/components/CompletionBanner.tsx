export function CompletionBanner() {
  return (
    <div className="rounded-lg border border-border bg-slate-50 p-4 flex items-center gap-3">
      <span className="text-success font-data text-lg">✓</span>
      <p className="font-interface text-sm text-text-default">
        Session submitted. Results are being compiled.
      </p>
    </div>
  )
}
