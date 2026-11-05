'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export type NotePage = { slug: string; title: string; body: string };
export type Piece = { title: string; text: string };
export type Content = { notes: NotePage[]; dreams: Piece[]; fragments: Piece[]; unfinished: Piece[] };

type Section = 'notes' | 'dreams' | 'fragments' | 'unfinished' | 'now' | 'about';

const SECTIONS: { id: Section; label: string }[] = [
  { id: 'notes', label: 'Notes' },
  { id: 'dreams', label: 'Dreams' },
  { id: 'fragments', label: 'Fragments' },
  { id: 'unfinished', label: 'Unfinished' },
  { id: 'now', label: 'Now' },
  { id: 'about', label: 'About' },
];
const LABEL = Object.fromEntries(SECTIONS.map(s => [s.id, s.label])) as Record<Section, string>;

type Def =
  | { kind: 'cover' | 'intro' | 'toc' | 'blank' | 'back' }
  | { kind: 'note'; section: 'notes'; note: NotePage }
  | { kind: 'piece'; section: 'dreams' | 'fragments' | 'unfinished'; piece: Piece }
  | { kind: 'now' | 'about'; section: 'now' | 'about' };

const sectionOf = (def: Def): Section | undefined => ('section' in def ? def.section : undefined);

// Page order. The total is always even so every leaf has a front and a back.
function buildDefs(c: Content): Def[] {
  const defs: Def[] = [{ kind: 'cover' }, { kind: 'intro' }, { kind: 'toc' }];
  c.notes.forEach(note => defs.push({ kind: 'note', section: 'notes', note }));
  for (const [section, list] of [['dreams', c.dreams], ['fragments', c.fragments], ['unfinished', c.unfinished]] as const) {
    list.forEach(piece => defs.push({ kind: 'piece', section, piece }));
  }
  defs.push({ kind: 'now', section: 'now' }, { kind: 'about', section: 'about' });
  if ((defs.length + 1) % 2 !== 0) defs.push({ kind: 'blank' });
  defs.push({ kind: 'back' });
  return defs;
}

// Printed page numbers start at the contents page.
const pageNumber = (index: number, def: Def) =>
  index >= 2 && def.kind !== 'blank' && def.kind !== 'back' ? String(index - 1) : '';

// Keep in step with --turn in style.css.
const TURN_MS = 1400;

