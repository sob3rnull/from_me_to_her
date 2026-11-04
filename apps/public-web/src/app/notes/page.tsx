import type { Metadata } from 'next';
import Link from 'next/link';
import { NOTES, formatDate } from '../../lib/notes';

export const metadata: Metadata = { title: 'Notes' };

export default function Notes() {
  return <section className="page">
    <h1>Notes</h1>
    <p className="lede">Short things, written when they were true.</p>
    <ul className="entries">
      {NOTES.map(note => <li key={note.slug}>
        <time dateTime={note.date}>{formatDate(note.date)}</time>
        <Link href={`/notes/${note.slug}/`}>{note.title}</Link>
        <p>{note.summary}</p>
      </li>)}
    </ul>
  </section>;
}
