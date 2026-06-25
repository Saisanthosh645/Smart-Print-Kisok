import { Link } from 'react-router-dom'
import { Printer, Upload, CreditCard, BarChart3, Zap } from 'lucide-react'

const features = [
  { icon: Upload, title: 'Upload & Print', desc: 'PDF, DOCX, PPTX — upload from anywhere' },
  { icon: CreditCard, title: 'Online Payment', desc: 'UPI, Cards, Net Banking via Razorpay' },
  { icon: Zap, title: 'Live Tracking', desc: 'Track your job like food delivery' },
  { icon: BarChart3, title: 'Smart Analytics', desc: 'AI cost optimization & queue management' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-brand-700 to-brand-500">
      <header className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-white">
          <Printer className="w-8 h-8" />
          <span className="text-xl font-bold">SmartPrintX</span>
        </div>
        <div className="flex gap-3">
          <Link to="/login" className="text-white hover:text-brand-100 px-4 py-2">Login</Link>
          <Link to="/register" className="bg-white text-brand-700 font-medium px-4 py-2 rounded-lg hover:bg-brand-50">Sign Up</Link>
        </div>
      </header>

      <section className="max-w-6xl mx-auto px-6 py-20 text-center text-white">
        <h1 className="text-5xl font-bold mb-6">Intelligent Campus Printing</h1>
        <p className="text-xl text-brand-100 max-w-2xl mx-auto mb-10">
          Upload documents, pay online, and collect printouts from kiosks — no more queues.
        </p>
        <Link to="/register" className="inline-block bg-white text-brand-700 font-semibold px-8 py-3 rounded-xl hover:bg-brand-50 transition">
          Get Started Free
        </Link>
      </section>

      <section className="max-w-6xl mx-auto px-6 pb-20 grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="bg-white/10 backdrop-blur rounded-xl p-6 text-white">
            <Icon className="w-10 h-10 mb-4" />
            <h3 className="font-semibold text-lg mb-2">{title}</h3>
            <p className="text-brand-100 text-sm">{desc}</p>
          </div>
        ))}
      </section>
    </div>
  )
}
