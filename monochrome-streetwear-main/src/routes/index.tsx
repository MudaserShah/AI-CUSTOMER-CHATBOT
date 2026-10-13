import { createFileRoute } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { ArrowUpRight, ArrowRight, Search, ShoppingBag, Menu, Heart, Plus, Minus, Check, X, SlidersHorizontal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Sheet, SheetContent, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { CheckoutDialog } from '@/components/checkout-dialog';
import { products, money, type Product, type BagItem } from '@/lib/catalog';
import campaign from '@/assets/urbanvibe-campaign.jpg';

export const Route = createFileRoute('/')({
  head: () => ({ meta: [
    { title: 'UrbanVibe — Elevated Streetwear & Everyday Essentials' },
    { name: 'description', content: 'Discover UrbanVibe. Modern luxury streetwear, heavyweight essentials, and considered silhouettes for your everyday uniform.' },
    { property: 'og:title', content: 'UrbanVibe — Elevated Streetwear' },
    { property: 'og:description', content: 'Independent attitude. Elevated essentials. Explore the latest UrbanVibe collection.' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
  ] }),
  component: Index,
});

function Index() {
  const [category, setCategory] = useState('All pieces');
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<Product | null>(null);
  const [size, setSize] = useState('M');
  const [bag, setBag] = useState<BagItem[]>([]);
  const [bagOpen, setBagOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [sort, setSort] = useState('Featured');
  const count = bag.reduce((total, item) => total + item.quantity, 0);
  const subtotal = bag.reduce((total, item) => total + item.product.price * item.quantity, 0);
  const shown = products.filter(p => category === 'All pieces' || (category === 'New arrivals' ? p.tag === 'NEW ARRIVAL' : p.category === category)).sort((a,b) => sort === 'Price: low to high' ? a.price-b.price : sort === 'Price: high to low' ? b.price-a.price : 0);
  function shop(filter = 'All pieces') { setCategory(filter); setMenuOpen(false); document.getElementById('collection')?.scrollIntoView({ behavior: 'smooth' }); }
  function openProduct(product: Product) { setSize('M'); setSelected(product); setSearchOpen(false); }
  function addToBag() {
    if (!selected) return;
    const product = selected;
    setBag(items => { const found = items.find(i => i.product.id === product.id && i.size === size); return found ? items.map(i => i === found ? { ...i, quantity: i.quantity + 1 } : i) : [...items, {product, size, quantity: 1}]; });
    setSelected(null); setBagOpen(true);
  }
  function quantity(id: string, itemSize: string, delta: number) { setBag(items => items.map(i => i.product.id === id && i.size === itemSize ? {...i, quantity: i.quantity + delta} : i).filter(i => i.quantity > 0)); }
  useEffect(() => {
    function clearBag() { setBag([]); setBagOpen(false); }
    window.addEventListener('urbanvibe:order-placed', clearBag);
    return () => window.removeEventListener('urbanvibe:order-placed', clearBag);
  }, []);
  return (
    <main>
      <div className="bg-highlight text-foreground h-8 flex items-center justify-center gap-3 text-[9px] font-bold uppercase tracking-[1.5px]">A new perspective. The latest collection is here. <ArrowUpRight size={12} /></div>
      <header className="site-header content-shell bg-inverse text-inverse-foreground flex items-center justify-between">
        <a href="/" className="wordmark text-[38px]" aria-label="UrbanVibe home">UrbanVibe<span className="text-highlight">®</span></a>
        <nav className="hidden md:flex items-center gap-6" aria-label="Main navigation">
          <Button variant="nav" onClick={() => shop()}>Shop all</Button>
          <Button variant="nav" onClick={() => shop('New arrivals')}>New arrivals <span className="w-1 h-1 rounded-full bg-highlight" /></Button>
          <Button variant="nav" onClick={() => shop('Hoodies')}>Essentials</Button>
          <Button variant="nav" onClick={() => setAboutOpen(true)}>The brand <ArrowUpRight size={12} /></Button>
        </nav>
        <div className="flex items-center gap-2 md:gap-4">
          <Button variant="nav" size="icon" aria-label="Search products" title="Search products" onClick={() => setSearchOpen(true)}><Search className="size-5" /></Button>
          <Button variant="nav" className="text-inverse-foreground gap-2" aria-label={`Shopping bag, ${count} items`} onClick={() => setBagOpen(true)}><ShoppingBag className="size-5" /><span className="hidden sm:inline">Bag</span><span className="text-[10px]">({count})</span></Button>
          <Button variant="nav" size="icon" className="md:hidden" aria-label="Open menu" onClick={() => setMenuOpen(true)}><Menu /></Button>
        </div>
      </header>
      <section className="hero text-inverse-foreground" aria-label="UrbanVibe latest collection">
        <img className="hero-image" src={campaign} alt="Two models wearing UrbanVibe oversized essentials beside brutalist architecture" width={1920} height={1024} fetchPriority="high" />
        <div className="hero-copy">
          <div className="eyebrow flex items-center gap-3"><span className="h-px w-7 bg-highlight" /> The everyday uniform / Vol. 01</div>
          <h1 className="wordmark hero-title">UrbanVibe<span className="text-highlight">.</span></h1>
          <p className="text-[22px] md:text-[28px] font-medium mb-3">Not just worn. Lived in.</p>
          <p className="text-inverse-foreground/75 text-xs md:text-sm leading-6 max-w-[310px] mb-8">Elevated essentials. Uncompromising comfort.<br />Streetwear for wherever life takes you.</p>
          <Button variant="hero" onClick={() => shop()}>Explore the collection <ArrowUpRight className="ml-4" /></Button>
        </div>
        <div className="hero-bottom text-[9px] uppercase tracking-[1.5px] text-inverse-foreground/75"><span>Independent attitude. Universal expression.</span><span className="hidden sm:flex items-center gap-3">01 — 03 <span className="w-14 h-px bg-inverse-foreground" /><span className="w-4 h-px bg-inverse-foreground/30" /></span></div>
      </section>
      <div className="content-shell border-b border-border flex justify-between items-center py-5 gap-4 text-[9px] uppercase font-semibold tracking-[1px]"><span className="flex items-center gap-2"><Check size={13} /> Considered details</span><span className="flex items-center gap-2"><Check size={13} /> Premium fabrics</span><span className="hidden sm:flex items-center gap-2"><Check size={13} /> Made for every day</span><span className="hidden md:flex items-center gap-2">Less, but better. <ArrowUpRight size={13} /></span></div>
      <section id="collection" className="content-shell pt-14 pb-16 scroll-mt-6">
        <div className="flex items-end justify-between gap-4 mb-7"><div><p className="eyebrow text-muted-foreground mb-3">The curated edit</p><h2 className="font-display text-4xl md:text-5xl uppercase font-semibold">Your next rotation.</h2></div><Button variant="link" className="hidden sm:flex text-[11px] px-0" onClick={() => shop()}>Shop all pieces <ArrowUpRight /></Button></div>
        <div className="flex items-center justify-between border-b border-border pb-5 mb-6 gap-3"><div className="flex gap-1 sm:gap-4 overflow-x-auto" role="group" aria-label="Product categories">{['All pieces','T-shirts','Hoodies','Pants'].map(c => <Button key={c} size="sm" variant={category === c ? 'default' : 'ghost'} className="rounded-none text-[10px] sm:text-xs" onClick={() => setCategory(c)}>{c}</Button>)}</div><label className="hidden sm:flex gap-2 items-center text-[10px] text-muted-foreground"><SlidersHorizontal size={13}/><select aria-label="Sort products" className="bg-background py-2 outline-none" value={sort} onChange={e => setSort(e.target.value)}><option>Featured</option><option>Price: low to high</option><option>Price: high to low</option></select></label></div>
        {category === 'New arrivals' && <p className="text-xs mb-5 text-muted-foreground">New arrivals · {shown.length} pieces</p>}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 sm:gap-x-6 gap-y-8">
          {shown.map(p => <article className="product-tile" key={p.id}>
            <div className="product-photo"><img src={p.image} alt={p.name} className="product-image" width={1024} height={1024} loading="lazy" /><span className="product-tag">{p.tag}</span><Button variant="ghost" size="icon" className="absolute top-3 right-3" aria-label={`${favorites.includes(p.id) ? 'Unsave' : 'Save'} ${p.name}`} title="Save piece" onClick={() => setFavorites(ids => ids.includes(p.id) ? ids.filter(id => id !== p.id) : [...ids,p.id])}><Heart className={favorites.includes(p.id) ? 'fill-foreground' : ''} /></Button><Button className="product-action rounded-none bg-background text-foreground hover:bg-primary hover:text-primary-foreground text-[10px] h-10" onClick={() => openProduct(p)}>Quick add <Plus size={14}/></Button></div>
            <div className="flex justify-between items-start gap-2 mt-4"><Button variant="link" className="p-0 h-auto text-left whitespace-normal justify-start text-xs sm:text-sm font-semibold" onClick={() => openProduct(p)}>{p.name}</Button><span className="text-xs sm:text-sm shrink-0">{money(p.price)}</span></div><p className="mt-1.5 text-[10px] text-muted-foreground">{p.color} / Oversized fit</p><div className="flex gap-1.5 mt-3"><span className="swatch bg-swatch-black ring-1 ring-foreground ring-offset-2 ring-offset-background" title={p.color}/><span className="swatch bg-swatch-stone"/><span className="swatch bg-swatch-olive"/></div>
          </article>)}
        </div>
      </section>
      <div className="marquee"><div className="marquee-track"><span>LESS NOISE. MORE YOU.</span><span className="text-muted-foreground">✳</span><span>BUILT FOR THE EVERYDAY.</span><span className="text-muted-foreground">✳</span><span className="hidden sm:inline">BEYOND THE ORDINARY.</span></div></div>
      <section className="content-shell bg-inverse text-inverse-foreground py-16 md:py-20 grid md:grid-cols-2 gap-10 md:gap-20"><div><p className="eyebrow text-inverse-muted mb-5">The UrbanVibe mindset</p><h2 className="font-display font-semibold text-5xl md:text-6xl uppercase leading-none">Good clothes.<br />No compromises.</h2></div><div className="md:pt-8"><p className="text-sm leading-7 text-inverse-muted max-w-md">Rooted in the city. Made for the individual. We believe the best pieces are the ones you keep reaching for — considered silhouettes, substantial fabrics, and a little independent spirit.</p><Button variant="nav" className="px-0 mt-6 text-inverse-foreground underline underline-offset-8" onClick={() => setAboutOpen(true)}>Meet UrbanVibe <ArrowUpRight /></Button></div></section>
      <footer className="bg-inverse text-inverse-foreground content-shell pb-8"><div className="border-t border-inverse-muted/25 pt-10 flex flex-wrap gap-8 justify-between items-end"><a href="/" className="wordmark footer-wordmark">UrbanVibe<span className="text-highlight">.</span></a><p className="text-xs text-inverse-muted max-w-[180px] leading-6">Elevated essentials.<br />Independent by nature.</p></div><div className="mt-10 flex justify-between gap-4 text-[9px] text-inverse-muted"><span>© 2026 UrbanVibe. All rights reserved.</span><span>Designed for the everyday.</span></div></footer>
      <Dialog open={selected !== null} onOpenChange={open => { if (!open) setSelected(null); }}><DialogContent className="max-w-3xl grid md:grid-cols-2 gap-7 max-h-[90vh] overflow-y-auto">{selected && <><img src={selected.image} alt={selected.name} width={1024} height={1024} className="w-full max-h-[35vh] md:max-h-none object-contain bg-secondary"/><div className="flex flex-col justify-center py-5"><p className="eyebrow text-muted-foreground mb-3">{selected.tag}</p><DialogTitle className="font-display text-3xl uppercase">{selected.name}</DialogTitle><p className="my-4 font-semibold">{money(selected.price)}</p><DialogDescription className="leading-6">{selected.description}</DialogDescription><p className="text-xs text-muted-foreground mt-3">{selected.material}</p><p className="text-xs mt-6 mb-3">Size: {size}</p><div className="flex gap-2">{['XS','S','M','L','XL'].map(s => <Button key={s} variant={size === s ? 'default' : 'outline'} className="rounded-none flex-1" aria-pressed={s === size} onClick={() => setSize(s)}>{s}</Button>)}</div><Button className="rounded-none mt-6 h-12" onClick={addToBag}>Add to bag <Plus /></Button></div></>}</DialogContent></Dialog>
      <Sheet open={bagOpen} onOpenChange={setBagOpen}><SheetContent className="w-full sm:max-w-md flex flex-col"><SheetTitle className="font-display text-3xl uppercase">Your bag ({count})</SheetTitle><SheetDescription>{count ? 'Your next rotation is taking shape.' : 'Make room for your new everyday essentials.'}</SheetDescription><div className="flex-1 overflow-y-auto mt-6">{bag.map(item => <div key={`${item.product.id}-${item.size}`} className="flex gap-4 py-5 border-b"><img src={item.product.image} width={96} height={112} alt={item.product.name} className="w-24 h-28 object-cover"/><div className="flex-1"><p className="text-xs font-semibold">{item.product.name}</p><p className="text-xs text-muted-foreground mt-2">{item.product.color} · {item.size}</p><p className="text-xs mt-2">{money(item.product.price)}</p><div className="flex items-center gap-3 mt-2"><Button variant="outline" size="icon" className="w-7 h-7" aria-label={`Decrease quantity of ${item.product.name}`} onClick={() => quantity(item.product.id,item.size,-1)}><Minus size={12}/></Button><span className="text-xs">{item.quantity}</span><Button variant="outline" size="icon" className="w-7 h-7" aria-label={`Increase quantity of ${item.product.name}`} onClick={() => quantity(item.product.id,item.size,1)}><Plus size={12}/></Button></div></div><Button variant="ghost" size="icon" className="h-6 w-6" aria-label={`Remove ${item.product.name}`} onClick={() => setBag(items => items.filter(i => i !== item))}><X size={12}/></Button></div>)}{!count && <Button className="rounded-none mt-5" onClick={() => {setBagOpen(false);shop();}}>Explore the collection <ArrowRight/></Button>}</div>{count > 0 && <div className="border-t pt-5"><div className="flex justify-between text-sm font-semibold mb-4"><span>Subtotal</span><span>{money(subtotal)}</span></div><Button className="w-full rounded-none h-12" onClick={() => { setBagOpen(false); setCheckoutOpen(true); }}>Checkout <ArrowRight/></Button><p className="text-xs leading-5 mt-4 text-muted-foreground">Next step: enter your delivery details. This is a preview store — no payment will be taken.</p></div>}</SheetContent></Sheet>
      <CheckoutDialog open={checkoutOpen} onOpenChange={setCheckoutOpen} bag={bag} subtotal={subtotal} />
      <Dialog open={searchOpen} onOpenChange={setSearchOpen}><DialogContent><DialogTitle className="font-display text-3xl uppercase">Find your next piece</DialogTitle><DialogDescription>Search the UrbanVibe collection.</DialogDescription><input aria-label="Search collection" autoFocus value={query} onChange={e => setQuery(e.target.value)} placeholder="Try hoodies, cargo, heavyweight…" className="border-b bg-background p-3 text-sm outline-none focus:border-foreground"/><div className="space-y-2">{products.filter(p => `${p.name} ${p.category} ${p.color}`.toLowerCase().includes(query.toLowerCase())).map(p => <Button variant="ghost" key={p.id} className="w-full h-auto justify-start py-2" onClick={() => openProduct(p)}><img src={p.image} alt="" width={52} height={52}/><span className="text-xs flex-1 text-left">{p.name}</span><span className="text-xs">{money(p.price)}</span><ArrowUpRight/></Button>)}{!products.some(p => `${p.name} ${p.category} ${p.color}`.toLowerCase().includes(query.toLowerCase())) && <p className="text-sm text-muted-foreground py-6">No pieces found. Try another search.</p>}</div></DialogContent></Dialog>
      <Sheet open={menuOpen} onOpenChange={setMenuOpen}><SheetContent side="left"><SheetTitle className="wordmark text-3xl">UrbanVibe</SheetTitle><SheetDescription className="sr-only">Main navigation</SheetDescription><div className="flex flex-col items-start gap-4 mt-12">{['All pieces','New arrivals','T-shirts','Hoodies','Pants'].map(c => <Button variant="ghost" key={c} onClick={() => shop(c)}>{c}<ArrowUpRight/></Button>)}<Button variant="ghost" onClick={() => {setMenuOpen(false);setAboutOpen(true);}}>The brand <ArrowUpRight/></Button></div></SheetContent></Sheet>
      <Dialog open={aboutOpen} onOpenChange={setAboutOpen}><DialogContent><p className="eyebrow text-muted-foreground">Independent by nature</p><DialogTitle className="wordmark text-5xl">UrbanVibe.</DialogTitle><DialogDescription className="leading-7 mt-3">Streetwear with a considered point of view. UrbanVibe brings together relaxed silhouettes, tactile fabrics, and an understated palette. Pieces that move with you, not against you. Less noise. More you.</DialogDescription><Button className="rounded-none mt-4" onClick={() => {setAboutOpen(false);shop();}}>Explore our essentials <ArrowUpRight/></Button></DialogContent></Dialog>
    </main>
  );
}
