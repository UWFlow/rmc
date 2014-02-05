# Contributing

## Pull requests

We follow the [GitHub Workflow](http://guides.github.com/overviews/flow/).
Here's a brief summary:

1. Create a topic branch.
1. Push code to that branch.
1. Submit a pull request and get it reviewed.
1. When a reviewer comments with "LGTM" (Looks Good To Me), you can merge if
   you have merge permissions.

If your pull request changes UI, please include screenshots. This makes it easy
for reviewers to provide copy, styling, and interaction feedback.

## Style

General style guidelines:

- 4-space indent in Python; 2-space indents everywhere else
- No trailing whitespace
- 80-character line limit
- Double-indent continuation lines
- Avoid checking in commented-out code (exceptions allowed where reasonable —
  for example, if a line is meant to be un-commented shortly after).
- Non-trivial functions should have explanatory docstrings/JSDoc.
- Try to avoid huge functions. If possible, break them up into reusable,
  logical helper functions that do one thing each.

For the most part, you can just stick to the conventions of the surrounding
code.

[See our style guide for language-specific
guidelines.](https://github.com/divad12/rmc/wiki/Flow-Style-Guide)

## Mock-ups

For any major additions/changes to the UI, please draw some quick mock-ups on
paper first. And by draw, I mean scrawl, scratch, barf graphite onto paper,
whatever you want. They should be chicken scratches. (Bonus marks if you can
actually train a chicken to scratch out your mock-up.) Mock-ups are purely
meant to define interaction and layout -- not visual styling/design.

The ideas is to be able to very quickly iterate on UI concepts, before it gets
much more difficult to change once committed to code. It's also just easier
psychologically for a reviewer to suggest big changes on a 5-minute chicken
scratch than on beautiful shiny working code.

Another advantage of starting with low-fidelity mock-ups is that it focuses
time and attention on trying and thinking of different layouts and
interactions, instead of refining one and being stuck at a local maximum.

A pencil-and-paper mock-up also makes it easy to communicate to other team
members what it is that you're building, concretely (heh).

You can paste your chicken scratches into HipChat for discussion.

[Here's some examples.](http://david-hu.com/2013/09/25/start-with-mockups.html)
