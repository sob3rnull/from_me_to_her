import Link from 'next/link';
import { NOTES, formatDate } from '../lib/notes';
import DreamSheet from './DreamSheet';

export default function Home() {
  return <>
    <section className="hero">
      <div className="hero-copy">
        <h1>
          <span className="line l1">Some things</span>{' '}
          <span className="line l2">need a place</span>{' '}
          <span className="line l3">to exist.</span>
        </h1>
        <p className="lede">
          Thoughts that took the long way home. A few strange dreams.
          And a website that is still figuring itself out.
        </p>
      </div>
      <DreamSheet />
    </section>

    <section className="recent">
      <h2>Recent notes</h2>
      <ul className="entries">
        {NOTES.slice(0, 3).map(note => <li key={note.slug}>
          <time dateTime={note.date}>{formatDate(note.date)}</time>
          <Link href={`/notes/${note.slug}/`}>{note.title}</Link>
          <p>{note.summary}</p>
        </li>)}
      </ul>
      <p className="more"><Link href="/notes/">All notes</Link></p>
    </section>
  </>;
}
