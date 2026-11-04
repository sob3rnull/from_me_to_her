import type { Metadata } from 'next';
import DreamSheet from '../DreamSheet';

export const metadata: Metadata = { title: 'Dreams' };

const DRAWER = [
  { date: '2026-10-03', text: 'A bakery where every loaf was a different postcode. I bought a small one and it was raining inside.' },
  { date: '2026-09-21', text: 'Walking a very long corridor of doors, each labelled with something I forgot to buy.' },
  { date: '2026-09-08', text: 'The library had moved to a boat. Nobody minded. The librarian stamped my hand with a tide table.' },
  { date: '2026-08-30', text: 'A staircase that only went up if you apologised to it first.' },
];

export default function Dreams() {
  return <section className="page">
    <h1>Dreams</h1>
    <p className="lede">I write them down before breakfast gets them. Ask the sheet for another, or read what is in the drawer.</p>
    <div className="dreams-grid">
      <DreamSheet />
      <div>
        <h2>From the drawer</h2>
        <ul className="entries">
          {DRAWER.map(dream => <li key={dream.date}>
            <time dateTime={dream.date}>{new Date(dream.date + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'long', timeZone: 'UTC' })}</time>
            <p>{dream.text}</p>
          </li>)}
        </ul>
      </div>
    </div>
  </section>;
}
