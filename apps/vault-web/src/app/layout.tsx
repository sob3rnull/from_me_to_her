import './style.css';
import { connection } from 'next/server';
export const metadata = { title: 'The private archive', robots: {index: false, follow: false} };
export default async function Layout({children}: {children: React.ReactNode}) {
  await connection(); // A fresh CSP nonce belongs to each response, never a static export.
  return <html lang="en"><body>{children}</body></html>;
}
