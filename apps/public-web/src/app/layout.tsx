import '@fontsource-variable/newsreader/wght.css';
import '@fontsource-variable/newsreader/wght-italic.css';
import '@fontsource/special-elite/latin-400.css';
import './style.css';
import Link from 'next/link';
import Knock from '../components/Knock';
import SiteNav from '../components/SiteNav';
import { sealDoor } from '../lib/door';
import ThemeToggle from './ThemeToggle';

export const metadata = { title: { default: 'from me, to her', template: '%s · from me, to her' }, description: 'A small corner of the internet.' };

export default function Layout({children}: {children: React.ReactNode}) {
  return <html lang="en"><body>
    <div className="stripe" aria-hidden="true" />
    <div className="shell">
      <header className="top">
        <Link href="/" className="mark">from me, to her</Link>
        <SiteNav />
        <ThemeToggle />
      </header>
      <main>{children}</main>
      <footer>
        <span>Public words here. Private memories elsewhere<Knock sealed={sealDoor()} /></span>
      </footer>
    </div>
  </body></html>;
}
