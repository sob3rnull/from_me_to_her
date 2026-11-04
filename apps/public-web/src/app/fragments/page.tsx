import type { Metadata } from 'next';
import { FRAGMENTS } from '../../lib/writing';

export const metadata: Metadata = { title: 'Fragments' };

export default function Page() {
  return <section className="page">
    <h1>Fragments</h1>
    <p className="lede">Small pieces that did not need to be anything more.</p>
    <ul className="entries">
      {FRAGMENTS.map(piece => <li key={piece.title}>
        <h2 className="piece-title">{piece.title}</h2>
        <p>{piece.text}</p>
      </li>)}
    </ul>
  </section>;
}
