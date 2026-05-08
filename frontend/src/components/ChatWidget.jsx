import { useState, useRef, useEffect } from 'react'
import { sendMessage } from '../api'

const SUGGESTED = {
  website: [
    'What does Jamiiz AI do?',
    'How much does it cost?',
    'Can you help a nonprofit?',
  ],
  property: [
    'What time is check-in?',
    'What is the Wi-Fi password?',
    'What are the house rules?',
  ],
  document: [
    'Summarise this document',
    'What are the key requirements?',
    'Draft a problem statement',
  ],
}

export default function ChatWidget({ assistantType, sessionId, onLeadTrigger }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const history = messages.map((m) => ({
    role: m.role,
    content: m.content,
  }))

  async function send(text) {
    const question = text || input.trim()
    if (!question) return

    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setInput('')
    setLoading(true)

    try {
      const data = await sendMessage({
        message: question,
        assistantType,
        sessionId,
        history,
      })

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources || [],
          confidence: data.confidence,
        },
      ])

      if (data.suggest_booking && onLeadTrigger) {
        onLeadTrigger()
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, something went wrong. Please try again.',
          error: true,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const suggestions = SUGGESTED[assistantType] || []
  const showSuggestions = messages.length === 0

  return (
    <div className="chat-widget">
      {/* Messages */}
      <div className="chat-messages">
        {showSuggestions && (
          <div className="chat-suggestions">
            <p className="suggestions-label">Try asking:</p>
            {suggestions.map((s) => (
              <button key={s} className="suggestion-chip" onClick={() => send(s)}>
                {s}
              </button>
            ))}
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`chat-message ${m.role}`}>
            <div className="message-bubble">
              <p>{m.content}</p>
              {m.sources && m.sources.length > 0 && (
                <div className="message-sources">
                  {m.sources.map((s, j) => (
                    <span key={j} className="source-tag">{s}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-message assistant">
            <div className="message-bubble typing">
              <span /><span /><span />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-row">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Type a message…"
          rows={1}
        />
        <button
          className="chat-send-btn"
          onClick={() => send()}
          disabled={loading || !input.trim()}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  )
}
