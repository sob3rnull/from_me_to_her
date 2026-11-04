import '@fontsource-variable/newsreader/wght.css';
import '@fontsource-variable/newsreader/wght-italic.css';
import '@fontsource/special-elite/latin-400.css';
import '@fontsource/kalam/latin-400.css';
import '@fontsource/kalam/latin-700.css';
import './style.css';
import Knock from '../components/Knock';
import { sealDoor } from '../lib/door';
import ThemeToggle from './ThemeToggle';

export const metadata = { title: 'from me, to her', description: 'A small notebook on the internet.' };

export default function Layout({children}: {children: React.ReactNode}) {
  return <html lang="en"><body>
    <div className="desk">
      <header className="bar">
        <span className="mark">from me, to her</span>
        <ThemeToggle />
      </header>
      <main>{children}</main>
      <footer>
        <span>Public words here. Private memories elsewhere<Knock sealed={sealDoor()} /></span>
      </footer>
    </div>
  </body></html>;
}
