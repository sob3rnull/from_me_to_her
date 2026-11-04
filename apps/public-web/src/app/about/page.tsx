import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'About' };

export default function About() {
  return <section className="page">
    <h1>About</h1>
    <div className="prose">
      <p>
        This is a small personal website. It collects short notes, odd dreams, and whatever else
        wanted somewhere to live. It started on a whim and has not been talked out of it.
      </p>
      <p>
        There is no sign-up, no tracking, and no comment box. Everything on these pages is public
        and meant to be read.
      </p>
      <h2>Colophon</h2>
      <p>
        Set in Newsreader, with Special Elite for the typewriter. Built as a static site, so it
        loads fast and keeps very few secrets. Light and dark follow your system unless you flick the lamp.
      </p>
    </div>
  </section>;
}
