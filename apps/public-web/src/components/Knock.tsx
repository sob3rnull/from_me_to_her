'use client';

import { useRef, useState } from 'react';
import { normalizePhrase } from '../lib/phrase';

type Sealed = { salt: string; iv: string; data: string; iterations: number };

const bytes = (value: string) => Uint8Array.from(atob(value), char => char.charCodeAt(0));

async function open(phrase: string, sealed: Sealed): Promise<string | null> {
  try {
    const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(normalizePhrase(phrase)), 'PBKDF2', false, ['deriveKey']);
    const key = await crypto.subtle.deriveKey(
      { name: 'PBKDF2', salt: bytes(sealed.salt), iterations: sealed.iterations, hash: 'SHA-256' },
      base, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
    const plain = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: bytes(sealed.iv) }, key, bytes(sealed.data));
    const url = new TextDecoder().decode(plain);
    return /^https?:\/\//.test(url) ? url : null;
  } catch {
    return null; // wrong phrase, or no WebCrypto in this context
  }
}

// The full stop at the end of the footer. Nothing about it says "door".
export default function Knock({ sealed }: { sealed: Sealed }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [phrase, setPhrase] = useState('');
  const [state, setState] = useState<'idle' | 'busy' | 'no'>('idle');

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (state === 'busy' || !phrase.trim()) return;
    setState('busy');
    const url = await open(phrase, sealed);
    if (url) {
      window.location.assign(url);
      return;
    }
    setState('no');
  }

  function close() {
    dialog.current?.close();
    setPhrase('');
    setState('idle');
  }

  return (
    <>
      <button type="button" className="knock" aria-label="Knock" onClick={() => dialog.current?.showModal()}>.</button>
      <dialog ref={dialog} className="knock-box" onClose={() => { setPhrase(''); setState('idle'); }}>
        <form onSubmit={submit} className={state === 'no' ? 'shake' : undefined} onAnimationEnd={() => state === 'no' && setState('idle')}>
          <label htmlFor="knock-phrase">Who is there?</label>
          <input id="knock-phrase" type="text" value={phrase} autoComplete="off" autoCapitalize="off"
                 spellCheck={false} onChange={event => setPhrase(event.target.value)} />
          <p className="knock-note" role="status">{state === 'busy' ? 'Listening…' : state === 'no' ? 'Nobody home.' : ' '}</p>
          <div className="knock-actions">
            <button type="submit" disabled={state === 'busy'}>Try it</button>
            <button type="button" className="quiet" onClick={close}>Never mind</button>
          </div>
        </form>
      </dialog>
    </>
  );
}
