'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/notes/', label: 'Notes' },
  { href: '/dreams/', label: 'Dreams' },
  { href: '/now/', label: 'Now' },
  { href: '/about/', label: 'About' },
];

export default function SiteNav() {
  const path = usePathname() || '/';
  return (
    <nav aria-label="Main">
      {LINKS.map(link => {
        const here = path.startsWith(link.href.slice(0, -1));
        return <Link key={link.href} href={link.href} aria-current={here ? 'page' : undefined}>{link.label}</Link>;
      })}
    </nav>
  );
}
