'use client';

import { useEffect, useState } from 'react';

type Theme = 'paper' | 'night';
const KEY = 'theme';

function systemTheme(): Theme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'night' : 'paper';
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    let saved: string | null = null;
    try { saved = localStorage.getItem(KEY); } catch { /* storage can be blocked */ }
    const initial: Theme = saved === 'night' || saved === 'paper' ? saved : systemTheme();
    document.documentElement.dataset.theme = initial;
    setTheme(initial);
  }, []);

  function flip() {
    const next: Theme = (theme ?? systemTheme()) === 'night' ? 'paper' : 'night';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem(KEY, next); } catch { /* storage can be blocked */ }
    setTheme(next);
  }

  const night = theme === 'night';
  return (
    <button type="button" className="lamp" onClick={flip} aria-pressed={night}
            aria-label={night ? 'Switch to daylight' : 'Switch to night'}>
      <span className="lamp-bulb" aria-hidden="true" />
      <span>{night ? 'Lamp on' : 'Lamp off'}</span>
    </button>
  );
}
