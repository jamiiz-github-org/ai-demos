import { useState } from 'react'
import { submitLead } from '../api'

export default function LeadCaptureForm({ assistantType, sessionId, onClose }) {
  const [form, setForm] = useState({ name: '', email: '', business: '', pain_point: '' })
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState(null)

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.name || !form.email) return
    setSubmitting(true)
    setError(null)
    try {
      await submitLead({
        ...form,
        assistant: assistantType,
        session_id: sessionId,
      })
      setSubmitted(true)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="lead-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="lead-modal">
        <button className="lead-close" onClick={onClose}>✕</button>

        {submitted ? (
          <div className="lead-success">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <h3>You're on the list!</h3>
            <p>We'll be in touch within 24 hours to schedule your Free AI Workflow Review.</p>
            <button className="btn-primary" onClick={onClose}>Close</button>
          </div>
        ) : (
          <>
            <div className="lead-header">
              <span className="lead-badge">Free Offer</span>
              <h3>Get a Free AI Workflow Review</h3>
              <p>See exactly where AI can save your team time — no commitment, no sales pitch.</p>
            </div>

            <form onSubmit={handleSubmit} className="lead-form">
              <div className="form-group">
                <label>Your name *</label>
                <input
                  type="text"
                  placeholder="Jane Smith"
                  value={form.name}
                  onChange={(e) => update('name', e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Work email *</label>
                <input
                  type="email"
                  placeholder="jane@company.com"
                  value={form.email}
                  onChange={(e) => update('email', e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Business / Organisation</label>
                <input
                  type="text"
                  placeholder="Acme Corp"
                  value={form.business}
                  onChange={(e) => update('business', e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>What's your biggest time drain right now?</label>
                <textarea
                  placeholder="e.g. answering the same guest questions every day, reviewing contracts manually…"
                  value={form.pain_point}
                  onChange={(e) => update('pain_point', e.target.value)}
                  rows={3}
                />
              </div>

              {error && <p className="form-error">{error}</p>}

              <button type="submit" className="btn-primary" disabled={submitting || !form.name || !form.email}>
                {submitting ? 'Sending…' : 'Book My Free Review →'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