export default function Notebook({ content }: { content: Content }) {
  const defs = useMemo(() => buildDefs(content), [content]);
  const n = defs.length;
  const starts = useMemo(() => {
    const map = {} as Record<Section, number>;
    defs.forEach((def, i) => { const s = sectionOf(def); if (s && map[s] === undefined) map[s] = i; });
    return map;
  }, [defs]);

  const [wide, setWide] = useState(true);
  const [spread, setSpread] = useState(0);
  const [turning, setTurning] = useState<number | null>(null);
  const [lifting, setLifting] = useState<number[]>([]);
  const liftTimers = useRef<Record<number, number>>({});
  const [ready, setReady] = useState(false);
  const wideRef = useRef(true);
  const spreadRef = useRef(0);
  const prevSpread = useRef(0);
  const stepper = useRef<number | undefined>(undefined);
  const turnTimer = useRef<number | undefined>(undefined);
  const swipe = useRef<{ x: number; y: number } | null>(null);

  const spreadOf = useCallback((page: number, w: boolean) => (w ? Math.ceil(page / 2) : page), []);
  const pageOf = useCallback((s: number, w: boolean) => (w ? (s === 0 ? 0 : Math.min(2 * s, n - 1)) : s), [n]);

  // Moves to a spread. Long jumps riffle through the pages one by one.
  const goToSpread = useCallback((target: number) => {
    const max = wideRef.current ? n / 2 : n - 1;
    const to = Math.max(0, Math.min(max, target));
    window.clearInterval(stepper.current);
    const from = spreadRef.current;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || Math.abs(to - from) <= 1) {
      spreadRef.current = to;
      setSpread(to);
      return;
    }
    const dir = to > from ? 1 : -1;
    stepper.current = window.setInterval(() => {
      const next = spreadRef.current + dir;
      spreadRef.current = next;
      setSpread(next);
      if (next === to) window.clearInterval(stepper.current);
    }, 150);
  }, [n]);

  const goToPage = useCallback((page: number) => goToSpread(spreadOf(page, wideRef.current)), [goToSpread, spreadOf]);

  // Start-up: read the layout, restore a page from the address, then allow animation.
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 900px)');
    const fromHash = () => {
      const m = /^#(\d+)$/.exec(window.location.hash);
      return m ? Math.min(Number(m[1]), n - 1) : 0;
    };
    wideRef.current = mq.matches;
    setWide(mq.matches);
    const first = spreadOf(fromHash(), mq.matches);
    spreadRef.current = first;
    prevSpread.current = first;
    setSpread(first);
    const raf = requestAnimationFrame(() => requestAnimationFrame(() => setReady(true)));

    const onLayout = () => {
      const before = wideRef.current;
      if (before === mq.matches) return;
      const page = pageOf(spreadRef.current, before);
      wideRef.current = mq.matches;
      setWide(mq.matches);
      const s = spreadOf(page, mq.matches);
      spreadRef.current = s;
      prevSpread.current = s;
      setSpread(s);
    };
    const onHash = () => goToSpread(spreadOf(fromHash(), wideRef.current));
    mq.addEventListener('change', onLayout);
    window.addEventListener('hashchange', onHash);
    return () => {
      cancelAnimationFrame(raf);
      mq.removeEventListener('change', onLayout);
      window.removeEventListener('hashchange', onHash);
      window.clearInterval(stepper.current);
      window.clearTimeout(turnTimer.current);
      Object.values(liftTimers.current).forEach(id => window.clearTimeout(id));
    };
  }, [n, spreadOf, pageOf, goToSpread]);

  // The leaf being turned sits on top of the pile and lifts off it while it moves.
  useEffect(() => {
    const prev = prevSpread.current;
    if (prev === spread) return;
    const leaf = Math.min(prev, spread);
    setTurning(leaf);
    window.clearTimeout(turnTimer.current);
    turnTimer.current = window.setTimeout(() => setTurning(null), TURN_MS + 100);
    setLifting(list => (list.includes(leaf) ? list : [...list, leaf]));
    window.clearTimeout(liftTimers.current[leaf]);
    liftTimers.current[leaf] = window.setTimeout(() => setLifting(list => list.filter(k => k !== leaf)), TURN_MS + 100);
    prevSpread.current = spread;
  }, [spread]);

  // Keep the address in step so a refresh or a shared link lands on the same page.
  useEffect(() => {
    if (!ready) return;
    const page = pageOf(spread, wide);
    window.history.replaceState(null, '', page === 0 ? window.location.pathname + window.location.search : '#' + page);
  }, [spread, wide, ready, pageOf]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.target instanceof Element && e.target.closest('input, textarea, select, dialog')) return;
      if (e.key === 'ArrowRight') goToSpread(spreadRef.current + 1);
      else if (e.key === 'ArrowLeft') goToSpread(spreadRef.current - 1);
      else if (e.key === 'Home') goToSpread(0);
      else if (e.key === 'End') goToSpread(Infinity);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [goToSpread]);

  const maxSpread = wide ? n / 2 : n - 1;
  const left = wide && spread > 0 ? 2 * spread - 1 : null;
  const right = wide ? (2 * spread <= n - 1 ? 2 * spread : null) : spread;
  const shown = new Set([left, right].filter((x): x is number => x !== null));
  const leafCount = wide ? n / 2 : n;
  const lead = defs[right ?? left ?? 0];
  const activeSection = sectionOf(lead) ?? (left !== null ? sectionOf(defs[left]) : undefined);

  const named = [right, left].map(i => (i === null ? undefined : defs[i])).find(d => d && sectionOf(d));
  const name = named ? LABEL[sectionOf(named)!]
    : lead.kind === 'cover' ? 'Cover' : lead.kind === 'back' ? 'Back cover' : lead.kind === 'toc' ? 'Contents'
      : lead.kind === 'intro' ? 'Inside cover' : 'Blank page';
  const numbers = [left, right].filter((x): x is number => x !== null).map(i => pageNumber(i, defs[i])).filter(Boolean);
  const status = numbers.length === 2 ? `${name}, pages ${numbers[0]} and ${numbers[1]}` : numbers.length === 1 ? `${name}, page ${numbers[0]}` : name;

  const pos = !wide ? 'open' : spread === 0 ? 'start' : spread === maxSpread ? 'end' : 'open';

  return (
    <div className="nb" data-mode={wide ? 'spread' : 'single'} data-ready={ready}>
      <div className="shelf" data-pos={pos}>
        <div
          className="stage"
          onPointerDown={e => {
            if (e.pointerType === 'mouse' || (e.target as HTMLElement).closest('button')) return;
            swipe.current = { x: e.clientX, y: e.clientY };
          }}
          onPointerUp={e => {
            const start = swipe.current;
            swipe.current = null;
            if (!start) return;
            const dx = e.clientX - start.x;
            const dy = e.clientY - start.y;
            if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) goToSpread(spreadRef.current + (dx < 0 ? 1 : -1));
          }}
        >
          {Array.from({ length: leafCount }, (_, k) => {
            const front = wide ? 2 * k : k;
            const back = wide ? 2 * k + 1 : null;
            const flipped = k < spread;
            const z = turning === k ? 999 : flipped ? k : leafCount - k;
            const cls = ['leaf', flipped ? 'flipped' : '', Math.abs(k - spread) <= 3 ? 'near' : '', lifting.includes(k) ? 'lifting' : ''].join(' ');
            return (
              <div key={k} className={cls} style={{ zIndex: z }}>
                <Face def={defs[front]} index={front} side="front" visible={shown.has(front)} starts={starts} go={goToPage} />
                <Face def={back === null ? undefined : defs[back]} index={back ?? -1} side="back" visible={back !== null && shown.has(back)} starts={starts} go={goToPage} />
              </div>
            );
          })}
          <div className="rings" aria-hidden="true" />
          <button type="button" className="corner prev" aria-hidden="true" tabIndex={-1} hidden={spread === 0}
                  onClick={() => goToSpread(spreadRef.current - 1)} />
          <button type="button" className="corner next" aria-hidden="true" tabIndex={-1} hidden={spread === maxSpread}
                  onClick={() => goToSpread(spreadRef.current + 1)} />
          <div className="ribbon" aria-hidden="true" />
        </div>
        <div className="tabs" role="group" aria-label="Sections">
          {SECTIONS.map(s => (
            <button key={s.id} type="button" data-section={s.id} aria-current={activeSection === s.id ? 'true' : undefined}
                    onClick={() => goToPage(starts[s.id])}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="controls">
        <button type="button" className="flip" disabled={spread === 0} onClick={() => goToSpread(spreadRef.current - 1)}>
          Previous page
        </button>
        <p className="status" aria-live="polite">{status}</p>
        <button type="button" className="flip" disabled={spread === maxSpread} onClick={() => goToSpread(spreadRef.current + 1)}>
          Next page
        </button>
      </div>
    </div>
  );
}

function Face({ def, index, side, visible, starts, go }: {
  def: Def | undefined; index: number; side: 'front' | 'back'; visible: boolean;
  starts: Record<Section, number>; go: (page: number) => void;
}) {
  const bound = def?.kind === 'cover' || def?.kind === 'back';
  const cls = ['face', side, bound ? (def!.kind === 'back' ? 'backcover' : 'cover') : 'paper'].join(' ');
  return (
    <div className={cls} aria-hidden={visible ? undefined : true} inert={!visible}>
      {def && (bound ? <Bound def={def} /> : <Sheet def={def} index={index} side={side} starts={starts} go={go} />)}
    </div>
  );
}

function Bound({ def }: { def: Def }) {
  if (def.kind === 'cover') {
    return <>
      <p className="cover-mark">from me, to her</p>
      <h1>
        <span className="line l1">Some things</span>{' '}
        <span className="line l2">need a place</span>{' '}
        <span className="line l3">to exist.</span>
      </h1>
      <span className="band" />
    </>;
  }
  return <>
    <p className="cover-end">That is all for now.</p>
    <span className="band" />
  </>;
}

function Sheet({ def, index, side, starts, go }: {
  def: Def; index: number; side: 'front' | 'back'; starts: Record<Section, number>; go: (page: number) => void;
}) {
  const section = sectionOf(def);
  const head = def.kind === 'toc' ? 'Contents' : section ? LABEL[section] : '';
  return (
    <div className="sheet">
      <div className="head"><span>{head}</span></div>
      <div className="lines">{body(def, starts, go)}</div>
      <span className={'num ' + side}>{pageNumber(index, def)}</span>
    </div>
  );
}

function body(def: Def, starts: Record<Section, number>, go: (page: number) => void) {
  switch (def.kind) {
    case 'intro':
      return <>
        <p>Thoughts that took the long way home. A few strange dreams. And a website that is still figuring itself out.</p>
        <p className="hint gap">Turn the page. Use the corners, the arrow keys, or swipe.</p>
      </>;
    case 'toc':
      return <>
        <h2 className="title">Contents</h2>
        <ol className="toc">
          {SECTIONS.map(s => (
            <li key={s.id}>
              <button type="button" onClick={() => go(starts[s.id])}>
                <span>{s.label}</span><i className="dots" /><span>{starts[s.id] - 1}</span>
              </button>
            </li>
          ))}
        </ol>
      </>;
    case 'note':
      return <>
        <h2 className="title">{def.note.title}</h2>
        <p>{def.note.body}</p>
      </>;
    case 'piece':
      return <>
        <h2 className="title">{def.piece.title}</h2>
        <p>{def.piece.text}</p>
      </>;
    case 'now':
      return <>
        <h2 className="title">Now</h2>
        <p><b>Reading.</b> A paperback with a cracked spine and a very patient narrator.</p>
        <p><b>Making.</b> This notebook, one page at a time.</p>
        <p><b>Listening.</b> Rain on the window, mostly.</p>
        <p><b>Eating.</b> More soup than strictly necessary.</p>
      </>;
    case 'about':
      return <>
        <h2 className="title">About</h2>
        <p>A small personal notebook on the internet. It started on a whim and has not been talked out of it.</p>
        <p className="gap">No sign-up, no tracking, no comment box. Everything on these pages is public and meant to be read.</p>
      </>;
    default:
      return null;
  }
}
