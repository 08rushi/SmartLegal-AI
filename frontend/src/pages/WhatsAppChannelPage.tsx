import { Link } from 'react-router-dom'
import WhatsAppHero from '../components/whatsapp/WhatsAppHero'
import WhatsAppConnectionCard from '../components/whatsapp/WhatsAppConnectionCard'
import WhatsAppCapabilities from '../components/whatsapp/WhatsAppCapabilities'
import WhatsAppHowItWorks from '../components/whatsapp/WhatsAppHowItWorks'
import WhatsAppDocumentUseCase from '../components/whatsapp/WhatsAppDocumentUseCase'
import WhatsAppLanguageSupport from '../components/whatsapp/WhatsAppLanguageSupport'
import WhatsAppSecuritySection from '../components/whatsapp/WhatsAppSecuritySection'

export default function WhatsAppChannelPage() {
  const scrollToConnection = () => {
    const el = document.getElementById('connection-card')
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <div className="page-shell bg-app min-h-screen py-10 px-4 sm:px-6 lg:px-8 space-y-12">
      <div className="content-wrap max-w-6xl mx-auto space-y-12">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Link to="/" className="hover:text-amber-400 transition">
            Home
          </Link>
          <span>/</span>
          <span className="text-slate-300">Channels</span>
          <span>/</span>
          <span className="text-emerald-400 font-medium">WhatsApp AI Channel</span>
        </div>

        {/* Hero Section */}
        <WhatsAppHero onStartClick={scrollToConnection} />

        {/* Connection Status Card */}
        <WhatsAppConnectionCard state="preparing" onStartClick={scrollToConnection} />

        {/* What Can You Do Section */}
        <WhatsAppCapabilities />

        {/* How It Works */}
        <WhatsAppHowItWorks />

        {/* Document Use Case */}
        <WhatsAppDocumentUseCase />

        {/* Multilingual Support */}
        <WhatsAppLanguageSupport />

        {/* Security Section */}
        <WhatsAppSecuritySection />

        {/* Final CTA Re-anchor */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8 sm:p-12 text-center space-y-6 shadow-2xl">
          <h2 className="text-2xl font-bold text-white sm:text-3xl tracking-tight">
            Ready to experience SmartLegal AI on WhatsApp?
          </h2>
          <p className="text-sm text-slate-300 max-w-xl mx-auto">
            Ask questions, send documents, and receive clear legal guidance straight to your WhatsApp chat.
          </p>
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={scrollToConnection}
              className="w-full sm:w-auto rounded-xl bg-[linear-gradient(180deg,#25D366,#128C7E)] px-6 py-3.5 text-sm font-semibold text-slate-950 shadow-[0_10px_30px_rgba(37,211,102,0.3)] transition hover:brightness-110"
            >
              Start on WhatsApp →
            </button>
            <Link
              to="/"
              className="w-full sm:w-auto rounded-xl border border-slate-700 bg-slate-800/80 px-6 py-3.5 text-sm font-medium text-slate-200 hover:bg-slate-800 hover:text-white transition"
            >
              Back to SmartLegal AI
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
