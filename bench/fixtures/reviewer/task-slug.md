# Task 02 — Slugify helper

- **ID:** 02 · **Depends on:** none · **Status:** todo

## Objective
Add a pure `slugify` helper used to build URL slugs from titles.

## Files
- Create: `src/utils/slug.ts` — the helper only

## Contract
```ts
export function slugify(input: string): string;
// lowercased; spaces and non-alphanumerics collapsed to single "-";
// leading/trailing "-" trimmed. slugify("Hello, World!") === "hello-world"
```

## What to do
- Lowercase, replace runs of non-alphanumeric chars with a single `-`, trim edges.
- Keep it a pure function. Do NOT touch routing, config, or any other file.

## Definition of Done
- [ ] `slugify("Hello, World!")` returns `"hello-world"`
- [ ] Exported as a named export `slugify`
- [ ] Verify command passes

## Verify
```bash
npm test -- utils/slug
```
