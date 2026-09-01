# Security — theory

> What secure-by-default Android IS and why. The OWASP/NIST-anchored standard of QUALITY-BAR §4.
> How, per stack: `../lib/android/reference/security-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §4, §7.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

Security on mobile is **defense in depth at every trust boundary** (QUALITY-BAR §4): the app runs on a device the user may not fully control, talks to a server over an untrusted network, and holds tokens whose compromise is an account compromise. This layer is anchored to [OWASP ASVS 5.0 Level 2](https://owasp.org/www-project-application-security-verification-standard/) and the [OWASP Top 10:2025](https://owasp.org/Top10/), with a zero-high-findings bar.

## Threat Model <!-- 3 -->
Organic from the app's **actual exposure surface** — installed in unknown hands, on unrooted and rooted devices, over hostile Wi-Fi, beside competing apps. [OWASP's mobile guide](https://owasp.org/www-project-mobile-security-testing-guide/) names the platform-specific risks a generic web threat model misses: local data at rest, inter-app IPC, snapshot and backup leakage, reverse engineering. Each control below exists because one of these is real.

## Deny-By-Default <!-- 3 -->
**Start closed, open narrowly** (QUALITY-BAR §4): nothing is reachable, exported, or authorized unless an explicit gate lets it be. Authorization is enforced on every protected destination — a nav guard driven by auth state — not "known to be behind a logged-in screen". Default-deny also governs components (`android:exported=false`), file creation (private), and data sharing (explicit) ([MASVS](https://mobile-security.gitbook.io/mobile-app-security-testing-guide/)).

## Secure Token Storage <!-- 3 -->
Tokens live in **Keystore-backed secure storage**, never plain Preferences, never unencrypted files, never readable by other apps (QUALITY-BAR §4): the OS Keystore + encrypted prefs hold the access and refresh tokens, with keys scoped to the app. The device's storage must be assumed readable by an attacker with physical access; encryption-at-rest under the Keystore is the control.

## Token Lifecycle <!-- 3 -->
Tokens are **short-lived and rotating** (QUALITY-BAR §4, NIST): the access token lives minutes; the refresh token persists and rotates on use. A breached access token is useful for minutes, not weeks; a rotating refresh token invalidates its predecessor, so a stolen one is a one-time asset. Logout **revokes server-side and clears all stored credentials** — local deletion alone leaves a ghost account.

## Bearer Attachment <!-- 3 -->
Authenticated requests attach the token **mechanically, through one interceptor** at the transport edge (QUALITY-BAR §4): the header comes from secure storage in a single place, so no caller can forget or hand-roll auth and no token is copied around the app. The interceptor is also the single place to react to 401 and coordinate refresh. One attachment point = one thing to audit.

## Single-Flight Refresh <!-- 3 -->
The **thundering-herd control**: when several in-flight requests hit 401, exactly **one** refresh starts and the rest await its result (QUALITY-BAR §4) — the "everything expired at once" race. Refresh is atomic: failure revokes the session (logout + clear) and is never retried in a loop; concurrent refreshes are serialized. A 401 storm spamming the token endpoint is how an app rate-limits itself into lockout.

## Authorization Is Local Too <!-- 3 -->
**Every protected surface re-checks, even with a valid token** (QUALITY-BAR §4): valid authentication does not imply authorization — the server rejects unauthorized calls regardless (client-enforced deny is theater), and the app's own UI hides or short-circuits what the user isn't entitled to. Roles/permissions are derived in the domain/auth layer (QUALITY-BAR §1) and drive both nav-gating and real server checks: server authoritative, app helpful.

## Secrets Management <!-- 3 -->
**No secrets in code, `BuildConfig`, or the repo** (QUALITY-BAR §4): API keys, signing keys, and tokens are injected at build/run from secure sources (CI secrets, env, or a secure backend), the repo carrying only `.example` placeholders. Secret-bearing scope is minimized and rotated, and signing keystores come from CI secrets. A secret committed to git history is compromised on the day it's pushed.

## Network Security <!-- 3 -->
**Transport is TLS everywhere, with cleartext blocked** (QUALITY-BAR §4): no plain HTTP for app traffic — the default network-security config forbids cleartext, and private endpoints additionally pin or restrict trust via network-security config. Certificates are validated (missing hostname/chain checks are fatal); debug-only endpoints are strictly separated from production. An `http://` request in a production path is a critical finding by definition.

## Validation & Injection <!-- 3 -->
Every external input is **validated before use** (QUALITY-BAR §4): typed contract-layer DTOs, parameterized queries, escaped dynamic content. This is at the top of the Top 10 for a reason — enforcing value objects and edge validation (api-theory) closes the injection family at the type system, not by review. Never interpolate untrusted strings into SQL, URLs, or markup.

## Logging Hygiene <!-- 3 -->
**Secrets and personal data never reach logs** (QUALITY-BAR §4, ASVS): no tokens, passwords, or PII in crash reports or logcat — tokens and at-rest keys are the first candidates to redact. Sensitive events (auth success/failure, refresh, logout) are logged *without credentials*. An accidental `Log.d("token", "$token")` in a hot path is an account-takeover ticket in analytics.

## Least Privilege <!-- 3 -->
The app declares **only the permissions it exercises** and handles denial gracefully (QUALITY-BAR §4): permission requests are contextual and minimal, data access is scoped per purpose, and a runtime-denied permission degrades the feature, not the app. A manifest full of unused permissions is a free attack surface nobody inspected.

## Screen-Safety & Data Hygiene <!-- 3 -->
User-facing data is protected **on and off screen** ([MASVS storage section](https://mobile-security.gitbook.io/mobile-app-security-testing-guide/)): flags keep secure content out of recents and screenshots; clipboard and screen-capture guards protect credential fields; sessions auto-lock on timeout; cache and crash dumps are scrubbed of sensitive payloads. An exported backup or readable cache dir is a data-exfiltration channel wearing a shrug.

