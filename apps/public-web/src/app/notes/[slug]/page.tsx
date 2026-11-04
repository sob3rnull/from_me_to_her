import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { NOTES, bySlug, formatDate } from '../../../lib/notes';

export const dynamicParams = false;
export const generateStaticParams = () => NOTES.map(note => ({ slug: note.slug }));

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const note = bySlug((await params).slug);
  return { title: note?.title, description: note?.summary };
}

export default async function NotePage({ params }: { params: Promise<{ slug: string }> }) {
  const note = bySlug((await params).slug);
  if (!note) notFound();
  const index = NOTES.indexOf(note);
  const newer = NOTES[index - 1];
  const older = NOTES[index + 1];
  return <article className="page note-page">
    <p className="crumb"><Link href="/notes/">Notes</Link></p>
    <h1>{note.title}</h1>
    <time dateTime={note.date}>{formatDate(note.date)}</time>
    <div className="prose">{note.body.map((paragraph, i) => <p key={i}>{paragraph}</p>)}</div>
    <nav className="pager" aria-label="More notes">
      {older ? <Link href={`/notes/${older.slug}/`} rel="prev">Older: {older.title}</Link> : <span />}
      {newer ? <Link href={`/notes/${newer.slug}/`} rel="next">Newer: {newer.title}</Link> : <span />}
    </nav>
  </article>;
}
