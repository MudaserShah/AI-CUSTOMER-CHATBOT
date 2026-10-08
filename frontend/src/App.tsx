import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import {
  ApiError,
  type Product,
  type Order,
  type CheckoutResponse,
  checkout,
  createRefund,
  getOrders,
  getProducts,
  requestToken,
  sendChatMessage,
} from "./api";

type View = "shop" | "checkout" | "orders";
type ChatMessage = { role: "user" | "assistant"; content: string };
type Session = {
  accessToken: string;
  customerId: string;
  name: string;
  email: string;
};

const SESSION_KEY = "technest-session";
const THREAD_KEY = "technest-chat-thread";

function money(value: string | number, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function dateLabel(value: string | null) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function newThreadId() {
  return `web-${crypto.randomUUID()}`;
}

function App() {
  const [view, setView] = useState<View>("shop");
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(true);
  const [productsError, setProductsError] = useState("");
  const [cart, setCart] = useState<Record<string, number>>({});
  const [cartOpen, setCartOpen] = useState(false);
  const [session, setSession] = useState<Session | null>(() => {
    const stored = localStorage.getItem(SESSION_KEY);
    if (!stored) return null;
    try {
      return JSON.parse(stored) as Session;
    } catch {
      localStorage.removeItem(SESSION_KEY);
      return null;
    }
  });
  const [orders, setOrders] = useState<Order[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [ordersError, setOrdersError] = useState("");
  const [checkoutError, setCheckoutError] = useState("");
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutResult, setCheckoutResult] = useState<CheckoutResponse | null>(null);
  const [signInOpen, setSignInOpen] = useState(false);
  const [signInCustomerId, setSignInCustomerId] = useState("");
  const [signInEmail, setSignInEmail] = useState("");
  const [signInError, setSignInError] = useState("");
  const [signInLoading, setSignInLoading] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");

  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatSending, setChatSending] = useState(false);
  const [threadId, setThreadId] = useState(() => {
    return localStorage.getItem(THREAD_KEY) || newThreadId();
  });
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [refundOrderId, setRefundOrderId] = useState<string | null>(null);
  const [refundReason, setRefundReason] = useState("");
  const [refundSending, setRefundSending] = useState(false);
  const [refundError, setRefundError] = useState("");

  useEffect(() => {
    localStorage.setItem(THREAD_KEY, threadId);
  }, [threadId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setProductsLoading(true);
        const data = await getProducts();
        if (!cancelled) setProducts(data);
      } catch (error) {
        if (!cancelled) {
          setProductsError(
            error instanceof Error
              ? error.message
              : "Could not load the product catalog.",
          );
        }
      } finally {
        if (!cancelled) setProductsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!session) return;
    setCustomerName(session.name);
    setCustomerEmail(session.email);
    loadOrders(session.accessToken);
  }, [session]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, chatSending]);

  const cartItems = useMemo(
    () =>
      products
        .filter((product) => cart[product.id])
        .map((product) => ({ product, quantity: cart[product.id] })),
    [products, cart],
  );

  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);
  const cartTotal = cartItems.reduce(
    (sum, item) => sum + Number(item.product.unit_price) * item.quantity,
    0,
  );

  async function loadOrders(token: string) {
    setOrdersLoading(true);
    setOrdersError("");
    try {
      const data = await getOrders(token);
      setOrders(data);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout();
        return;
      }
      setOrdersError(
        error instanceof Error ? error.message : "Could not load your orders.",
      );
    } finally {
      setOrdersLoading(false);
    }
  }

  function addToCart(productId: string) {
    setCart((current) => ({
      ...current,
      [productId]: (current[productId] || 0) + 1,
    }));
    setCartOpen(true);
  }

  function updateQuantity(productId: string, delta: number) {
    setCart((current) => {
      const next = Math.max((current[productId] || 0) + delta, 0);
      if (!next) {
        const copy = { ...current };
        delete copy[productId];
        return copy;
      }
      return { ...current, [productId]: next };
    });
  }

  function startCheckout() {
    if (!cartItems.length) return;
    setCartOpen(false);
    setCheckoutError("");
    setView("checkout");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleCheckout(event: React.FormEvent) {
    event.preventDefault();
    if (checkoutLoading || !cartItems.length) return;

    setCheckoutError("");
    setCheckoutLoading(true);
    try {
      const result = await checkout(
        {
          name: customerName.trim(),
          email: customerEmail.trim(),
          delivery_address: deliveryAddress.trim(),
          payment_method: "cod",
          items: cartItems.map(({ product, quantity }) => ({
            product_id: product.id,
            quantity,
          })),
        },
        session?.accessToken,
      );

      const nextSession = {
        accessToken: result.access_token,
        customerId: result.customer_id,
        name: result.name,
        email: result.email,
      };
      localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
      setSession(nextSession);
      setCheckoutResult(result);
      setCart({});
      setView("orders");
      await loadOrders(result.access_token);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setSignInCustomerId("");
        setSignInEmail(customerEmail.trim());
        setSignInError("This email already has an account. Sign in with your Customer ID to place the order.");
        setSignInOpen(true);
      }
      setCheckoutError(
        error instanceof Error
          ? error.message
          : "Could not complete checkout.",
      );
    } finally {
      setCheckoutLoading(false);
    }
  }

  async function handleSignIn(event: React.FormEvent) {
    event.preventDefault();
    if (signInLoading) return;

    setSignInError("");
    setSignInLoading(true);
    try {
      const result = await requestToken(signInCustomerId.trim(), signInEmail.trim());
      const nextSession: Session = {
        accessToken: result.access_token,
        customerId: signInCustomerId.trim(),
        name: customerName.trim() || "Customer",
        email: signInEmail.trim(),
      };
      localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
      setSession(nextSession);
      setSignInOpen(false);
      setSignInCustomerId("");
      setSignInEmail("");
      setCheckoutError("");
    } catch (error) {
      setSignInError(
        error instanceof Error ? error.message : "Could not sign you in.",
      );
    } finally {
      setSignInLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem(SESSION_KEY);
    setSession(null);
    setOrders([]);
    setCheckoutResult(null);
    setChatMessages([]);
    setChatOpen(false);
    setThreadId(newThreadId());
    setView("shop");
  }

  async function submitRefund(order: Order) {
    if (!session || refundSending || !refundReason.trim()) return;

    setRefundSending(true);
    setRefundError("");
    try {
      await createRefund(session.accessToken, order.order_id, refundReason.trim());
      setRefundOrderId(null);
      setRefundReason("");
      await loadOrders(session.accessToken);
      setChatOpen(true);
      setChatMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: `Refund request for order ${order.order_id} has been submitted. You can also ask me for its status anytime.`,
        },
      ]);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout();
        return;
      }
      setRefundError(
        error instanceof Error ? error.message : "Could not submit the refund request.",
      );
    } finally {
      setRefundSending(false);
    }
  }

  async function sendMessage(text = chatMessage) {
    const clean = text.trim();
    if (!session || !clean || chatSending) return;

    setChatMessages((current) => [...current, { role: "user", content: clean }]);
    setChatMessage("");
    setChatSending(true);

    try {
      const data = await sendChatMessage(session.accessToken, threadId, clean);
      setChatMessages((current) => [
        ...current,
        { role: "assistant", content: data.response },
      ]);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout();
        return;
      }
      setChatMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            error instanceof Error
              ? error.message
              : "The assistant is temporarily unavailable.",
        },
      ]);
    } finally {
      setChatSending(false);
    }
  }

  function handleChatKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMessage();
    }
  }

  function askAboutOrder(orderId: string) {
    if (!session) {
      openChat();
      return;
    }
    setChatOpen(true);
    void sendMessage(`Where is my order ${orderId}?`);
  }

  function openChat() {
    if (!session) {
      setView("checkout");
      setCheckoutError("Place an order first so the assistant can securely access your customer account.");
      return;
    }
    setChatOpen(true);
  }

  return (
    <div className="storefront">
      <header className="site-header">
        <button className="brand" type="button" onClick={() => setView("shop")}>
          <span className="brand-icon">TN</span>
          <span>
            <strong>TechNest</strong>
            <small>Electronics</small>
          </span>
        </button>

        <nav className="nav-links" aria-label="Primary">
          <button type="button" className={view === "shop" ? "active" : ""} onClick={() => setView("shop")}>
            Shop
          </button>
          <button
            type="button"
            className={view === "orders" ? "active" : ""}
            onClick={() => {
              setView("orders");
              if (session) loadOrders(session.accessToken);
            }}
          >
            My orders
          </button>
        </nav>

        <div className="header-actions">
          {session && <span className="customer-chip">ID {session.customerId}</span>}
          <button type="button" className="cart-button" onClick={() => setCartOpen(true)}>
            Cart <span>{cartCount}</span>
          </button>
          {session ? (
            <button className="signout" type="button" onClick={logout}>
              Sign out
            </button>
          ) : (
            <button className="signout" type="button" onClick={() => { setSignInError(""); setSignInOpen(true); }}>
              Sign in
            </button>
          )}
        </div>
      </header>

      {view === "shop" && (
        <main>
          <section className="hero">
            <div className="hero-copy">
              <span className="eyebrow">SMART SHOPPING · SMART SUPPORT</span>
              <h1>Buy your next device.<br /><em>Support comes with it.</em></h1>
              <p>
                A working ecommerce experience where every checkout creates a secure customer identity,
                a unique order number, and a support AI that knows only your orders.
              </p>
              <div className="hero-actions">
                <button className="primary-button" type="button" onClick={() => document.getElementById("catalog")?.scrollIntoView({ behavior: "smooth" })}>
                  Explore products
                </button>
                <button className="ghost-button" type="button" onClick={openChat}>
                  Ask AI support
                </button>
              </div>
            </div>
            <div className="hero-card">
              <div className="hero-orb">AI</div>
              <div>
                <span className="hero-card-label">YOUR SUPPORT LAYER</span>
                <h3>Order status · Refunds · Delivery help</h3>
                <p>Authenticated to your account after checkout.</p>
              </div>
            </div>
          </section>

          <section className="catalog section-shell" id="catalog">
            <div className="section-heading">
              <div>
                <span className="eyebrow">CURATED CATALOG</span>
                <h2>Built for everyday tech.</h2>
              </div>
              <p>Prices are calculated by the backend at checkout, so the browser never controls the order total.</p>
            </div>

            {productsError && <div className="notice error">{productsError}</div>}
            {productsLoading ? (
              <div className="loading-grid">
                {[1, 2, 3, 4].map((item) => <div className="skeleton-card" key={item} />)}
              </div>
            ) : (
              <div className="product-grid">
                {products.map((product) => (
                  <article className="product-card" key={product.id}>
                    <div className="product-visual">
                      <span>{product.image_emoji}</span>
                      <small>{product.category}</small>
                    </div>
                    <div className="product-body">
                      <div className="product-title-row">
                        <h3>{product.name}</h3>
                        <strong>{money(product.unit_price, product.currency)}</strong>
                      </div>
                      <p>{product.description}</p>
                      <button className="add-button" type="button" onClick={() => addToCart(product.id)}>
                        Add to cart
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="trust-strip">
            <div><strong>Unique identity</strong><span>Created at checkout</span></div>
            <div><strong>5-digit order ID</strong><span>Generated server-side</span></div>
            <div><strong>AI support</strong><span>Customer-scoped access</span></div>
            <div><strong>Refund workflow</strong><span>Eligibility + status tracking</span></div>
          </section>
        </main>
      )}

      {view === "checkout" && (
        <main className="section-shell checkout-page">
          <button type="button" className="back-link" onClick={() => setView("shop")}>← Continue shopping</button>
          <div className="checkout-layout">
            <form className="checkout-form" onSubmit={handleCheckout}>
              <div className="section-heading compact">
                <div>
                  <span className="eyebrow">SECURE CHECKOUT</span>
                  <h2>Your order creates your support identity.</h2>
                </div>
              </div>
              <label>
                Full name
                <input required minLength={2} value={customerName} onChange={(event) => setCustomerName(event.target.value)} placeholder="Ali Khan" />
              </label>
              <label>
                Email
                <input required type="email" value={customerEmail} onChange={(event) => setCustomerEmail(event.target.value)} placeholder="ali@example.com" />
                <small>We use this email to recognize returning customers.</small>
              </label>
              <label>
                Delivery address
                <textarea required minLength={5} value={deliveryAddress} onChange={(event) => setDeliveryAddress(event.target.value)} placeholder="House 10, Street 2, Wah Cantt" rows={4} />
              </label>
              {checkoutError && <div className="notice error">{checkoutError}</div>}
              <button className="primary-button full" disabled={checkoutLoading} type="submit">
                {checkoutLoading ? "Creating your order…" : `Place order · ${money(cartTotal)}`}
              </button>
              <p className="form-footnote">Demo checkout uses Cash on Delivery. The payment provider can be plugged into this same order flow later.</p>
            </form>

            <aside className="checkout-summary">
              <span className="eyebrow">ORDER SUMMARY</span>
              {cartItems.map(({ product, quantity }) => (
                <div className="summary-item" key={product.id}>
                  <span className="summary-emoji">{product.image_emoji}</span>
                  <div>
                    <strong>{product.name}</strong>
                    <small>Qty {quantity}</small>
                  </div>
                  <strong>{money(Number(product.unit_price) * quantity)}</strong>
                </div>
              ))}
              <div className="summary-total"><span>Total</span><strong>{money(cartTotal)}</strong></div>
            </aside>
          </div>
        </main>
      )}

      {view === "orders" && (
        <main className="section-shell orders-page">
          <div className="orders-head">
            <div>
              <span className="eyebrow">CUSTOMER CENTER</span>
              <h2>{session ? `${session.name}'s orders` : "Your orders"}</h2>
              {session && <p className="muted">Customer ID <code>{session.customerId}</code></p>}
            </div>
            <button type="button" className="primary-button" onClick={() => setView("shop")}>Shop more</button>
          </div>

          {checkoutResult && (
            <div className="success-banner">
              <div>
                <span className="eyebrow">ORDER CREATED</span>
                <h3>You're all set. Your support identity is ready.</h3>
              </div>
              <div className="success-ids">
                <span><small>Customer ID</small><strong>{checkoutResult.customer_id}</strong></span>
                <span><small>Order ID</small><strong>{checkoutResult.order_id}</strong></span>
              </div>
            </div>
          )}

          {!session ? (
            <div className="empty-state">
              <div className="empty-icon">◎</div>
              <h3>No customer session yet.</h3>
              <p>Place an order and the backend will generate the customer ID and order number automatically.</p>
              <button className="primary-button" type="button" onClick={() => setView("shop")}>Start shopping</button>
            </div>
          ) : ordersLoading ? (
            <div className="empty-state"><div className="loading-spinner" /><p>Loading your orders…</p></div>
          ) : ordersError ? (
            <div className="notice error">{ordersError}</div>
          ) : !orders.length ? (
            <div className="empty-state">
              <div className="empty-icon">◇</div>
              <h3>No orders yet.</h3>
              <p>Your next checkout will appear here and will automatically be linked to your customer account.</p>
              <button className="primary-button" type="button" onClick={() => setView("shop")}>Browse products</button>
            </div>
          ) : (
            <div className="orders-list">
              {orders.map((order) => (
                <article className="order-card" key={order.order_id}>
                  <div className="order-card-head">
                    <div>
                      <span className="eyebrow">ORDER</span>
                      <h3>#{order.order_id}</h3>
                      <span className={`status-pill ${order.status.toLowerCase()}`}>{order.status}</span>
                    </div>
                    <div className="order-meta">
                      <span>Placed {dateLabel(order.created_at)}</span>
                      <strong>{money(order.total_amount, order.currency)}</strong>
                    </div>
                  </div>

                  <div className="order-items">
                    {order.items.length ? order.items.map((item) => (
                      <div className="order-item" key={`${order.order_id}-${item.product_id}`}>
                        <span>{item.name}</span>
                        <span>× {item.quantity}</span>
                        <strong>{money(item.line_total, order.currency)}</strong>
                      </div>
                    )) : <p className="muted">Legacy order without item details.</p>}
                  </div>

                  <div className="order-details-grid">
                    <div><small>Delivery address</small><span>{order.delivery_address || "Not available"}</span></div>
                    <div><small>Delivery estimate</small><span>{dateLabel(order.receiving_date || order.shipping_date || order.dispatch_date)}</span></div>
                    <div><small>Payment</small><span>Cash on Delivery</span></div>
                  </div>

                  <div className="order-actions">
                    <button className="secondary-button" type="button" onClick={() => askAboutOrder(order.order_id)}>
                      Ask AI about this order
                    </button>
                    {order.refund_status ? (
                      <span className="refund-state">Refund: <strong>{order.refund_status}</strong>{order.refund_request_id ? ` · ${order.refund_request_id.slice(0, 8)}` : ""}</span>
                    ) : order.refund_eligible ? (
                      <button className="refund-button" type="button" onClick={() => { setRefundOrderId(order.order_id); setRefundError(""); }}>
                        Request refund
                      </button>
                    ) : (
                      <span className="muted small">Refund: {order.refund_reason || "Not available yet."}</span>
                    )}
                  </div>

                  {refundOrderId === order.order_id && (
                    <div className="refund-box">
                      <div>
                        <span className="eyebrow">REFUND REQUEST · #{order.order_id}</span>
                        <h4>Why are you returning this order?</h4>
                      </div>
                      <textarea rows={3} value={refundReason} onChange={(event) => setRefundReason(event.target.value)} placeholder="The product arrived damaged…" />
                      {refundError && <div className="notice error">{refundError}</div>}
                      <div className="refund-actions">
                        <button type="button" className="ghost-button" onClick={() => setRefundOrderId(null)}>Cancel</button>
                        <button type="button" className="primary-button" disabled={refundSending || refundReason.trim().length < 3} onClick={() => submitRefund(order)}>
                          {refundSending ? "Submitting…" : "Submit refund request"}
                        </button>
                      </div>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </main>
      )}

      <button className="chat-launcher" type="button" onClick={openChat} aria-label="Open AI support">
        <span>AI</span>
        <strong>Support</strong>
      </button>

      {chatOpen && (
        <div className="chat-panel">
          <div className="chat-head">
            <div>
              <span className="eyebrow">TECHNEST AI</span>
              <h3>Customer support</h3>
              {session && <small>Secure session · {session.customerId}</small>}
            </div>
            <button type="button" className="icon-button" onClick={() => setChatOpen(false)} aria-label="Close assistant">×</button>
          </div>

          <div className="chat-body">
            {!chatMessages.length && (
              <div className="chat-welcome">
                <div className="chat-avatar">AI</div>
                <h4>What can I help with?</h4>
                <p>I can use your authenticated customer context to look up orders and manage refund requests.</p>
                <div className="chat-prompts">
                  <button type="button" onClick={() => sendMessage("Show me my latest order.")}>Show my latest order</button>
                  <button type="button" onClick={() => sendMessage("Do I have a refund request?")}>Check my refund</button>
                  <button type="button" onClick={() => sendMessage("What is your refund policy?")}>Refund policy</button>
                </div>
              </div>
            )}
            {chatMessages.map((message, index) => (
              <div className={`chat-message ${message.role}`} key={`${message.role}-${index}`}>
                <div>{message.content}</div>
              </div>
            ))}
            {chatSending && <div className="chat-message assistant"><div className="typing-dots"><span /><span /><span /></div></div>}
            <div ref={chatEndRef} />
          </div>

          <div className="chat-input-row">
            <input value={chatMessage} onChange={(event) => setChatMessage(event.target.value)} onKeyDown={handleChatKeyDown} placeholder="Ask about your order…" disabled={chatSending || !session} />
            <button type="button" onClick={() => sendMessage()} disabled={!chatMessage.trim() || chatSending || !session}>→</button>
          </div>
        </div>
      )}

      {signInOpen && (
        <div className="overlay" onClick={() => setSignInOpen(false)}>
          <div className="auth-modal" onClick={(event) => event.stopPropagation()}>
            <div className="drawer-head">
              <div>
                <span className="eyebrow">RETURNING CUSTOMER</span>
                <h3>Sign in to your customer account</h3>
              </div>
              <button className="icon-button" type="button" onClick={() => setSignInOpen(false)}>×</button>
            </div>
            <form className="checkout-form auth-form" onSubmit={handleSignIn}>
              <label>
                Customer ID
                <input required value={signInCustomerId} onChange={(event) => setSignInCustomerId(event.target.value)} placeholder="customer-a1b2c3d4e5f6" />
              </label>
              <label>
                Email
                <input required type="email" value={signInEmail} onChange={(event) => setSignInEmail(event.target.value)} placeholder="you@example.com" />
              </label>
              {signInError && <div className="notice error">{signInError}</div>}
              <button className="primary-button full" disabled={signInLoading} type="submit">
                {signInLoading ? "Signing in…" : "Continue"}
              </button>
              <p className="form-footnote">For this demo, the Customer ID is the stable customer identity generated during your first checkout.</p>
            </form>
          </div>
        </div>
      )}

      {cartOpen && (
        <>
          <div className="overlay" onClick={() => setCartOpen(false)} />
          <aside className="cart-drawer">
            <div className="drawer-head"><div><span className="eyebrow">YOUR CART</span><h3>{cartCount} item{cartCount === 1 ? "" : "s"}</h3></div><button className="icon-button" type="button" onClick={() => setCartOpen(false)}>×</button></div>
            {!cartItems.length ? (
              <div className="drawer-empty"><div>◇</div><p>Your cart is empty.</p><button className="primary-button" type="button" onClick={() => { setCartOpen(false); setView("shop"); }}>Browse products</button></div>
            ) : (
              <>
                <div className="drawer-items">
                  {cartItems.map(({ product, quantity }) => (
                    <div className="drawer-item" key={product.id}>
                      <span className="drawer-emoji">{product.image_emoji}</span>
                      <div className="drawer-item-main"><strong>{product.name}</strong><small>{money(product.unit_price)}</small><div className="qty-controls"><button type="button" onClick={() => updateQuantity(product.id, -1)}>−</button><span>{quantity}</span><button type="button" onClick={() => updateQuantity(product.id, 1)}>+</button></div></div>
                      <strong>{money(Number(product.unit_price) * quantity)}</strong>
                    </div>
                  ))}
                </div>
                <div className="drawer-total"><span>Total</span><strong>{money(cartTotal)}</strong></div>
                <button className="primary-button full" type="button" onClick={startCheckout}>Checkout</button>
              </>
            )}
          </aside>
        </>
      )}
    </div>
  );
}

export default App;
