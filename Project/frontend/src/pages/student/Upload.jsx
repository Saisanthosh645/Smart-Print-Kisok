import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload as UploadIcon, Lightbulb, MapPin } from 'lucide-react'
import { student } from '../../api/client'

export default function Upload() {
  const [file, setFile] = useState(null)
  const [uploadedDoc, setUploadedDoc] = useState(null)
  const [options, setOptions] = useState({
    is_color: false,
    is_double_sided: false,
    page_range: '',
    is_urgent: false,
    kiosk_location: '',
  })
  const [estimate, setEstimate] = useState(null)
  const [recommendations, setRecommendations] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (uploadedDoc) {
      student.estimate({ document_id: uploadedDoc.id, options }).then((r) => setEstimate(r.data))
      student.recommendations(uploadedDoc.id).then((r) => setRecommendations(r.data))
    }
  }, [uploadedDoc, options])

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    try {
      const res = await student.uploadDocument(file)
      setUploadedDoc(res.data)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateJob = async () => {
    setLoading(true)
    try {
      const res = await student.createJob({ document_id: uploadedDoc.id, options })
      navigate(`/jobs/${res.data.id}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">Upload & Print</h1>

      {!uploadedDoc ? (
        <div className="card">
          <div
            className="border-2 border-dashed border-slate-300 rounded-xl p-12 text-center hover:border-brand-400 transition cursor-pointer"
            onClick={() => window.document.getElementById('file-input').click()}
          >
            <UploadIcon className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="font-medium mb-2">Drop your file here or click to browse</p>
            <p className="text-sm text-slate-500">PDF, DOCX, PPTX — max 50MB</p>
            <input
              id="file-input"
              type="file"
              accept=".pdf,.docx,.pptx"
              className="hidden"
              onChange={(e) => setFile(e.target.files[0])}
            />
          </div>
          {file && (
            <div className="mt-4 flex items-center justify-between">
              <span className="text-sm">{file.name}</span>
              <button onClick={handleUpload} className="btn-primary" disabled={loading}>
                {loading ? 'Uploading...' : 'Upload & Analyze'}
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="card">
            <h2 className="font-semibold mb-2">{uploadedDoc.filename}</h2>
            <p className="text-sm text-slate-500">{uploadedDoc.page_count} pages · {uploadedDoc.file_type.toUpperCase()}</p>
            {uploadedDoc.analysis?.recommendations?.length > 0 && (
              <div className="mt-4 p-3 bg-amber-50 rounded-lg">
                <p className="text-sm font-medium flex items-center gap-1"><Lightbulb className="w-4 h-4" /> AI Analysis</p>
                <ul className="text-sm text-slate-600 mt-2 list-disc list-inside">
                  {uploadedDoc.analysis.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            )}
          </div>

          <div className="card grid md:grid-cols-2 gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={options.is_color} onChange={(e) => setOptions({ ...options, is_color: e.target.checked })} />
              Color printing
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={options.is_double_sided} onChange={(e) => setOptions({ ...options, is_double_sided: e.target.checked })} />
              Double-sided
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={options.is_urgent} onChange={(e) => setOptions({ ...options, is_urgent: e.target.checked })} />
              Urgent (+ priority)
            </label>
            <div>
              <label className="label">Page Range (e.g. 1-5, 8)</label>
              <input className="input" placeholder="All pages" value={options.page_range} onChange={(e) => setOptions({ ...options, page_range: e.target.value })} />
            </div>
          </div>

          {estimate && (
            <div className="card bg-brand-50 border-brand-200">
              <h3 className="font-semibold mb-3">Cost Calculator</h3>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div><p className="text-sm text-slate-500">Pages</p><p className="text-xl font-bold">{estimate.pages_to_print}</p></div>
                <div><p className="text-sm text-slate-500">Sheets</p><p className="text-xl font-bold">{estimate.sheets_required}</p></div>
                <div><p className="text-sm text-slate-500">Total</p><p className="text-xl font-bold text-brand-700">₹{estimate.cost}</p></div>
              </div>
              {estimate.optimization_suggestions?.map((s, i) => (
                <p key={i} className="text-sm text-brand-700 flex items-center gap-1"><Lightbulb className="w-3 h-3" /> {s}</p>
              ))}
            </div>
          )}

          {recommendations?.fastest_collection && (
            <div className="card">
              <p className="text-sm flex items-center gap-1"><MapPin className="w-4 h-4" /> Fastest kiosk: {recommendations.fastest_collection.name} — ~{recommendations.fastest_collection.estimated_wait_minutes} min wait</p>
            </div>
          )}

          <button onClick={handleCreateJob} className="btn-primary w-full py-3 text-lg" disabled={loading}>
            Create Print Job — ₹{estimate?.cost || '...'}
          </button>
        </div>
      )}
    </div>
  )
}
