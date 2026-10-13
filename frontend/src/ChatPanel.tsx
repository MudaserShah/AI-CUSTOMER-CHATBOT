import { Fragment, useEffect, useLayoutEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import "./chat.css";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  time: number;
  error?: boolean;
};

type Props = {
  open: boolean;
  messages: ChatMessage[];
  sending: boolean;
  customerId?: string;
  customerName?: string;
  disabled: boolean;
  onSend: (text: string) => void;
  onClose: () => void;
  onNewChat: () => void;
  onRetry: () => void;
};

const SUGGESTIONS = [
  { icon: "📦", label: "Where is my latest order?", text: "Show me my latest order." },
  { icon: "↩︎", label: "I want to return something", text: "I want to request a refund." },
  { icon: "🧾", label: "Check my refund status", text: "Do I have a refund request?" },
  { icon: "📋", label: "What is the refund policy?", text: "What is your refund policy?" },
];

const timeFmt = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit" });
const dayFmt = new Intl.DateTimeFormat("en-US", { weekday: "long", month: "short", day: "numeric" });

function dayLabel(ts: number) {
  const d = new Date(ts);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return dayFmt.format(d);
}

/* ---------- tiny dependency-free markdown renderer ---------- */

function inline(text: string, keyPrefix: string): ReactNode[] {
  // **bold**, `code`, and order/ID-looking tokens (#12345)
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|#\d{3,})/g);
  return parts.map((part, i) => {
    const key = `${keyPrefix}-${i}`;
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4)
      return <strong key={key}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2)
      return <code key={key}>{part.slice(1, -1)}</code>;
    if (/^#\d{3,}$/.test(part)) return <span className="cp-chip" key={key}>{part}</span>;
    return <Fragment key={key}>{part}</Fragment>;
  });
}

