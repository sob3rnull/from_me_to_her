import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { NOTES, bySlug } from '../../../lib/writing';

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
  const previous = NOTES[index - 1];
  const next = NOTES[index + 1];
  return <article className="page note-page">
    <p className="crumb"><Link href="/notes/">Notes</Link></p>
    <h1>{note.title}</h1>
    <div className="prose"><p>{note.body}</p></div>
    <nav className="pager" aria-label="More notes">
      {previous ? <Link href={`/notes/${previous.slug}/`} rel="prev">Previous: {previous.title}</Link> : <span />}
      {next ? <Link href={`/notes/${next.slug}/`} rel="next">Next: {next.title}</Link> : <span />}
    </nav>
  </article>;
}
