type ErrorMessageProps = {
  title: string
  body?: string
}

export function ErrorMessage({ title, body }: ErrorMessageProps) {
  return (
    <div className="rounded-lg border border-danger/20 bg-danger/5 p-4">
      <p className="font-interface text-sm font-medium text-danger">{title}</p>
      {body && <p className="font-interface text-sm text-text-muted mt-1">{body}</p>}
    </div>
  )
}