function renderRich(content: string): ReactNode {
  const lines = content.replace(/\r/g, "").split("\n");
  const blocks: ReactNode[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;
  let para: string[] = [];

  const flushPara = () => {
    if (para.length) {
      const idx = blocks.length;
      blocks.push(
        <p key={`p${idx}`}>
          {para.map((l, i) => (
            <Fragment key={i}>
              {i > 0 && <br />}
              {inline(l, `p${idx}-${i}`)}
            </Fragment>
          ))}
        </p>,
      );
      para = [];
    }
  };
  const flushList = () => {
    if (list) {
      const idx = blocks.length;
      const items = list.items.map((it, i) => <li key={i}>{inline(it, `l${idx}-${i}`)}</li>);
      blocks.push(list.ordered ? <ol key={`l${idx}`}>{items}</ol> : <ul key={`l${idx}`}>{items}</ul>);
      list = null;
    }
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (bullet || numbered) {
      flushPara();
      const ordered = !!numbered;
      if (list && list.ordered !== ordered) flushList();
      if (!list) list = { ordered, items: [] };
      list.items.push((bullet || numbered)![1]);
    } else if (!line.trim()) {
      flushPara();
      flushList();
    } else {
      flushList();
      para.push(line);
    }
  }
  flushPara();
  flushList();
  return blocks;
}

/* ---------- component ---------- */

export default function ChatPanel({
  open, messages, sending, customerId, customerName, disabled,
  onSend, onClose, onNewChat, onRetry,
}: Props) {
  const [draft, setDraft] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [atBottom, setAtBottom] = useState(true);
  const bodyRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (atBottom) endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending, atBottom]);

  useLayoutEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [draft]);

  if (!open) return null;

  function submit() {
    const text = draft.trim();
    if (!text || sending || disabled) return;
    onSend(text);
    setDraft("");
    setAtBottom(true);
  }

  function onScroll() {
    const el = bodyRef.current;
    if (!el) return;
    setAtBottom(el.scrollHeight - el.scrollTop - el.clientHeight < 80);
  }

  const lastIsError = messages.length > 0 && messages[messages.length - 1].error;
  const firstName = customerName?.split(" ")[0];

  return (
    <section className={`cp-panel ${expanded ? "expanded" : ""}`} role="dialog" aria-label="TechNest support chat">
      <header className="cp-head">
        <div className="cp-head-avatar">
          <span>AI</span>
          <i className="cp-online" />
        </div>
        <div className="cp-head-text">
          <h3>TechNest Support</h3>
          <small>
            <i className="cp-dot" /> Online · usually replies instantly
          </small>
        </div>
        <div className="cp-head-actions">
          <button type="button" onClick={onNewChat} title="Start a new chat" aria-label="Start a new chat">＋</button>
          <button type="button" className="cp-hide-mobile" onClick={() => setExpanded((v) => !v)} title={expanded ? "Shrink" : "Expand"} aria-label="Toggle size">
            {expanded ? "⤡" : "⤢"}
          </button>
          <button type="button" onClick={onClose} title="Close" aria-label="Close chat">✕</button>
        </div>
      </header>

      <div className="cp-body" ref={bodyRef} onScroll={onScroll}>
        {messages.length === 0 ? (
          <div className="cp-welcome">
            <div className="cp-welcome-avatar">AI</div>
            <h4>Hi{firstName ? `, ${firstName}` : ""} 👋</h4>
            <p>I can check your orders, track delivery and handle refund requests. What do you need?</p>
            <div className="cp-suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s.label} type="button" disabled={sending || disabled} onClick={() => onSend(s.text)}>
                  <span>{s.icon}</span>
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="cp-thread">
            {messages.map((m, i) => {
              const prev = messages[i - 1];
              const next = messages[i + 1];
              const newDay = !prev || new Date(prev.time).toDateString() !== new Date(m.time).toDateString();
              const firstInGroup = newDay || !prev || prev.role !== m.role;
              const lastInGroup = !next || next.role !== m.role || next.time - m.time > 5 * 60_000;
              const mine = m.role === "user";
              return (
                <Fragment key={m.id}>
                  {newDay && <div className="cp-day"><span>{dayLabel(m.time)}</span></div>}
                  <div className={`cp-row ${mine ? "mine" : "theirs"} ${firstInGroup ? "first" : ""}`}>
                    {!mine && <div className={`cp-mini-avatar ${lastInGroup ? "" : "ghost"}`}>AI</div>}
                    <div className="cp-col">
                      {firstInGroup && <div className="cp-name">{mine ? "You" : "TechNest AI"}</div>}
                      <div className={`cp-bubble ${m.error ? "error" : ""} ${lastInGroup ? "tail" : ""}`}>
                        {mine ? <p>{m.content}</p> : renderRich(m.content)}
                      </div>
                      {lastInGroup && <div className="cp-time">{timeFmt.format(m.time)}</div>}
                    </div>
                  </div>
                </Fragment>
              );
            })}

            {sending && (
              <div className="cp-row theirs first">
                <div className="cp-mini-avatar">AI</div>
                <div className="cp-col">
                  <div className="cp-bubble typing" aria-label="Assistant is typing">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}

            {lastIsError && !sending && (
              <button type="button" className="cp-retry" onClick={onRetry}>↻ Try again</button>
            )}
          </div>
        )}
        <div ref={endRef} />
      </div>

      {!atBottom && messages.length > 0 && (
        <button type="button" className="cp-jump" onClick={() => endRef.current?.scrollIntoView({ behavior: "smooth" })}>
          ↓ New messages
        </button>
      )}

      <footer className="cp-foot">
        <div className="cp-compose">
          <textarea
            ref={inputRef}
            rows={1}
            value={draft}
            disabled={disabled}
            placeholder={disabled ? "Place an order to start chatting" : "Type your message…"}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault();
                submit();
              }
            }}
          />
          <button type="button" className="cp-send" onClick={submit} disabled={!draft.trim() || sending || disabled} aria-label="Send message">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M12 19V5M5 12l7-7 7 7" /></svg>
          </button>
        </div>
        <div className="cp-foot-note">
          {customerId ? <>Secure session · <code>{customerId}</code></> : "AI can make mistakes — verify important details."}
        </div>
      </footer>
    </section>
  );
}
