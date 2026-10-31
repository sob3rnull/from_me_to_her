'use client';

import { useEffect, useRef, useState } from 'react';

// Fictional, generic fragments only. Nothing here is personal.
const SCENES = [
  'I was carrying a staircase across a train station',
  'I was teaching a lighthouse to whistle',
  'I was mailing a small thunderstorm',
  'I was returning a borrowed moon to the library',
  'I was following a bicycle that knew the way home',
  'I was folding the sea into a suitcase',
  'I was watering a clock on the windowsill',
  'I was selling umbrellas to a very polite cloud',
  'I was translating a lullaby for the night bus',
  'I was painting a door onto the side of a hill',
];

const TWISTS = [
  'the ticket collector only accepted apologies',
  'nobody would tell me the postage',
  'every door opened onto the same afternoon',
  'the map kept changing its mind',
  'it turned out the rain was on my side',
  'the whole street was quietly translating itself',
  'I woke up holding the receipt',
  'someone had already signed for it',
  'the clocks agreed to wait',
  'the last page was blank on purpose',
];

const compose = (scene: number, twist: number) => `${SCENES[scene]}, but ${TWISTS[twist]}.`;
const FIRST = compose(0, 0);

function reducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export default function DreamSheet() {
  const [dream, setDream] = useState(FIRST);
  const [typed, setTyped] = useState(FIRST);
  const [typing, setTyping] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);

  function dreamAgain() {
    let next = dream;
    while (next === dream) {
      next = compose(Math.floor(Math.random() * SCENES.length), Math.floor(Math.random() * TWISTS.length));
    }
    if (timer.current) clearInterval(timer.current);
    setDream(next);
    if (reducedMotion()) {
      setTyped(next);
      setTyping(false);
      return;
    }
    let count = 0;
    setTyped('');
    setTyping(true);
    timer.current = setInterval(() => {
      count += 1;
      setTyped(next.slice(0, count));
      if (count >= next.length) {
        if (timer.current) clearInterval(timer.current);
        setTyping(false);
      }
    }, 34);
  }

  return (
    <figure className="sheet">
      <figcaption>Last night, apparently</figcaption>
      <p className="typed" aria-hidden="true">
        {typed}<span className={typing ? 'caret typing' : 'caret'} />
      </p>
      <p className="sr-only" aria-live="polite">{dream}</p>
      <button type="button" className="again" onClick={dreamAgain}>Dream again</button>
    </figure>
  );
}
