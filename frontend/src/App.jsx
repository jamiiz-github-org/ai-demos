import { useState } from 'react'
import ChatWidget from './components/ChatWidget'
import FileUpload from './components/FileUpload'
import LeadCaptureForm from './components/LeadCaptureForm'
import './App.css'

const SESSION_ID = `demo-${Date.now()}`

const DEMOS = [
  {
    id: 'website',
    assistantType: 'website',
    label: 'Website Assistant',
    tag: 'Lead Generation',
    tagColor: 'orange',
    headline: 'An AI that works your website 24/7',
    description:
      'Answers questions about your business, services, and pricing — and turns visitors into leads without you lifting a finger.',
    pitch: 'Imagine this on your website capturing leads and answering customer questions around the clock.',
  },
  {
    id: 'property',
    assistantType: 'property',
    label: 'Guest Assistant',
    tag: 'Property & Hospitality',
    tagColor: 'green',
    headline: 'Stop answering the same guest questions',
    description:
      'Check-in times, house rules, local recommendations — your guests get instant answers, you get your time back.',
    pitch: 'Imagine your guests getting instant answers without you replying to the same messages every day.',
  },
  {
    id: 'document',
    assistantType: 'document',
    label: 'Document Assistant',
    tag: 'Document Intelligence',
    tagColor: 'blue',
    headline: 'Ask questions across any document',
    description:
      'Upload a grant, contract, policy, or SOP — then ask anything. Summarise, extract key info, or draft a response.',
    pitch: 'Imagine your team asking questions across grants, policies, and SOPs instead of searching manually.',
  },
]

export default function App() {
  const [activeDemo, setActiveDemo] = useState('website')
  const [showLead, setShowLead] = useState(false)

  const current = DEMOS.find((d) => d.id === activeDemo)

  return (
    <div className="app">

      {/* ── NAV ── */}
      <header className="nav">
        <div className="nav-inner">
          <div className="nav-logo">
            <span className="logo-icon">J</span>
            <span className="logo-text">Jamiiz <span>AI</span></span>
          </div>
          <nav className="nav-links">
            <a href="https://ai.jamiiz.io" target="_blank" rel="noopener">Website</a>
            <a href="#demos">Demos</a>
            <button className="btn-nav-cta" onClick={() => setShowLead(true)}>
              Free AI Review
            </button>
          </nav>
        </div>
      </header>

      {/* ── HERO ── */}
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-badge">Live Demo Lab</div>
          <h1>AI that works while<br /><span>you sleep</span></h1>
          <p className="hero-sub">
            Three real AI assistants — trained on real business content. Pick one and start chatting.
          </p>
          <div className="hero-cta-row">
            <button className="btn-primary" onClick={() => document.getElementById('demos').scrollIntoView({ behavior: 'smooth' })}>
              Try the Demos
            </button>
            <button className="btn-ghost" onClick={() => setShowLead(true)}>
              Get a Free AI Review
            </button>
          </div>
        </div>
        <div className="hero-bg-grid" />
      </section>

      {/* ── DEMOS ── */}
      <section className="demos-section" id="demos">
        <div className="demos-inner">
          <div className="demos-header">
            <h2>Three demos. One backend.</h2>
            <p>Each assistant is trained on real content. Adding a new one takes hours, not months.</p>
          </div>

          {/* Tab switcher */}
          <div className="demo-tabs">
            {DEMOS.map((d) => (
              <button
                key={d.id}
                className={`demo-tab ${activeDemo === d.id ? 'active' : ''}`}
                onClick={() => setActiveDemo(d.id)}
              >
                <span className={`demo-tab-dot ${d.tagColor}`} />
                {d.label}
              </button>
            ))}
          </div>

          {/* Active demo panel */}
          <div className="demo-panel">
            <div className="demo-info">
              <span className={`demo-tag ${current.tagColor}`}>{current.tag}</span>
              <h3>{current.headline}</h3>
              <p>{current.description}</p>
              <div className="demo-pitch">
                <span className="pitch-icon">💡</span>
                <em>{current.pitch}</em>
              </div>
              {activeDemo === 'document' && (
                <FileUpload onUploaded={() => {}} />
              )}
            </div>

            <div className="demo-chat">
              <div className="chat-header">
                <span className={`chat-dot ${current.tagColor}`} />
                <span>{current.label}</span>
                <span className="chat-live">● Live</span>
              </div>
              <ChatWidget
                key={activeDemo}
                assistantType={current.assistantType}
                sessionId={`${SESSION_ID}-${activeDemo}`}
                onLeadTrigger={() => setShowLead(true)}
              />
            </div>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="how-section">
        <div className="how-inner">
          <h2>How it works</h2>
          <div className="how-steps">
            {[
              { n: '01', title: 'We learn your business', body: 'We ingest your documents, website, workflows — whatever content drives your team.' },
              { n: '02', title: 'We build your assistant', body: 'A custom AI trained on your content, with your voice, your rules, your escalation triggers.' },
              { n: '03', title: 'It goes live in days', body: 'Embedded on your site, your Slack, your inbox — wherever the work actually happens.' },
            ].map((s) => (
              <div key={s.n} className="how-step">
                <div className="step-number">{s.n}</div>
                <h4>{s.title}</h4>
                <p>{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA STRIP ── */}
      <section className="cta-strip">
        <div className="cta-strip-inner">
          <h2>Ready to see what AI can do for your business?</h2>
          <p>Free 60-minute AI Workflow Review. No commitment. No sales pitch.</p>
          <button className="btn-primary large" onClick={() => setShowLead(true)}>
            Book My Free Review →
          </button>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <span className="logo-icon sm">J</span>
            <span className="logo-text sm">Jamiiz <span>AI</span></span>
          </div>
          <p>© 2025 Jamiiz AI Systems. Built to automate the work that slows you down.</p>
          <a href="https://ai.jamiiz.io" target="_blank" rel="noopener">ai.jamiiz.io</a>
        </div>
      </footer>

      {/* ── LEAD MODAL ── */}
      {showLead && (
        <LeadCaptureForm
          assistantType={current.assistantType}
          sessionId={SESSION_ID}
          onClose={() => setShowLead(false)}
        />
      )}
    </div>
  )
}
