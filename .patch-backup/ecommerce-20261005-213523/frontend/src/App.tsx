import { useEffect, useRef, useState } from 'react'
import './App.css'
import { ApiError, requestToken, sendChatMessage } from './api'

type Message = {
  role: 'user' | 'assistant' | 'system'
  content: string
}

type Screen = 'identify' | 'chat'

function makeThreadId() {
  return `thread-${Math.random().toString(36).slice(2, 10)}`
}

function App() {
  const [screen, setScreen] = useState<Screen>('identify')

  // Identify form
  const [customerId, setCustomerId] = useState('')
  const [email, setEmail] = useState('')
  const [identifyError, setIdentifyError] = useState('')
  const [verifying, setVerifying] = useState(false)

  // Session
  const [token, setToken] = useState('')
  const [threadId] = useState(makeThreadId)

  // Chat
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [sending, setSending] = useState(false)

  const scrollAnchor = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollAnchor.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  async function handleIdentify(event: React.FormEvent) {
    event.preventDefault()
    if (!customerId.trim() || !email.trim() || verifying) return

    setIdentifyError('')
    setVerifying(true)

    try {
      const result = await requestToken(customerId.trim(), email.trim())
      setToken(result.access_token)
      setScreen('chat')
    } catch (error) {
      setIdentifyError(
        error instanceof ApiError ? error.message : 'Something went wrong. Please try again.',
      )
    } finally {
      setVerifying(false)
    }
  }

  function returnToIdentify(noticeText: string) {
    setToken('')
    setScreen('identify')
    setMessages([])
    setIdentifyError(noticeText)
  }

  async function sendMessage() {
    if (!message.trim() || sending) return

    const userMessage = message.trim()
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setMessage('')
    setSending(true)

    try {
      const data = await sendChatMessage(token, threadId, userMessage)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
    } catch (error) {
      if (error instanceof ApiError && error.message === 'SESSION_EXPIRED') {
        returnToIdentify('Your session expired. Please verify your details again.')
        return
      }
      setMessages((prev) => [
        ...prev,
        {
          role: 'system',
          content:
            error instanceof ApiError
              ? error.message
              : 'Could not reach the support server. Please try again.',
        },
      ])
    } finally {
      setSending(false)
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  if (screen === 'identify') {
    return (
      <div className="gate">
        <form className="gate-panel" onSubmit={handleIdentify}>
          <div className="gate-mark">⎔</div>
          <h1>TechNest Support</h1>
          <p className="gate-subtitle">Verify your details to start a session</p>

          <label>
            Customer ID
            <input
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              placeholder="customer-002"
              autoFocus
            />
          </label>

          <label>
            Email on file
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </label>

          {identifyError && <div className="gate-error">{identifyError}</div>}

          <button type="submit" disabled={verifying}>
            {verifying ? 'Verifying…' : 'Start session'}
          </button>
        </form>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-mark">⎔</span>
          <div>
            <h1>TechNest Support</h1>
            <p>AI customer support assistant</p>
          </div>
        </div>

        <div className="session">
          <span className="session-id">{customerId}</span>
          <span className="status">
            <span className="status-dot" />
            connected
          </span>
        </div>
      </header>

      <main className="chat-container">
        {messages.length === 0 && (
          <div className="welcome">
            <h2>How can I help?</h2>
            <p>Ask about an order, a refund, or a delivery address.</p>

            <div className="examples">
              <button onClick={() => setMessage('Where is my order 12346?')}>
                Track an order
              </button>
              <button
                onClick={() =>
                  setMessage('I want a refund for order 12345 because the product is defective.')
                }
              >
                Request a refund
              </button>
              <button
                onClick={() => setMessage('I want to change the delivery address for order 12346.')}
              >
                Update delivery address
              </button>
            </div>
          </div>
        )}

        <div className="messages">
          {messages.map((msg, index) => (
            <div key={index} className={`message-row ${msg.role}`}>
              <div className="message-bubble">{msg.content}</div>
            </div>
          ))}

          {sending && (
            <div className="message-row assistant">
              <div className="message-bubble typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          )}

          <div ref={scrollAnchor} />
        </div>
      </main>

      <div className="input-area">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your order…"
          rows={1}
          disabled={sending}
        />
        <button onClick={sendMessage} disabled={!message.trim() || sending}>
          Send
        </button>
      </div>
    </div>
  )
}

export default App
