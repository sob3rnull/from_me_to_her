import type { Metadata } from 'next';
import { UNFINISHED } from '../../lib/writing';

export const metadata: Metadata = { title: 'Unfinished' };

export default function Page() {
  return <section className="page">
    <h1>Unfinished</h1>
    <p className="lede">Things I started saying and did not finish. That is allowed.</p>
    <ul className="entries">
      {UNFINISHED.map(piece => <li key={piece.title}>
        <h2 className="piece-title">{piece.title}</h2>
        <p>{piece.text}</p>
      </li>)}
    </ul>
  </section>;
}
