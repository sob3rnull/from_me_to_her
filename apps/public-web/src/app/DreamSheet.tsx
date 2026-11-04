'use client';

import { useEffect, useRef, useState } from 'react';

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export default function DreamSheet({ dreams }: { dreams: string[] }) {
  const [dream, setDream] = useState(dreams[0] ?? '');
  const [typed, setTyped] = useState(dreams[0] ?? '');
  const [typing, setTyping] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);

  function dreamAgain() {
    if (dreams.length < 2) return;
    let next = dream;
    while (next === dream) next = dreams[Math.floor(Math.random() * dreams.length)];
    if (timer.current) clearInterval(timer.current);
    setDream(next);
    if (reducedMotion()) {
      setTyped(next);
      setTyping(false);
      return;
    }
    let count = 0;
    setTyped('');
    setTyping(true);
    timer.current = setInterval(() => {
      count += 1;
      setTyped(next.slice(0, count));
      if (count >= next.length) {
        if (timer.current) clearInterval(timer.current);
        setTyping(false);
      }
    }, 28);
  }

  return (
    <figure className="sheet">
      <figcaption>From the drawer</figcaption>
      <p className="typed" aria-hidden="true">
        {typed}<span className={typing ? 'caret typing' : 'caret'} />
      </p>
      <p className="sr-only" aria-live="polite">{dream}</p>
      <button type="button" className="again" onClick={dreamAgain}>Another dream</button>
    </figure>
  );
}
