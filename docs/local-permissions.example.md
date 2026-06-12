# Local Permissions Example

Copy this file to `_local/local-permissions.md` to store the operator identity and any
standing permissions for Amazon work. The real file lives under `_local/`, which is ignored
by Git, so the operator's name and standing approvals stay local and are never committed.

`_local/local-permissions.md` is the single source of truth for the operator's name. Skills and
docs in this repo refer to "the operator" and read the actual identity from this file at runtime;
they must not hardcode a real name.

## What to store

- The operator full name / sender identity used when Amazon asks for a sender name or when
  signing a Seller Support message (e.g. case follow-ups and appeals).
- Standing permissions: each one should name the allowed action, the account/client/marketplace
  scope it applies to, and any limits (e.g. message type, date range).

Example:

```text
## Operator Identity

- Full name: <Your Full Name>
- Short signature: Best, <First Name>
- Formal signature: Best regards, <Your Full Name>

## Standing Permissions

- Date saved: YYYY-MM-DD
- Scope: <account / client / marketplace and the specific workflow>
- Instruction: <the exact action that is pre-approved within that scope>
- Limits: <any caps, message types, or date ranges>
```

## Rules

- Do not commit `_local/local-permissions.md`. It is ignored by Git on purpose.
- Never store passwords, passkeys, OTP/MFA codes, cookies, session/token data, payment details,
  tax details, bank details, or private keys in this file.
- A standing permission only applies when it clearly matches the current action and scope; when
  in doubt, pause and ask the operator before any risky or externally visible action.
- If no operator full name is stored and a sender identity is required, pause and ask the
  operator before sending — do not send the literal placeholder `CURRENT USERNAME`.
