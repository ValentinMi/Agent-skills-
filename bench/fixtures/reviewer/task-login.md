# Task 04 — Login route

- **ID:** 04 · **Depends on:** 03 · **Status:** todo

## Objective
Add a `POST /login` route that authenticates a user by email + password.

## Files
- Modify: `src/routes/auth.ts` — add the `/login` handler

## Contract
```ts
// POST /login  body: { email: string, password: string }
// 200 -> { token: string }   on valid credentials
// 401 -> { error: string }   on unknown email OR wrong password
```

## What to do
- Look the user up by email (existing `findUserByEmail(email)`).
- Compare with `bcrypt.compare(password, user.passwordHash)`.
- On no user OR mismatch, return **401** — never reveal which of the two failed.
- On success, sign a JWT with `signToken(user.id)` and return `{ token }`.
- Reuse the existing `bcrypt` and `signToken` imports; do not add new deps.

## Definition of Done
- [ ] Valid credentials return 200 with a token
- [ ] Unknown email returns 401
- [ ] Wrong password returns 401
- [ ] Verify command passes

## Verify
```bash
npm test -- auth/login
```
