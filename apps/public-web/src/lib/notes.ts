// Fictional placeholder writing. Swap in real public notes whenever you like.
export type Note = { slug: string; title: string; date: string; summary: string; body: string[] };

export const NOTES: Note[] = [
  {
    slug: 'a-very-slow-wednesday', title: 'Notes on a very slow Wednesday', date: '2026-10-27',
    summary: 'Nothing happened, and I wrote it all down.',
    body: [
      'The kettle took its time. The bus took more. By noon I had accepted that the day was going to move at the speed of a cat deciding on a chair.',
      'So I wrote down what did happen: a pigeon on a signpost, a stranger humming something I almost knew, a cloud shaped like a mildly disappointed teapot.',
      'It turns out a slow day has plenty in it. You just have to stop hurrying past the furniture.',
    ],
  },
  {
    slug: 'no-comment-box', title: 'Why this website has no comment box', date: '2026-10-20',
    summary: 'Some rooms are better with the door closed and the window open.',
    body: [
      'Every page here is meant to be read, not discussed. There is nothing to sign up for and nothing counting how long you stayed.',
      'If something lands, keep it. If it does not, the back button is right there and I will not take it personally.',
    ],
  },
  {
    slug: 'the-soup-that-fixed-tuesday', title: 'The soup that fixed Tuesday', date: '2026-10-12',
    summary: 'A recipe, mostly, and partly an apology to onions.',
    body: [
      'Start with too many onions and a pan that is slightly too small. Be patient. Patience is the main ingredient and the only one you cannot buy in a bag.',
      'Add whatever is in the fridge that is not yet a science experiment. Season, taste, season again. Eat it standing up at the stove like a person with nothing to prove.',
    ],
  },
  {
    slug: 'unfinished-sentences', title: 'A short field guide to unfinished sentences', date: '2026-10-06',
    summary: 'Where they come from, and why they are worth keeping.',
    body: [
      'There are three kinds: the ones interrupted by a train, the ones that lost their nerve, and the ones that were never going to end because ending them would make them true.',
      'I keep a list. It is longer than my list of finished ones, and a lot more interesting to read on the bus.',
    ],
  },
  {
    slug: 'things-at-the-bus-stop', title: 'Things I almost said at the bus stop', date: '2026-09-29',
    summary: 'Small thoughts that missed the 7:42.',
    body: [
      'Nice weather for it, whatever it is. Did you also feel the whole street lean slightly toward the corner shop? Is this your umbrella, or has it been following me?',
      'In the end I said nothing and the bus arrived anyway. Politeness is just good timing wearing a coat.',
    ],
  },
  {
    slug: 'porch-light', title: 'On leaving the porch light on', date: '2026-09-14',
    summary: 'A small habit and what it is for.',
    body: [
      'The light is not for anyone in particular. It is for the idea that someone might come by, and that the place should look like it expected them.',
      'Most nights nobody does. The light stays on anyway. I have decided that is the whole point.',
    ],
  },
];

export const bySlug = (slug: string) => NOTES.find(note => note.slug === slug);

export const formatDate = (iso: string) =>
  new Date(iso + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
