import Link from 'next/link';

export default function NotFound() {
  return <section className="page">
    <h1>Nothing here.</h1>
    <p className="lede">That page does not exist, or it has gone for a walk. <Link href="/">Back to the front page</Link>.</p>
  </section>;
}
