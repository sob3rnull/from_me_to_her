import type { Metadata } from 'next';
import { DREAMS } from '../../lib/writing';
import DreamSheet from '../DreamSheet';

export const metadata: Metadata = { title: 'Dreams' };

export default function Dreams() {
  return <section className="page">
    <h1>Dreams</h1>
    <p className="lede">The ones that stayed after I woke up. Ask the sheet for another, or read them all.</p>
    <div className="dreams-grid">
      <DreamSheet dreams={DREAMS.map(dream => dream.text)} />
      <div>
        <h2>All of them</h2>
        <ul className="entries">
          {DREAMS.map(dream => <li key={dream.title}>
            <h3 className="piece-title">{dream.title}</h3>
            <p>{dream.text}</p>
          </li>)}
        </ul>
      </div>
    </div>
  </section>;
}
