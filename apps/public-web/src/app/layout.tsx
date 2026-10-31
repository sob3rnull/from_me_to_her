import '@fontsource-variable/newsreader/wght.css';
import '@fontsource-variable/newsreader/wght-italic.css';
import '@fontsource/special-elite/latin-400.css';
import './style.css';

export const metadata = { title: 'from me, to her', description: 'A small corner of the internet.' };

export default function Layout({children}: {children: React.ReactNode}) {
  return <html lang="en"><body>{children}</body></html>;
}
