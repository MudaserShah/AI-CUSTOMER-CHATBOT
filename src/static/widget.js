/**
 * AI Customer Chatbot — Standalone Embeddable Widget
 * Encapsulated via Shadow DOM for 100% style isolation.
 * Works on any website (Shopify, WordPress, Webflow, React, HTML).
 */
(function () {
  if (window.__AI_CHATBOT_WIDGET_LOADED__) return;
  window.__AI_CHATBOT_WIDGET_LOADED__ = true;

  // 1. Read configuration from script tag attributes
  const currentScript =
    document.currentScript ||
    document.querySelector("script[data-project-id]") ||
    document.querySelector("script[src*='widget.js']");

  const projectId = currentScript?.getAttribute("data-project-id") || "technest-default";
  const apiKey = currentScript?.getAttribute("data-api-key") || "";
  const apiUrl =
    currentScript?.getAttribute("data-api-url") ||
    (currentScript?.src ? new URL(currentScript.src).origin : "http://localhost:8000");

  let customerEmail = currentScript?.getAttribute("data-customer-email") || "";
  let customerName = currentScript?.getAttribute("data-customer-name") || "";

  // Public SDK for host websites (Shopify, WooCommerce, React)
  window.AIWidget = {
    identify: function (user) {
      if (!user) return;
      if (user.email) customerEmail = user.email;
      if (user.name) customerName = user.name;
    },
    open: function () { if (!isOpen) toggleChat(); },
    close: function () { if (isOpen) toggleChat(); },
    toggle: function () { toggleChat(); },
  };

  const storageKeyThread = `ai_widget_thread_${projectId}`;
  const storageKeyHistory = `ai_widget_history_${projectId}`;

  let threadId = localStorage.getItem(storageKeyThread);
  if (!threadId) {
    threadId = "wid-" + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
    localStorage.setItem(storageKeyThread, threadId);
  }

  // 2. Fetch project configuration
  let config = {
    project_id: projectId,
    name: "AI Assistant",
    widget_title: "Customer Support",
    widget_greeting: "Hello! How can I help you today?",
    primary_color: "#2563eb",
  };

  async function fetchConfig() {
    try {
      const url = new URL(`${apiUrl}/widget/config`);
      if (apiKey) url.searchParams.set("api_key", apiKey);
      else url.searchParams.set("project_id", projectId);

      const res = await fetch(url.toString());
      if (res.ok) {
        const data = await res.json();
        config = { ...config, ...data };
        updateWidgetBranding();
      }
    } catch (err) {
      console.warn("[AI Widget] Using default configuration:", err);
    }
  }

  // 3. Create host element and Shadow Root
  const host = document.createElement("div");
  host.id = "ai-chatbot-widget-container";
  document.body.appendChild(host);
  const shadow = host.attachShadow({ mode: "open" });

  // 4. Widget CSS
  const styles = `
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    
    :host {
      --primary: ${config.primary_color};
      --primary-hover: #1d4ed8;
      --bg-panel: #ffffff;
      --text-dark: #0f172a;
      --text-muted: #64748b;
      --bubble-bot: #f1f5f9;
      --bubble-user: var(--primary);
      --border-color: #e2e8f0;
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 999999;
      display: block;
    }

    .launcher-btn {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: var(--primary);
      box-shadow: 0 8px 24px rgba(37, 99, 235, 0.35);
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      outline: none;
    }

    .launcher-btn:hover {
      transform: scale(1.08);
      box-shadow: 0 12px 32px rgba(37, 99, 235, 0.45);
    }

    .launcher-btn svg {
      width: 28px;
      height: 28px;
      fill: currentColor;
      transition: transform 0.2s ease;
    }

    .chat-panel {
      position: absolute;
      bottom: 76px;
      right: 0;
      width: 380px;
      height: 580px;
      max-width: calc(100vw - 32px);
      max-height: calc(100vh - 120px);
      background: var(--bg-panel);
      border-radius: 20px;
      box-shadow: 0 20px 48px -8px rgba(15, 23, 42, 0.2), 0 0 0 1px rgba(15, 23, 42, 0.05);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      opacity: 0;
      pointer-events: none;
      transform: translateY(16px) scale(0.96);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .chat-panel.open {
      opacity: 1;
      pointer-events: auto;
      transform: translateY(0) scale(1);
    }

    .header {
      background: linear-gradient(135deg, var(--primary) 0%, #1e40af 100%);
      color: #ffffff;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .header-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .header-avatar {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 16px;
      backdrop-filter: blur(4px);
    }

    .header-title-box h3 {
      font-size: 15px;
      font-weight: 600;
      line-height: 1.2;
    }

    .header-status {
      font-size: 11px;
      opacity: 0.85;
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .status-dot {
      width: 7px;
      height: 7px;
      background: #22c55e;
      border-radius: 50%;
    }

    .close-btn {
      background: none;
      border: none;
      color: #ffffff;
      cursor: pointer;
      opacity: 0.8;
      padding: 4px;
      border-radius: 6px;
      transition: opacity 0.2s;
    }

    .close-btn:hover { opacity: 1; background: rgba(255, 255, 255, 0.15); }

    .messages-container {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      background: #fafaf9;
    }

    .msg {
      max-width: 86%;
      padding: 12px 16px;
      font-size: 13.5px;
      line-height: 1.55;
      border-radius: 16px;
      word-break: break-word;
      transition: all 0.2s ease;
    }

    .msg-bot {
      align-self: flex-start;
      background: #ffffff;
      color: var(--text-dark);
      border-bottom-left-radius: 4px;
      border: 1px solid var(--border-color);
      box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }

    .msg-bot p {
      margin: 0 0 8px 0;
    }
    .msg-bot p:last-child {
      margin-bottom: 0;
    }

    .msg-bot strong {
      color: #0f172a;
      font-weight: 600;
    }

    .msg-bot ul, .msg-bot ol {
      margin: 6px 0 10px 0;
      padding-left: 20px;
    }

    .msg-bot li {
      margin-bottom: 4px;
      line-height: 1.5;
    }

    .msg-bot ul li {
      list-style-type: disc;
    }

    .msg-bot ol li {
      list-style-type: decimal;
    }

    .msg-bot h4, .msg-bot h3 {
      font-size: 14px;
      font-weight: 700;
      margin: 10px 0 4px 0;
      color: #0f172a;
    }

    .msg-bot .chip {
      display: inline-block;
      background: #eff6ff;
      color: #1d4ed8;
      font-size: 12px;
      font-weight: 600;
      padding: 1px 7px;
      border-radius: 6px;
      border: 1px solid #bfdbfe;
      margin: 0 2px;
    }

    .msg-bot .status-tag {
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .msg-bot .status-processing {
      background: #fef3c7;
      color: #92400e;
      border: 1px solid #fde68a;
    }
    .msg-bot .status-delivered {
      background: #dcfce7;
      color: #166534;
      border: 1px solid #bbf7d0;
    }
    .msg-bot .status-shipped {
      background: #e0e7ff;
      color: #3730a3;
      border: 1px solid #c7d2fe;
    }

    .msg-user {
      align-self: flex-end;
      background: var(--primary);
      color: #ffffff;
      border-bottom-right-radius: 4px;
      white-space: pre-wrap;
    }

    .msg-time {
      font-size: 10px;
      color: var(--text-muted);
      margin-top: 4px;
      display: block;
      text-align: right;
    }

    .typing-indicator {
      display: none;
      align-self: flex-start;
      background: #ffffff;
      padding: 12px 18px;
      border-radius: 16px;
      border-bottom-left-radius: 4px;
      border: 1px solid var(--border-color);
    }

    .typing-indicator.active { display: flex; gap: 4px; align-items: center; }

    .typing-dot {
      width: 6px;
      height: 6px;
      background: #94a3b8;
      border-radius: 50%;
      animation: pulse 1.4s infinite ease-in-out both;
    }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }

    @keyframes pulse {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }

    .input-bar {
      padding: 14px 16px;
      background: #ffffff;
      border-top: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .chat-input {
      flex: 1;
      padding: 10px 14px;
      font-size: 14px;
      border: 1px solid var(--border-color);
      border-radius: 12px;
      outline: none;
      transition: border 0.2s;
    }

    .chat-input:focus {
      border-color: var(--primary);
    }

    .send-btn {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: var(--primary);
      color: #ffffff;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: opacity 0.2s;
    }

    .send-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .branding-footer {
      text-align: center;
      font-size: 10px;
      color: var(--text-muted);
      padding: 6px;
      background: #f8fafc;
      border-top: 1px solid #f1f5f9;
    }
  `;

  // 5. Render HTML inside shadow DOM
  shadow.innerHTML = `
    <style>${styles}</style>
    
    <button class="launcher-btn" id="launcherBtn" aria-label="Open chat">
      <svg id="iconOpen" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>
      <svg id="iconClose" viewBox="0 0 24 24" style="display:none;"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
    </button>

    <div class="chat-panel" id="chatPanel">
      <div class="header">
        <div class="header-info">
          <div class="header-avatar" id="avatarText">AI</div>
          <div class="header-title-box">
            <h3 id="panelTitle">${config.widget_title}</h3>
            <div class="header-status">
              <span class="status-dot"></span> Online • Powered by AI
            </div>
          </div>
        </div>
        <button class="close-btn" id="closeBtn" aria-label="Close chat">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>

      <div class="messages-container" id="messagesContainer">
        <!-- Messages rendered dynamically -->
        <div class="typing-indicator" id="typingIndicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>

      <form class="input-bar" id="chatForm">
        <input type="text" class="chat-input" id="chatInput" placeholder="Ask a question..." autocomplete="off" />
        <button type="submit" class="send-btn" id="sendBtn" aria-label="Send">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </form>

      <div class="branding-footer" id="brandingFooter">
        AI Customer Assistant
      </div>
    </div>
  `;

  // 6. DOM Elements
  const launcherBtn = shadow.getElementById("launcherBtn");
  const iconOpen = shadow.getElementById("iconOpen");
  const iconClose = shadow.getElementById("iconClose");
  const chatPanel = shadow.getElementById("chatPanel");
  const closeBtn = shadow.getElementById("closeBtn");
  const panelTitle = shadow.getElementById("panelTitle");
  const avatarText = shadow.getElementById("avatarText");
  const messagesContainer = shadow.getElementById("messagesContainer");
  const typingIndicator = shadow.getElementById("typingIndicator");
  const chatForm = shadow.getElementById("chatForm");
  const chatInput = shadow.getElementById("chatInput");
  const sendBtn = shadow.getElementById("sendBtn");

  let isOpen = false;
  let isSending = false;

  function updateWidgetBranding() {
    panelTitle.textContent = config.widget_title || config.name || "AI Support";
    avatarText.textContent = (config.name || "AI").substring(0, 2).toUpperCase();
    host.style.setProperty("--primary", config.primary_color || "#2563eb");
  }

  function toggleChat() {
    isOpen = !isOpen;
    if (isOpen) {
      chatPanel.classList.add("open");
      iconOpen.style.display = "none";
      iconClose.style.display = "block";
      setTimeout(() => chatInput.focus(), 150);
    } else {
      chatPanel.classList.remove("open");
      iconOpen.style.display = "block";
      iconClose.style.display = "none";
    }
  }

  launcherBtn.addEventListener("click", toggleChat);
  closeBtn.addEventListener("click", toggleChat);

  // 7. Messages Management
  function loadHistory() {
    try {
      const raw = localStorage.getItem(storageKeyHistory);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function saveHistory(messages) {
    try {
      localStorage.setItem(storageKeyHistory, JSON.stringify(messages));
    } catch {}
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatInline(str) {
    let s = str;
    // Status tags for bolded statuses
    s = s.replace(/\*\*(Processing|Pending)\*\*/gi, '<span class="status-tag status-processing">$1</span>');
    s = s.replace(/\*\*(Delivered|Completed)\*\*/gi, '<span class="status-tag status-delivered">$1</span>');
    s = s.replace(/\*\*(Shipped|Dispatched)\*\*/gi, '<span class="status-tag status-shipped">$1</span>');
    // Order ID chips (#12345 or **12345** or order 12345)
    s = s.replace(/\*\*(\d{5})\*\*/g, '#$1');
    s = s.replace(/(#\d{5}\b)/g, '<span class="chip">$1</span>');
    s = s.replace(/\b(order\s+)(\d{5})\b/gi, '$1<span class="chip">#$2</span>');
    // Bold: **text**
    s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    // Italic: *text*
    s = s.replace(/\*([^*]+?)\*/g, "<em>$1</em>");
    // Inline code: `code`
    s = s.replace(/`([^`]+?)`/g, "<code>$1</code>");
    return s;
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let raw = text.trim();

    // Normalization to ensure lists and sections have line breaks even if squashed
    raw = raw.replace(/([.!?:])\s*(\*\*[A-Z][A-Za-z0-9\s\-/]+?:\*\*)/g, "$1\n\n$2\n");
    raw = raw.replace(/([^\n])\s+[-•*]\s+/g, "$1\n- ");
    raw = raw.replace(/([^\n])\s+(\d+[.)]\s+)/g, "$1\n$2");
    raw = raw.replace(/(\))\s+([A-Z][a-z]+)/g, "$1\n\n$2");

    const lines = raw.split(/\r?\n/);
    let html = "";
    let inList = false;
    let listType = ""; // "ul" or "ol"

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) {
        if (inList) {
          html += `</${listType}>`;
          inList = false;
        }
        continue;
      }

      const bulletMatch = line.match(/^[-*•]\s+(.*)$/);
      const numberMatch = line.match(/^\d+[.)]\s+(.*)$/);
      const headingMatch = line.match(/^(#{1,4})\s+(.*)$/);

      if (bulletMatch) {
        if (!inList || listType !== "ul") {
          if (inList) html += `</${listType}>`;
          html += "<ul>";
          inList = true;
          listType = "ul";
        }
        html += `<li>${formatInline(escapeHtml(bulletMatch[1]))}</li>`;
      } else if (numberMatch) {
        if (!inList || listType !== "ol") {
          if (inList) html += `</${listType}>`;
          html += "<ol>";
          inList = true;
          listType = "ol";
        }
        html += `<li>${formatInline(escapeHtml(numberMatch[1]))}</li>`;
      } else if (headingMatch) {
        if (inList) {
          html += `</${listType}>`;
          inList = false;
        }
        html += `<h4>${formatInline(escapeHtml(headingMatch[2]))}</h4>`;
      } else {
        if (inList) {
          html += `</${listType}>`;
          inList = false;
        }
        html += `<p>${formatInline(escapeHtml(line))}</p>`;
      }
    }

    if (inList) {
      html += `</${listType}>`;
    }

    return html;
  }

  function appendMessageToDOM(role, text) {
    const el = document.createElement("div");
    el.className = `msg msg-${role}`;
    if (role === "bot") {
      el.innerHTML = formatMarkdown(text);
    } else {
      el.textContent = text;
    }
    messagesContainer.insertBefore(el, typingIndicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Initial greeting
  const history = loadHistory();
  if (history.length === 0) {
    appendMessageToDOM("bot", config.widget_greeting);
    saveHistory([{ role: "bot", text: config.widget_greeting }]);
  } else {
    history.forEach((m) => appendMessageToDOM(m.role, m.text));
  }

  // 8. Send message to backend
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text || isSending) return;

    // Append user message
    chatInput.value = "";
    appendMessageToDOM("user", text);
    const updated = loadHistory();
    updated.push({ role: "user", text });
    saveHistory(updated);

    // Show typing indicator
    isSending = true;
    sendBtn.disabled = true;
    typingIndicator.classList.add("active");
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
      const res = await fetch(`${apiUrl}/widget/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: threadId,
          message: text,
          project_id: projectId,
          api_key: apiKey || undefined,
          customer_email: customerEmail || undefined,
          customer_name: customerName || undefined,
        }),
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();
      appendMessageToDOM("bot", data.response);
      updated.push({ role: "bot", text: data.response });
      saveHistory(updated);
    } catch (err) {
      const errorMsg = "Sorry, I am having trouble connecting right now. Please try again in a moment.";
      appendMessageToDOM("bot", errorMsg);
    } finally {
      isSending = false;
      sendBtn.disabled = false;
      typingIndicator.classList.remove("active");
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  });

  // Fetch live branding on startup
  fetchConfig();
})();
