import { useState } from 'react';
import { ArrowRight, ArrowUpRight, Check, Package, MessageSquare, Loader2 } from 'lucide-react';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { money, type BagItem } from '@/lib/catalog';

export type CheckoutDetails = {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  postal: string;
  country: string;
  notes: string;
};

const emptyDetails: CheckoutDetails = {
  firstName: '', lastName: '', email: '', phone: '', address: '', city: '', postal: '', country: 'Pakistan', notes: '',
};

const fields: { key: keyof CheckoutDetails; label: string; type?: string; span?: boolean; placeholder?: string }[] = [
  { key: 'firstName', label: 'First name' },
  { key: 'lastName', label: 'Last name' },
  { key: 'email', label: 'Email', type: 'email', span: true, placeholder: 'you@example.com' },
  { key: 'phone', label: 'Phone', type: 'tel', placeholder: '+92 300 0000000' },
  { key: 'address', label: 'Street address', span: true, placeholder: 'House, street, area' },
  { key: 'city', label: 'City' },
  { key: 'postal', label: 'Postal code' },
  { key: 'country', label: 'Country', span: true },
  { key: 'notes', label: 'Delivery notes (optional)', span: true, placeholder: 'Any instructions for the courier' },
];

export function CheckoutDialog({ open, onOpenChange, bag, subtotal }: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  bag: BagItem[];
  subtotal: number;
}) {
  const [details, setDetails] = useState<CheckoutDetails>(() => {
    const savedEmail = typeof window !== 'undefined' ? localStorage.getItem('monochrome_customer_email') || '' : '';
    const savedName = typeof window !== 'undefined' ? localStorage.getItem('monochrome_customer_name') || '' : '';
    const parts = savedName.split(' ');
    return {
      ...emptyDetails,
      email: savedEmail,
      firstName: parts[0] || '',
      lastName: parts.slice(1).join(' ') || '',
    };
  });
  const [errors, setErrors] = useState<Partial<Record<keyof CheckoutDetails, string>>>({});
  const [placed, setPlaced] = useState(false);
  const [orderNo, setOrderNo] = useState('');
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState('');
  const count = bag.reduce((total, item) => total + item.quantity, 0);
  const shipping = subtotal > 0 ? 8 : 0;

  function set(key: keyof CheckoutDetails, value: string) {
    setDetails(d => ({ ...d, [key]: value }));
    setErrors(e => ({ ...e, [key]: undefined }));
  }

  async function placeOrder() {
    const next: typeof errors = {};
    if (!details.firstName.trim()) next.firstName = 'Required';
    if (!details.lastName.trim()) next.lastName = 'Required';
    if (!/^\S+@\S+\.\S+$/.test(details.email.trim())) next.email = 'Enter a valid email';
    if (!details.phone.trim()) next.phone = 'Required';
    if (!details.address.trim()) next.address = 'Required';
    if (!details.city.trim()) next.city = 'Required';
    if (!details.postal.trim()) next.postal = 'Required';
    if (!details.country.trim()) next.country = 'Required';
    setErrors(next);
    if (Object.keys(next).length) return;

    setLoading(true);
    setServerError('');

    const apiUrl = 'http://localhost:8000';
    const fullName = `${details.firstName} ${details.lastName}`.trim();
    const cleanEmail = details.email.trim().toLowerCase();
    const fullAddress = `${details.address}, ${details.city} ${details.postal}, ${details.country}${details.phone ? ` (Phone: ${details.phone})` : ''}`;

    const payload = {
      name: fullName,
      email: cleanEmail,
      delivery_address: fullAddress,
      items: bag.map(item => ({ product_id: item.product.id, quantity: item.quantity })),
      payment_method: 'cod',
    };

    try {
      let token = localStorage.getItem('monochrome_auth_token');
      let res = await fetch(`${apiUrl}/store/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      // If returning customer without active token, mint a token and retry
      if (res.status === 409) {
        const tokenRes = await fetch(`${apiUrl}/auth/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: cleanEmail }),
        });
        if (tokenRes.ok) {
          const tokenData = await tokenRes.json();
          token = tokenData.access_token;
          if (token) {
            localStorage.setItem('monochrome_auth_token', token);
            res = await fetch(`${apiUrl}/store/checkout`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
              },
              body: JSON.stringify(payload),
            });
          }
        }
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to place order. Please check backend connection.');
      }

      const result = await res.json();
      const generatedOrderId = String(result.order_id);

      if (result.access_token) {
        localStorage.setItem('monochrome_auth_token', result.access_token);
      }
      localStorage.setItem('monochrome_customer_email', cleanEmail);
      localStorage.setItem('monochrome_customer_name', fullName);

      // Register identity with AI Chatbot widget
      if (typeof window !== 'undefined' && (window as any).AIWidget) {
        (window as any).AIWidget.identify({
          email: cleanEmail,
          name: fullName,
        });
      }

      setOrderNo(generatedOrderId);
      setPlaced(true);
      window.dispatchEvent(new CustomEvent('urbanvibe:order-placed'));
    } catch (err: any) {
      console.error('Checkout error:', err);
      setServerError(err.message || 'Something went wrong while creating your order.');
    } finally {
      setLoading(false);
    }
  }

  function close() {
    onOpenChange(false);
    if (placed) {
      setPlaced(false);
      setOrderNo('');
    }
  }

  return (
    <Dialog open={open} onOpenChange={o => (o ? onOpenChange(true) : close())}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        {placed ? (
          <div className="py-4 text-center">
            <span className="mx-auto mb-5 flex size-14 items-center justify-center rounded-full border border-border bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <Check className="size-6" />
            </span>
            <p className="eyebrow text-muted-foreground mb-2">Order #{orderNo}</p>
            <DialogTitle className="font-display text-4xl uppercase">Order confirmed</DialogTitle>
            <DialogDescription className="mx-auto mt-4 max-w-md leading-6">
              Thank you, {details.firstName}! Your order <strong className="text-foreground">#{orderNo}</strong> has been registered in the system. You can track this order with our AI assistant below.
            </DialogDescription>
            <div className="mx-auto mt-7 max-w-md border border-border p-5 text-left text-xs leading-6 bg-muted/20">
              <p className="font-semibold uppercase tracking-[1px] mb-2">Delivering to</p>
              <p>{details.firstName} {details.lastName}</p>
              <p className="text-muted-foreground">{details.address}, {details.city} {details.postal}, {details.country}</p>
              <p className="text-muted-foreground">{details.phone}</p>
              <div className="mt-3 border-t border-border pt-3 flex justify-between font-semibold"><span>{count} item{count === 1 ? '' : 's'} · total</span><span>{money(subtotal + shipping)}</span></div>
            </div>
            <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
              <Button
                className="rounded-none bg-primary text-primary-foreground gap-2 cursor-pointer"
                onClick={() => {
                  if (typeof window !== 'undefined' && (window as any).AIWidget) {
                    (window as any).AIWidget.open();
                  }
                }}
              >
                <MessageSquare className="size-4" /> Track with AI Support
              </Button>
              <Button variant="outline" className="rounded-none cursor-pointer" onClick={close}>
                Continue shopping <ArrowRight className="size-4 ml-1" />
              </Button>
            </div>
          </div>
        ) : (
          <div className="grid md:grid-cols-[1.2fr_1fr] gap-8">
            <div>
              <p className="eyebrow text-muted-foreground mb-2">Step 1 of 1</p>
              <DialogTitle className="font-display text-3xl uppercase">Delivery details</DialogTitle>
              <DialogDescription className="mt-2">Where should we send your pieces?</DialogDescription>
              {serverError && (
                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 text-red-600 text-xs rounded">
                  {serverError}
                </div>
              )}
              <form className="mt-5 grid grid-cols-2 gap-3" onSubmit={e => { e.preventDefault(); placeOrder(); }} noValidate>
                {fields.map(f => (
                  <label key={f.key} className={f.span ? 'col-span-2' : 'col-span-2 sm:col-span-1'}>
                    <span className="text-[10px] font-semibold uppercase tracking-[1px] text-muted-foreground">{f.label}</span>
                    {f.key === 'country' ? (
                      <select value={details.country} onChange={e => set('country', e.target.value)} className="mt-1 w-full rounded-none border border-input bg-background p-2.5 text-sm outline-none focus:border-foreground">
                        {['Pakistan', 'United Arab Emirates', 'United Kingdom', 'United States'].map(c => <option key={c}>{c}</option>)}
                      </select>
                    ) : (
                      <input type={f.type ?? 'text'} value={details[f.key]} placeholder={f.placeholder} onChange={e => set(f.key, e.target.value)} className="mt-1 w-full rounded-none border border-input bg-background p-2.5 text-sm outline-none focus:border-foreground" />
                    )}
                    {errors[f.key] && <span role="alert" className="text-[10px] text-red-600">{errors[f.key]}</span>}
                  </label>
                ))}
              </form>
            </div>
            <aside className="border border-border p-5 h-fit">
              <p className="text-[10px] font-semibold uppercase tracking-[1px] text-muted-foreground mb-4">Order summary</p>
              <div className="space-y-3">
                {bag.map(item => (
                  <div key={`${item.product.id}-${item.size}`} className="flex items-center gap-3">
                    <img src={item.product.image} alt="" width={44} height={52} className="h-[52px] w-11 object-cover" />
                    <div className="flex-1 text-xs leading-5"><p className="font-semibold">{item.product.name}</p><p className="text-muted-foreground">{item.size} × {item.quantity}</p></div>
                    <span className="text-xs">{money(item.product.price * item.quantity)}</span>
                  </div>
                ))}
              </div>
              <div className="mt-5 border-t border-border pt-4 space-y-2 text-xs">
                <div className="flex justify-between"><span className="text-muted-foreground">Subtotal</span><span>{money(subtotal)}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Shipping</span><span>{money(shipping)}</span></div>
                <div className="flex justify-between font-semibold text-sm pt-2 border-t border-border"><span>Total</span><span>{money(subtotal + shipping)}</span></div>
              </div>
              <Button className="w-full rounded-none h-12 mt-5 cursor-pointer" onClick={placeOrder} disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="size-4 animate-spin mr-2" /> Creating Order...
                  </>
                ) : (
                  <>
                    Place order · {money(subtotal + shipping)} <ArrowRight className="size-4 ml-1" />
                  </>
                )}
              </Button>
              <p className="mt-3 text-[10px] leading-5 text-muted-foreground flex gap-2"><Check className="size-3.5 shrink-0 mt-0.5" /> Cash on delivery. Instant confirmation with 5-digit Order ID.</p>
            </aside>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
