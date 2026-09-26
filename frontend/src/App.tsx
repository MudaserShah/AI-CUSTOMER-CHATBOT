import { useState } from 'react'
import './App.css'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

function App() {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)

  const customerId = 'customer-002'
  const threadId = 'frontend-test-001'

  async function sendMessage() {
    if (!message.trim() || loading) return

    const userMessage = message.trim()

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: userMessage,
      },
    ])

    setMessage('')
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_id: customerId,
          thread_id: threadId,
          message: userMessage,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response from server')
      }

      const data = await response.json()

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response,
        },
      ])
    } catch (error) {
      console.error(error)

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Sorry, I could not connect to the customer support server.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(
    event: React.KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>TechNest Support</h1>
          <p>AI Customer Support Assistant</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Online
        </div>
      </header>

      <main className="chat-container">
        {messages.length === 0 && (
          <div className="welcome">
            <h2>How can I help you?</h2>
            <p>
              Ask about your order, refund, or delivery address.
            </p>

            <div className="examples">
              <button
                onClick={() =>
                  setMessage('Where is my order 12346?')
                }
              >
                📦 Check order
              </button>

              <button
                onClick={() =>
                  setMessage(
                    'I want a refund for order 12349 because the product is defective.',
                  )
                }
              >
                💰 Request refund
              </button>

              <button
                onClick={() =>
                  setMessage(
                    'I want to change the delivery address of order 12346.',
                  )
                }
              >
                📍 Change address
              </button>
            </div>
          </div>
        )}

        <div className="messages">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message-row ${msg.role}`}
            >
              <div className="message-bubble">
                {msg.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row assistant">
              <div className="message-bubble typing">
                Thinking...
              </div>
            </div>
          )}
        </div>
      </main>

      <div className="input-area">
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask me about your order..."
          rows={1}
          disabled={loading}
        />

        <button
          onClick={sendMessage}
          disabled={!message.trim() || loading}
        >
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  )
}

export default App