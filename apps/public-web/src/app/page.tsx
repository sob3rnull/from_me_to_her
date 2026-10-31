import DreamSheet from './DreamSheet';
import ThemeToggle from './ThemeToggle';

export default function Home() {
  return <>
    <div className="stripe" aria-hidden="true" />
    <main>
    <header className="top">
      <span className="mark">from me, to her</span>
      <ThemeToggle />
    </header>

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
        <a className="door" href={process.env.NEXT_PUBLIC_VAULT_URL || 'http://localhost:3001'}>
          <span className="frame" aria-hidden="true"><span className="leaf" /></span>
          <span>Find the little door</span>
        </a>
      </div>
      <DreamSheet />
    </section>

    <section className="note">
      <h2>What lives here</h2>
      <p>
        Everything on this page is public. Anything more private is kept behind
        a door that opens for one person.
      </p>
    </section>

    <footer>Public words here. Private memories elsewhere.</footer>
    </main>
  </>;
}
