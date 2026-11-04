import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'Now' };

export default function Now() {
  return <section className="page">
    <h1>Now</h1>
    <p className="lede">What I am up to at the moment. Updated 4 November 2026.</p>
    <dl className="facts">
      <dt>Reading</dt><dd>A paperback with a cracked spine and a very patient narrator.</dd>
      <dt>Making</dt><dd>This website, one small page at a time.</dd>
      <dt>Listening</dt><dd>Rain on the window, mostly. Sometimes a radio in another room.</dd>
      <dt>Eating</dt><dd>More soup than strictly necessary.</dd>
      <dt>Wondering</dt><dd>Whether the porch light counts as a hobby.</dd>
    </dl>
  </section>;
}
