'use client';
import { FormEvent, useEffect, useState } from 'react';

type Session = { csrf: string; stage: number; role: string | null };
type PromiseData = {promise: string; date_made: string | null; status: string; context: string; still_intended: boolean; notes: string};
type Entry = {id: string; title: string; body: string; category: string; shared: boolean; occurred_on: string | null; promise: PromiseData | null};
const blank = {title: '', body: '', category: 'Letters', shared: false, occurred_on: null, promise: null} as Omit<Entry, 'id'>;
const emptyPromise: PromiseData = {promise: '', date_made: null, status: 'ONGOING', context: '', still_intended: true, notes: ''};

export default function Vault() {
  const [session, setSession] = useState<Session | null>(null);
  const [questions, setQuestions] = useState<{id:string;prompt:string}[]>([]);
  const [answers, setAnswers] = useState<Record<string,string>>({});
  const [owner, setOwner] = useState(false);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState({...blank});
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  async function api(path: string, method='GET', data?: unknown, csrf=session?.csrf) {
    const response = await fetch('/api' + path, {method, cache:'no-store', credentials:'same-origin',
      headers: {'Content-Type':'application/json', ...(csrf ? {'X-CSRF-Token':csrf} : {})},
      ...(data !== undefined ? {body:JSON.stringify(data)} : {})});
    const result = await response.json();
    if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Please check the fields and try again.');
    return result;
  }
  async function refresh() {
    const current = await api('/auth/session'); setSession(current);
    if (current.role) {
      setEntries(await api('/entries')); setCategories(await api('/categories'));
    } else {
      setEntries([]); setDraft({...blank}); setEditing(null);
      const challenge = await api('/auth/challenge'); setQuestions(challenge.questions || []);
    }
  }
  useEffect(() => { refresh().catch(e => setError(e.message)); }, []);
  async function run(action: () => Promise<void>) {
    setBusy(true); setError(''); setNotice('');
    try { await action(); } catch(e) {setError(e instanceof Error ? e.message : 'Request failed');}
    finally {setBusy(false);}
  }
  async function unlock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = Object.fromEntries(new FormData(event.currentTarget));
    await run(async () => {
      if (!owner && session?.stage === 0) await api('/auth/gate1','POST',{answers});
      else if (!owner && session?.stage === 1) await api('/auth/gate2','POST',data);
      else await api('/auth/login/' + (owner ? 'owner' : 'reader'),'POST',data);
      setAnswers({}); await refresh();
    });
  }
  async function save(event: FormEvent) {
    event.preventDefault(); await run(async () => {
      await api(editing ? '/entries/' + editing : '/entries', editing ? 'PUT' : 'POST', draft);
      setEditing(null); setDraft({...blank}); await refresh(); setNotice('Saved to your archive.');
    });
  }
  function updatePromise(patch: Partial<PromiseData>) {setDraft({...draft, promise:{...emptyPromise,...draft.promise,...patch}});}

  return <main>
    <nav><a href="http://localhost:3000">from me, to her</a><span>THE PRIVATE ARCHIVE</span></nav>
    <header><p className="eyebrow">A PLACE FOR THE UNSENT</p><h1>{session?.role ? 'The things we keep.' : 'A little closer.'}</h1>
      <p>{session?.role ? 'Letters, memories, and everything in between.' : 'Some doors open one small step at a time.'}</p></header>
    <div className="demo">Local preview · fictional accounts only</div>
    {error && <p role="alert" className="error">{error}</p>}{notice && <p role="status">{notice}</p>}
    {!session && <button onClick={() => run(refresh)} disabled={busy}>Connect to archive</button>}
    {session && !session.role && <section className="gate">
      <div className="tabs"><button onClick={() => setOwner(false)} aria-pressed={!owner}>Reader</button><button onClick={() => setOwner(true)} aria-pressed={owner}>Owner</button></div>
      <h2>{owner ? 'Your writing room' : `Step ${session.stage + 1} of 3`}</h2>
      <form onSubmit={unlock} key={`${owner}-${session.stage}`}>
        {!owner && session.stage === 0 ? questions.map(q => <label key={q.id}>{q.prompt}<input required maxLength={200} value={answers[q.id] || ''} onChange={e => setAnswers({...answers,[q.id]:e.target.value})}/></label>) :
          !owner && session.stage === 1 ? <><label>Anniversary<input name="anniversary" type="date" required/></label><label>His full name<input name="full_name" required maxLength={200}/></label></> :
          <><label>Username<input name="username" autoComplete="username" required maxLength={100}/></label><label>Password<input name="password" type="password" autoComplete="current-password" required maxLength={200}/></label><label>Authenticator code<input name="code" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" required/></label></>}
        <button className="primary" disabled={busy || (!owner && session.stage === 0 && !questions.length)}>{busy ? 'One moment…' : 'Continue →'}</button>
      </form>
    </section>}
    {session?.role && <>
      <div className="toolbar"><span>{session.role === 'OWNER' ? 'Your drafts & shared entries' : 'Shared with you'}</span><button disabled={busy} onClick={() => run(async () => {await api('/auth/logout','POST');setEntries([]);setSession(null);await refresh();})}>Sign out</button></div>
      <div className={session.role === 'OWNER' ? 'workspace' : ''}>
        {session.role === 'OWNER' && <section className="editor"><h2>{editing ? 'Edit a memory' : 'Leave a little something'}</h2><form onSubmit={save}>
          <label>Category<select value={draft.category} onChange={e => setDraft({...draft,category:e.target.value,promise:e.target.value === 'Promises' ? {...emptyPromise} : null})}>{categories.map(c => <option key={c}>{c}</option>)}</select></label>
          <label>Title<input value={draft.title} required maxLength={200} onChange={e => setDraft({...draft,title:e.target.value})}/></label>
          <label>Your words<textarea value={draft.body} maxLength={50000} rows={7} onChange={e => setDraft({...draft,body:e.target.value})}/></label>
          <label>When it happened<input type="date" value={draft.occurred_on || ''} onChange={e => setDraft({...draft,occurred_on:e.target.value || null})}/></label>
          {draft.promise && <fieldset><legend>The promise</legend>
            <label>Promise<input required value={draft.promise.promise} onChange={e => updatePromise({promise:e.target.value})}/></label>
            <label>Date made<input type="date" value={draft.promise.date_made || ''} onChange={e => updatePromise({date_made:e.target.value || null})}/></label>
            <label>Status<select value={draft.promise.status} onChange={e => updatePromise({status:e.target.value})}>{['KEPT','BROKEN','PARTIALLY_KEPT','ONGOING','UNCERTAIN'].map(s => <option key={s}>{s}</option>)}</select></label>
            <label>Context<textarea value={draft.promise.context} onChange={e => updatePromise({context:e.target.value})}/></label>
            <label>Notes<textarea value={draft.promise.notes} onChange={e => updatePromise({notes:e.target.value})}/></label>
            <label className="check"><input type="checkbox" checked={draft.promise.still_intended} onChange={e => updatePromise({still_intended:e.target.checked})}/>Still intended</label>
          </fieldset>}
          <label className="check"><input type="checkbox" checked={draft.shared} onChange={e => setDraft({...draft,shared:e.target.checked})}/>Share with reader</label>
          <button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save entry'}</button>
          {editing && <button type="button" onClick={() => {setEditing(null);setDraft({...blank});}}>Cancel edit</button>}
        </form></section>}
        <section aria-label="Archive entries" className="entries">
          {!entries.length && <div className="empty"><h2>A blank page is a beginning.</h2><p>{session.role === 'OWNER' ? 'Your first entry belongs here.' : 'There are no shared entries yet.'}</p></div>}
          {entries.map(entry => <article key={entry.id}><div className="entry-meta">{entry.category} · {entry.shared ? 'Shared' : 'Private draft'}</div><h2>{entry.title}</h2><p className="body">{entry.body}</p>{entry.occurred_on && <small>{entry.occurred_on}</small>}
            {entry.promise && <aside><strong>{entry.promise.status.replaceAll('_',' ')}</strong><p>{entry.promise.promise}</p><p>{entry.promise.context}</p><p>{entry.promise.notes}</p><small>{entry.promise.still_intended ? 'Still intended' : 'No longer intended'}{entry.promise.date_made ? ` · ${entry.promise.date_made}` : ''}</small></aside>}
            {session.role === 'OWNER' && <button onClick={() => {setEditing(entry.id);setDraft({...entry});setNotice('');}}>Edit entry</button>}
          </article>)}
        </section>
      </div>
    </>}
    <footer>Kept with care. One entry at a time.</footer>
  </main>;
}
