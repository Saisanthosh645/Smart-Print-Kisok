const STATUS_STEPS = ['uploaded', 'processing', 'queued', 'printing', 'completed']

const STATUS_LABELS = {
  uploaded: 'Uploaded',
  processing: 'Processing',
  queued: 'Queued',
  printing: 'Printing',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
}

export default function JobTracker({ status, history = [] }) {
  const currentIdx = STATUS_STEPS.indexOf(status)
  const isFailed = status === 'failed'

  return (
    <div className="w-full">
      <div className="flex items-center justify-between relative">
        <div className="absolute top-4 left-0 right-0 h-0.5 bg-slate-200" />
        <div
          className="absolute top-4 left-0 h-0.5 bg-brand-500 transition-all duration-500"
          style={{ width: isFailed ? '0%' : `${Math.max(0, currentIdx) / (STATUS_STEPS.length - 1) * 100}%` }}
        />
        {STATUS_STEPS.map((step, idx) => {
          const done = idx <= currentIdx && !isFailed
          const active = idx === currentIdx && !isFailed
          return (
            <div key={step} className="relative flex flex-col items-center z-10">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 ${
                  done
                    ? 'bg-brand-500 border-brand-500 text-white'
                    : active
                    ? 'bg-white border-brand-500 text-brand-500'
                    : 'bg-white border-slate-200 text-slate-400'
                }`}
              >
                {idx + 1}
              </div>
              <span className={`text-xs mt-2 ${done || active ? 'text-brand-700 font-medium' : 'text-slate-400'}`}>
                {STATUS_LABELS[step]}
              </span>
            </div>
          )
        })}
      </div>
      {isFailed && (
        <p className="text-center text-red-600 text-sm mt-4 font-medium">Print job failed — will retry automatically</p>
      )}
      {history?.length > 0 && (
        <div className="mt-6 space-y-1">
          {history.slice(-5).map((h, i) => (
            <p key={i} className="text-xs text-slate-500">
              {STATUS_LABELS[h.status] || h.status} — {new Date(h.at).toLocaleString()}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
