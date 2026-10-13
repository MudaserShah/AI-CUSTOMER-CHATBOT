import tee from '@/assets/washed-tee.jpg';
import hoodie from '@/assets/core-hoodie.jpg';
import cargo from '@/assets/cargo-pants.jpg';
export const products = [
  { id: 'tee', name: 'The Heavyweight Tee', category: 'T-shirts', color: 'Washed Black', price: 48, image: tee, tag: 'BESTSELLER', description: 'A considered everyday essential. Heavyweight cotton, a relaxed boxy fit, and a vintage-inspired garment wash.', material: '100% cotton · 240 GSM' },
  { id: 'hoodie', name: 'Essential Oversized Hoodie', category: 'Hoodies', color: 'Charcoal', price: 95, image: hoodie, tag: 'NEW ARRIVAL', description: 'Your off-duty uniform. A generous oversized silhouette in soft heavyweight cotton, finished with a structured hood.', material: '100% cotton · 450 GSM' },
  { id: 'cargo', name: 'Utility Cargo Pants', category: 'Pants', color: 'Stone Grey', price: 85, image: cargo, tag: 'NEW ARRIVAL', description: 'Made for the everyday. A wide-leg silhouette, functional cargo pockets, and durable washed cotton.', material: '100% cotton · relaxed fit' },
];
export type Product = (typeof products)[number];
export type BagItem = { product: Product; size: string; quantity: number };
export const money = (amount: number) => `$${amount.toFixed(2)}`;
