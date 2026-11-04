import Notebook from '../components/Notebook';
import { DREAMS, FRAGMENTS, NOTES, UNFINISHED } from '../lib/writing';

export default function Home() {
  const content = {
    notes: NOTES.map(({ slug, title, body }) => ({ slug, title, body })),
    dreams: DREAMS,
    fragments: FRAGMENTS,
    unfinished: UNFINISHED,
  };
  return <Notebook content={content} />;
}
