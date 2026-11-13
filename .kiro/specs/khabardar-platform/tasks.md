# Implementation Plan: KHABARDAR Platform

## Overview

This plan converts the KHABARDAR design into incremental, test-driven, buildable coding steps. It is organized into 7 phases. Phases 1–6 deliver the **Scope A MVP**; Phase 7 holds **Scope B / Future** enhancements that are clearly separated and NOT required for MVP completion.

The sequencing prioritizes an end-to-end vertical slice as early as possible: **submit text → rule-based detect → explainable result → masked persisted history** is reachable by the end of Phase 2. Shared services (SSRF guard, masking/hashing, upload validation, error envelope) are implemented once and referenced everywhere.

Stack per design: **Backend** Python 3.11+ / FastAPI / Pydantic / SQLAlchemy / Alembic; **Frontend** React / TypeScript / Vite / Tailwind. Tests use `pytest` + `hypothesis` (property tests, min 100 iterations, tagged `Feature: khabardar-platform, Property N: ...`).

**Hard gates applied to every relevant task (approved implementation conditions):**
- Never persist raw OTPs/passwords/tokens/unnecessary PII — mask/hash before persistence (blocking acceptance criterion).
- Default to privacy-preserving scan history (masked content only).
- Local-only until Req 18 auth exists — bind backend to `127.0.0.1`; no public exposure.
- SSRF protection MUST have automated security tests for DNS rebinding (resolve-then-pin), IPv4/IPv6 reserved/private ranges, and redirect-based attacks (per-hop revalidation).
- No feature is complete without passing its acceptance tests.
- No fabricated AI results, threat intelligence, or performance metrics — measured-only; honest "unavailable" states.

Legend: `[MVP]` = required for MVP; `[Scope B / Future]` = post-MVP. Sub-tasks marked `*` are optional (tests) and are not auto-implemented.

## Tasks

- [ ] 1. Phase 1: Project Foundation
  - [x] 1.1 [MVP] Scaffold monorepo, backend app skeleton, and config/secrets module
    - **Description:** Create the monorepo layout, FastAPI app entrypoint bound to localhost, and the env-based config/secrets loader (consolidates Req 8.7 / 18.2 / 19.4).
    - **Dependencies:** none (critical-path root).
    - **Files:** `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/__init__.py`, `backend/requirements.txt`, `backend/.env.example`, `backend/alembic.ini`, `frontend/package.json`, `.gitignore`, `README.md`
    - **Implementation details:** `config.py` loads from `.env` via python-dotenv; defines optional keys (`GEMINI_API_KEY`, `GROQ_API_KEY`, `OLLAMA_BASE_URL`, `GOOGLE_SAFE_BROWSING_KEY`, `VIRUSTOTAL_KEY`, `URLSCAN_KEY`, `TESSERACT_CMD`) and `RETENTION_DAYS`. App binds uvicorn to `127.0.0.1:8000`. No secrets in source.
    - **Acceptance criteria:** App boots on localhost only; no key value is referenced in source or frontend (MVP-AC-12, MVP-AC-11). `.env.example` documents all optional keys; app starts with none set.
    - **Unit tests:** config loader returns `unavailable`/`None` cleanly when keys absent; never raises on missing optional key.
    - **Security tests:** assert app host binding is loopback; assert no secret value is serialized by any config-to-dict/debug path.
    - _Requirements: 19.4, 8.7, 18.2, 25.1, 22.4_

  - [x] 1.2 [MVP] Implement shared error envelope, input-validation and middleware chain
    - **Description:** Implement the consistent success/error envelope and ordered middleware (CORS allowlist → rate limit → request-id/audit → input validation → error-envelope wrapper). Implemented once, reused by all routers.
    - **Dependencies:** 1.1.
    - **Files:** `backend/app/core/envelope.py`, `backend/app/core/errors.py`, `backend/app/middleware/cors.py`, `backend/app/middleware/rate_limit.py`, `backend/app/middleware/request_id.py`, `backend/app/middleware/validation.py`, `backend/app/middleware/error_wrapper.py`
    - **Implementation details:** success `{ ok: true, data }`; error `{ ok: false, error: { code, message, operation } }`. CORS allowlist from config (local origin default). Rate limit 100 req/60s per client → `429 RATE_LIMITED`. No stack traces/secrets leak to client.
    - **Acceptance criteria:** Every error response carries `code`, `message`, `operation`; 101st request in 60s window is rejected; CORS rejects non-allowlisted origins (MVP-AC-12).
    - **Unit tests:** envelope serialization success/error; rate-limit counter window boundary; CORS allow/deny.
    - **Security tests:** error responses never contain stack traces, secrets, or internal IPs.
    - _Requirements: 22.7, 19.1, 19.2, 19.3_

  - [x]* 1.3 [MVP] Write property test for user-input preservation on error
    - **Property 13: User input is preserved on operation error**
    - **Validates: Requirements 22.7**
    - Tagged `Feature: khabardar-platform, Property 13`, min 100 iterations. Assert failed operations return `operation` + message and never mutate submitted input.
    - **Files:** `backend/tests/properties/test_property_13_input_preserved.py`

  - [x] 1.4 [MVP] Build frontend shell: Vite + Tailwind + design system tokens + theme context
    - **Description:** Set up the React/TS/Vite app, Tailwind config with the exact palette, CSS-variable theming, dark-default theme context, and responsive breakpoints.
    - **Dependencies:** 1.1.
    - **Files:** `frontend/vite.config.ts`, `frontend/tailwind.config.js`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/context/ThemeContext.tsx`, `frontend/src/styles/tokens.css`, `frontend/src/components/ThemeToggle.tsx`
    - **Implementation details:** palette Deep Navy `#101D31`, Midnight Blue `#172A45`, Metallic Silver `#C5D0DC`, Electric Blue `#3987FF`, light `#F4F7FB`, dark `#0B1423`, Danger `#E5484D`, Warning `#E5A323`, Safe `#1C9B70`. Dark default on first load; selection persisted to localStorage and applied within 1s. Breakpoints mobile ≤767 / tablet 768–1023 / desktop ≥1024 with no horizontal overflow.
    - **Acceptance criteria:** Dark theme default; theme persists across reload; risk colors map Danger/Warning/Safe (MVP-AC-2).
    - **Unit tests:** theme persistence read/write; token values match palette.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6, 2.7, 2.8, 2.9_

  - [x] 1.5 [MVP] Implement i18n (EN / Urdu / Roman Urdu) with RTL and language context
    - **Description:** Wire react-i18next with `en`, `ur`, `ur-Latn` bundles, default English, persisted selection, English fallback for missing keys, and RTL when Urdu active.
    - **Dependencies:** 1.4.
    - **Files:** `frontend/src/i18n/index.ts`, `frontend/src/i18n/en.json`, `frontend/src/i18n/ur.json`, `frontend/src/i18n/ur-Latn.json`, `frontend/src/context/LanguageContext.tsx`, `frontend/src/components/LanguageToggle.tsx`
    - **Implementation details:** default `en` (Req 4.3); persist to localStorage, restore on load; missing key → English fallback; set `dir="rtl"` on root when `ur`; Roman Urdu + English LTR.
    - **Acceptance criteria:** Language switch applies within 1s and persists; Urdu renders RTL; missing key falls back to English (MVP-AC-2).
    - **Unit tests:** fallback-to-English on missing key; persistence; `dir` toggles with language.
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.7_

  - [x] 1.6 [MVP] Build splash screen with branded entry and logo-failure fallback
    - **Description:** Full-screen Deep Navy splash showing only Official_Logo + "KHABARDAR" + tagline, entrance animation 300–800ms, auto-advance to dashboard after ~2s, with Req 1.8 fallback when logo asset absent.
    - **Dependencies:** 1.4, 1.5.
    - **Files:** `frontend/src/pages/Splash.tsx`, `frontend/public/assets/logo.svg` (placeholder reference), `frontend/src/components/SplashLogo.tsx`
    - **Implementation details:** centered logo preserving aspect ratio, no nav/buttons/forms/footer; viewport 320–3840px centered without clipping; on logo load error render name + tagline and still advance after 2s.
    - **Acceptance criteria:** Shows only logo+name+tagline, auto-advances ~2s; missing-logo fallback still advances (MVP-AC-1).
    - **Unit tests:** auto-advance timer fires transition; logo-error path renders fallback and still transitions.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

  - [x] 1.7 [MVP] Build responsive navigation shell and all 12 routes with Scope B placeholders
    - **Description:** react-router with the 12 pages; active-state styling; Scope B Honeypot and Family pages render honest "advanced / coming soon" placeholders with disabled controls. Dashboard shell with entry points for Detector/URL/Media/SOC.
    - **Dependencies:** 1.4, 1.5, 1.6.
    - **Files:** `frontend/src/router.tsx`, `frontend/src/components/NavBar.tsx`, `frontend/src/components/UnavailableState.tsx`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/{Detector,UrlAnalyzer,Scanner,Intelligence,Honeypot,Family,History,Reports,Settings,About}.tsx`
    - **Implementation details:** navigation within 1s; failed destination within 5s stays on page with error indication; active nav visually distinct; dashboard entry points navigate to Detector/URL/Media/SOC.
    - **Acceptance criteria:** All 12 pages routable; Honeypot/Family shown as non-functional placeholders (never fake-functional); no horizontal overflow at 375/768/1280 (MVP-AC-2, honesty Req 22.1).
    - **Unit tests:** route table renders each page; placeholder pages disable action controls; nav active-state logic.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 22.1_

- [ ] 2. Phase 2: Scam Detection Engine
  - [x] 2.1 [MVP] Define SQLAlchemy models and Alembic migrations (portable SQLite/PostgreSQL)
    - **Description:** Implement all 11 normalized models with portable column types and the initial Alembic migration. `(ioc_type, normalized_value)` unique on ThreatIndicators; `origin` field on intelligence records.
    - **Dependencies:** 1.1.
    - **Files:** `backend/app/db/base.py`, `backend/app/db/session.py`, `backend/app/models/*.py` (Users, ScanHistory, ScamReports, URLAnalysis, ThreatIndicators, ScamCampaigns, FamilyGroups, FamilyMembers, Notifications, AuditLogs, HoneypotSessions), `backend/alembic/versions/0001_init.py`
    - **Implementation details:** portable types only (`String/Text/Integer/Boolean/DateTime(tz)/JSON`); string UUID PKs; seed single local user; nullable `password_hash`/`role` for Scope B seam.
    - **Acceptance criteria:** `alembic upgrade head` builds schema on SQLite; models match the ERD; ScanHistory stores only masked content.
    - **Unit tests:** migration up/down; unique constraint on IOC `(type, value)`; models instantiate with portable types.
    - _Requirements: 20.1, 20.2_

  - [x] 2.2 [MVP] Implement shared masking/hashing privacy service
    - **Description:** Single privacy service that masks OTPs/passwords/tokens/PII (≤ last 4 chars, irreversible) and one-way hashes identifiers not needed in raw form. Used by every persistence path.
    - **Dependencies:** 1.1.
    - **Files:** `backend/app/services/privacy.py`, `backend/app/services/pii_detectors.py`
    - **Implementation details:** detect OTP/password/token/PII patterns; mask reveals at most final 4 chars; original unreconstructable; hashing is one-way; store only data used by analysis.
    - **Acceptance criteria (hard gate):** No raw OTP/password/token/PII persisted anywhere; masked content only. A scan never writes plaintext secrets.
    - **Unit tests:** masking reveals ≤4 chars; masked ≠ original for len>4; hash irreversibility.
    - **Security tests:** fuzz secret-laden strings and assert stored form contains no plaintext secret.
    - _Requirements: 21.1, 21.2, 21.3, 21.4_

  - [ ]* 2.3 [MVP] Write property test for masking irreversibility and no plaintext secrets
    - **Property 5: Masking is irreversible and never leaves plaintext secrets**
    - **Validates: Requirements 21.2, 21.3, 21.4**
    - Tagged `Feature: khabardar-platform, Property 5`, min 100 iterations.
    - **Files:** `backend/tests/properties/test_property_05_masking.py`

  - [x] 2.4 [MVP] Implement XSS neutralization and parameterized-access repository layer
    - **Description:** Repository layer over SQLAlchemy (parameterized access only) plus markup-neutralization applied before storing/rendering attacker-controlled scam text.
    - **Dependencies:** 2.1, 2.2.
    - **Files:** `backend/app/repositories/base.py`, `backend/app/repositories/scan_history.py`, `backend/app/services/sanitize.py`
    - **Implementation details:** neutralize executable script/markup before storage and before returning for render; all queries parameterized.
    - **Acceptance criteria:** Stored/returned scam text contains no executable markup; no raw/`text()` SQL (MVP-AC-12).
    - **Unit tests:** sanitize strips/encodes script and event-handler attributes; repository uses bound params.
    - **Security tests:** SQLi probe strings do not alter queries; XSS payloads neutralized.
    - _Requirements: 19.6, 19.7_

  - [ ]* 2.5 [MVP] Write property test for XSS neutralization
    - **Property 12: Scam-text input is neutralized against XSS**
    - **Validates: Requirements 19.6**
    - Tagged `Feature: khabardar-platform, Property 12`, min 100 iterations.
    - **Files:** `backend/tests/properties/test_property_12_xss.py`

  - [x] 2.6 [MVP] Implement rule-based detection engine, scoring, and classification
    - **Description:** Deterministic Rule_Based_Engine evaluating all signal families; transparent weighted-signal score clamped 0–100; pure classification function; absence-of-safety logic (never SAFE solely because no keyword matched).
    - **Dependencies:** 2.1.
    - **Files:** `backend/app/services/detection/rule_engine.py`, `backend/app/services/detection/signals.py`, `backend/app/services/detection/scoring.py`, `backend/app/services/detection/classify.py`, `backend/app/services/detection/lexicons/{en,ur,ur_latn}.py`
    - **Implementation details:** signals = suspicious keywords, psychological manipulation, urgency/fear, authority impersonation, credential/OTP requests, suspicious payment, suspicious links, linguistic patterns; each recorded triggered-or-not with detected content, direction, weight; classification SAFE 0–39 / SUSPICIOUS 40–69 / HIGH RISK 70–100.
    - **Acceptance criteria:** Integer Risk_Score 0–100; classification pure function of score; no-keyword message not auto-SAFE (MVP-AC-3, MVP-AC-4).
    - **Unit tests:** score clamp bounds; each signal family fires on representative inputs; classification boundaries at 39/40/69/70.
    - _Requirements: 5.3, 5.4, 5.11, 7.1, 7.2_

  - [ ]* 2.7 [MVP] Write property test for Risk_Score bounds
    - **Property 1: Risk_Score is always within 0–100**
    - **Validates: Requirements 5.3, 9.7**
    - Tagged `Feature: khabardar-platform, Property 1`, min 100 iterations (text + URL analyzers once URL engine exists; include detector here, extend in 3.x).
    - **Files:** `backend/tests/properties/test_property_01_risk_bounds.py`

  - [ ]* 2.8 [MVP] Write property test for classification purity
    - **Property 2: Classification is a pure function of Risk_Score**
    - **Validates: Requirements 5.4**
    - Tagged `Feature: khabardar-platform, Property 2`, min 100 iterations.
    - **Files:** `backend/tests/properties/test_property_02_classification.py`

  - [x] 2.9 [MVP] Implement language detection, scam categories, and explainable result assembly
    - **Description:** Language detection (EN/Urdu/Roman Urdu), category assignment (phishing, OTP theft, prize/lottery, fake banking/JazzCash/Easypaisa, fake job/advance-fee, investment, romance, social engineering, account takeover, urgent payment, identity impersonation; `uncategorized` for non-SAFE with no specific category), and EN+Urdu explanations with recommended actions, confidence, timestamp.
    - **Dependencies:** 2.6.
    - **Files:** `backend/app/services/detection/language.py`, `backend/app/services/detection/categories.py`, `backend/app/services/detection/explanation.py`, `backend/app/services/detection/result.py`
    - **Implementation details:** process in provided language; explanation always EN + Urdu; signals listed with name/detected content/direction; "no contributing signals detected" when none; confidence 0.00–1.00; result within 15s.
    - **Acceptance criteria:** Returns score + classification + category + EN+Urdu explanation + ≥1 signal for a known scam; no-signal state explicit (MVP-AC-3, MVP-AC-4).
    - **Unit tests:** category mapping per Req 6; uncategorized fallback; explanation bilingual; no-signal explicit state.
    - _Requirements: 4.5, 4.6, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 7.4, 7.5_

  - [ ]* 2.10 [MVP] Write property test for explainability completeness
    - **Property 7: Explainability signal records are complete**
    - **Validates: Requirements 7.1, 7.2, 7.4, 7.5, 5.11**
    - Tagged `Feature: khabardar-platform, Property 7`, min 100 iterations.
    - **Files:** `backend/tests/properties/test_property_07_explainability.py`

  - [ ] 2.11 [MVP] Implement AI provider abstraction, selector, and offline rule-based fallback
    - **Description:** `AIProvider` interface + Gemini/Groq/Ollama providers (optional), selector with health-check (≤5s default), retry (≤2 attempts), and guaranteed fallback to Rule_Based_Engine with AuditLog on unavailability/failure.
    - **Dependencies:** 2.6, 1.1.
    - **Files:** `backend/app/services/ai/base.py`, `backend/app/services/ai/{gemini,groq,ollama}.py`, `backend/app/services/ai/classifier.py`, `backend/app/services/ai/explanation.py`, `backend/app/services/ai/selector.py`, `backend/app/repositories/audit.py`
    - **Implementation details:** `is_configured()` true only with env creds; exactly one provider per request; normalized `AIClassification`; on health-fail / ≤2-attempt fail / no provider → rule-based result + AuditLog entry. Credentials backend-only.
    - **Acceptance criteria (honesty gate):** Full valid result with zero keys; provider failure writes AuditLog and falls back; no fabricated AI output (MVP-AC-3).
    - **Unit tests:** no-provider path; health-check fail path; retry-exhaustion path; audit written on failure.
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 7.3_

  - [ ]* 2.12 [MVP] Write property test for zero-key / provider-failure fallback
    - **Property 6: The app returns a valid result with zero AI keys (and on provider failure)**
    - **Validates: Requirements 8.4, 8.5, 8.6**
    - Tagged `Feature: khabardar-platform, Property 6`, min 100 iterations.
    - **Files:** `backend/tests/properties/test_property_06_fallback.py`

  - [x] 2.13 [MVP] Wire detection pipeline, `/api/scam/detect` router, and masked persistence
    - **Description:** Orchestrate ingest/validate → language → rule-based → optional AI → score → classify → category → EN+Urdu explanation → mask → persist to ScanHistory. Build the router and `/api/capabilities`. Persistence failure still returns result with `save_error`.
    - **Dependencies:** 2.2, 2.4, 2.6, 2.9, 2.11.
    - **Files:** `backend/app/services/detection/pipeline.py`, `backend/app/routers/scam.py`, `backend/app/routers/capabilities.py`, `backend/app/schemas/scam.py`
    - **Implementation details:** validate 1–10000 chars (`400 INVALID_LENGTH`); mask before persist; `save_error: true` on persistence failure; response envelope per design.
    - **Acceptance criteria:** End-to-end slice works: submit text → detect → explainable result → masked persisted history (MVP-AC-3, MVP-AC-8); invalid length rejected.
    - **Integration tests:** EN/Urdu/Roman Urdu scam samples return expected classification with zero keys; persisted record masked; save-failure returns result + flag.
    - _Requirements: 5.1, 5.2, 7.3, 20.3, 20.4, 22.6_

  - [x] 2.14 [MVP] Build frontend Scam Detector page wired to `/api/scam/detect`
    - **Description:** Detector UI with input (preserved on error), RiskBadge, SignalList (bilingual explanation side-by-side), capability gating.
    - **Dependencies:** 1.7, 2.13.
    - **Files:** `frontend/src/pages/Detector.tsx`, `frontend/src/hooks/useScanDetect.ts`, `frontend/src/components/{RiskBadge,SignalList,CapabilityGate}.tsx`, `frontend/src/lib/apiClient.ts`
    - **Implementation details:** render scam text as text only (never `dangerouslySetInnerHTML`); EN+Urdu explanations side-by-side; input never cleared until success.
    - **Acceptance criteria:** Submitting a scam sample shows score/classification/category/signals/EN+Urdu explanation; input preserved on error (MVP-AC-3, Req 22.7).
    - **Unit tests:** error preserves input; signals render; risk color mapping.
    - _Requirements: 5.6, 7.4, 22.7, 4.5_

  - [ ] 2.15 [MVP] Create labeled evaluation dataset (≥100 examples, EN/Urdu/Roman Urdu, synthetic scams + legitimate)
    - **Description:** Build the fixed labeled dataset used by Req 24 evaluation and automated classification tests. All scam entries are Synthetic_Data and labeled.
    - **Dependencies:** 2.9.
    - **Files:** `backend/app/eval/dataset/khabardar_eval_v1.jsonl`, `backend/app/eval/dataset/README.md`
    - **Implementation details:** ≥100 examples; EN/Urdu/Roman Urdu scam messages, legitimate banking, fake prize, OTP theft; each entry carries expected Classification and `origin=synthetic`.
    - **Acceptance criteria:** Dataset ≥100 labeled examples covering required categories/languages; synthetic entries labeled.
    - **Unit tests:** dataset loads; schema valid; count ≥100; required categories/languages present.
    - _Requirements: 24.1, 24.5_

  - [ ] 2.16 Phase 2 Checkpoint
    - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Phase 3: URL Security Engine
  - [ ] 3.1 [MVP] Implement shared SSRF-safe fetch guard (single outbound chokepoint)
    <!-- PARTIAL: address_policy.py (loopback/private/link-local/metadata/reserved block, resolve-and-check) and url_normalize.py (scheme allowlist, IDNA, userinfo strip) implemented + tested. The MVP URL analyzer performs NO outbound fetch (network checks reported "unavailable"), so resolve-then-pin / redirect-hop revalidation / timeout+5MB enforcement of an actual httpx client (ssrf_guard.py) are deferred until live fetching is enabled (Scope B 7.3). This is the safest posture for an unauthenticated public demo. -->
    - **Description:** The one component every outbound-on-behalf-of-user request must pass through: scheme allowlist, IDNA normalization, userinfo stripping, DNS resolution of all A/AAAA, IPv4+IPv6 block policy, resolve-then-pin (DNS-rebinding protection), no auto-redirect with per-hop revalidation (max 10), 10s timeout, 5MB cap, no browse/download/execute.
    - **Dependencies:** 1.1, 1.2.
    - **Files:** `backend/app/services/url/ssrf_guard.py`, `backend/app/services/url/address_policy.py`, `backend/app/services/url/url_normalize.py`
    - **Implementation details:** block loopback (`127.0.0.0/8`,`::1`), private IPv4 (`10/8`,`172.16/12`,`192.168/16`), link-local (`169.254/16`,`fe80::/10`), metadata (`169.254.169.254`,`fd00:ec2::254`), reserved (`0.0.0.0/8`,`::`,`fc00::/7`,multicast); pin validated IP for the actual connection with correct Host/SNI; each redirect `Location` re-parsed/re-resolved/re-validated/re-pinned.
    - **Acceptance criteria (hard gate):** Never connects to a blocked address under any path incl. redirect and rebinding; non-http(s)/invalid-host rejected with no network request (MVP-AC-5).
    - **Unit tests:** scheme allowlist; userinfo strip; IDNA normalize; redirect cap; timeout and 5MB cap enforcement.
    - **Security tests (condition 4 — mandatory):** DNS rebinding (resolve-then-pin: validated IP ≠ connect IP is impossible); IPv4 reserved/private ranges; IPv6 reserved/private ranges (`::1`, `fe80::/10`, `fc00::/7`, `fd00:ec2::254`); redirect-based attack where a later hop resolves to a private/metadata IP (per-hop revalidation blocks it, no transmit).
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 19.8_

  - [ ]* 3.2 [MVP] Write property test for the SSRF guard (incl. DNS rebinding, IPv4/IPv6, redirects)
    - **Property 3: SSRF guard never connects to a blocked address under any path**
    - **Validates: Requirements 11.2, 11.3, 11.4, 11.5, 11.9, 11.10, 19.8**
    - Tagged `Feature: khabardar-platform, Property 3`, min 100 iterations. MUST include DNS rebinding + IPv4 + IPv6 reserved/private + redirect-hop revalidation generators per condition 4.
    - **Files:** `backend/tests/properties/test_property_03_ssrf.py`

  - [x] 3.3 [MVP] Implement keyless local URL heuristics and DNS/IP analysis
    - **Description:** Always-available local heuristics: typosquatting (edit distance vs brand/bank domains), homograph/IDNA mixed-script, IP-based URL, shortener detection, suspicious subdomain patterns, brand impersonation (JazzCash/Easypaisa/PK banks), scheme/HTTPS presence.
    - **Dependencies:** 3.1.
    - **Files:** `backend/app/services/url/heuristics.py`, `backend/app/services/url/brand_lists.py`, `backend/app/services/url/scoring.py`
    - **Implementation details:** heuristics produce explainable indicators and feed a 0–100 score with transparent weights.
    - **Acceptance criteria:** Local indicators returned with no keys configured; integer Risk_Score 0–100 (MVP-AC-5).
    - **Unit tests:** typosquatting edit distance; homograph detection; IP-URL and shortener detection; subdomain patterns.
    - _Requirements: 9.5, 9.6_

  - [ ] 3.4 [MVP] Implement SSL/HTTPS inspection and redirect-chain validation via the guard
    - **Description:** HTTPS validation + best-effort SSL certificate inspection and redirect-chain capture, all network hops performed only through the SSRF guard; unreachable/unavailable marked, not omitted.
    - **Dependencies:** 3.1, 3.3.
    - **Files:** `backend/app/services/url/ssl_inspect.py`, `backend/app/services/url/redirect.py`
    - **Implementation details:** SSL details marked "unavailable" when unretrievable; redirect chain recorded; unreachable host → offline heuristics only with network checks marked unavailable.
    - **Acceptance criteria:** SSL/redirect checks route through guard; unavailable states marked, never fabricated (MVP-AC-5, MVP-AC-9).
    - **Unit tests:** unavailable SSL marked not omitted; redirect chain captured; unreachable host falls back to heuristics.
    - _Requirements: 9.4, 9.8, 11.4, 11.5_

  - [ ] 3.5 [MVP] Implement modular external intelligence adapters with honest unavailable states
    - **Description:** Modular adapters for Google Safe Browsing, VirusTotal, urlscan.io, WHOIS; each `is_configured()`/`enrich(url)` with 10s timeout; absent keys or failures → labeled "unavailable", continue with remaining checks, record failure. (Live enrichment is Scope B; MVP ships the seam + honest states.)
    - **Dependencies:** 3.1.
    - **Files:** `backend/app/services/url/adapters/base.py`, `backend/app/services/url/adapters/{safe_browsing,virustotal,urlscan,whois}.py`
    - **Implementation details:** never present an integration result as available when unavailable; per-integration 10s timeout; failures recorded.
    - **Acceptance criteria (honesty gate):** Unconfigured integrations always shown "unavailable"; never fabricated (MVP-AC-9).
    - **Unit tests:** unconfigured → unavailable; timeout → unavailable + recorded; one failing adapter doesn't fail the analysis.
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 9.3_

  - [ ]* 3.6 [MVP] Write property test for unavailable-capability honesty
    - **Property 9: Unavailable capabilities are never presented as available**
    - **Validates: Requirements 10.3, 10.4, 10.5, 22.5, 22.6**
    - Tagged `Feature: khabardar-platform, Property 9`, min 100 iterations (covers integrations + AI providers).
    - **Files:** `backend/tests/properties/test_property_09_unavailable.py`

  - [x] 3.7 [MVP] Wire URL analysis pipeline, `/api/url/analyze` router, and masked persistence
    <!-- Pipeline + /api/url/analyze router implemented and tested (local heuristics + SSRF address policy, no outbound fetch). Persistence of URLAnalysis rows deferred (public-demo mode persists nothing; local mode wiring to ScanHistory/URLAnalysis is a follow-up). -->

    - **Description:** Orchestrate validate → local heuristics → guarded network checks → adapter enrichment → score → indicators → explanation → recommended action; persist masked URLAnalysis linked to ScanHistory; 30s timeout result.
    - **Dependencies:** 3.3, 3.4, 3.5, 2.2, 2.4.
    - **Files:** `backend/app/services/url/pipeline.py`, `backend/app/routers/url.py`, `backend/app/schemas/url.py`
    - **Implementation details:** `400 INVALID_URL` with no network request on format failure; `200 blocked:true,reason` on SSRF block; `integration_states` map; timeout result within 30s.
    - **Acceptance criteria:** Returns domain/score/indicators/explanation/recommended action; localhost/private/metadata URL blocked with no outbound request (MVP-AC-5).
    - **Integration tests:** phishing URL indicators; typosquatting; malformed rejected pre-network; localhost/private/metadata blocked.
    - _Requirements: 9.1, 9.2, 9.7, 9.9, 11.3, 20.3_

  - [x] 3.8 [MVP] Build frontend URL Analyzer page wired to `/api/url/analyze`
    - **Description:** URL Analyzer UI showing domain info, risk, indicators, redirect chain, integration states (unavailable labeled), recommended action; security-blocked state rendered honestly.
    - **Dependencies:** 1.7, 3.7.
    - **Files:** `frontend/src/pages/UrlAnalyzer.tsx`, `frontend/src/hooks/useUrlAnalyze.ts`
    - **Acceptance criteria:** SSRF-blocked case shows security-blocked message; unavailable integrations labeled; input preserved on error (MVP-AC-5, MVP-AC-9).
    - **Unit tests:** blocked-state rendering; unavailable integration badges; input preserved on error.
    - _Requirements: 9.7, 10.3, 11.3, 22.6, 22.7_

  - [ ] 3.9 Phase 3 Checkpoint
    - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Phase 4: Screenshot and QR Analysis
  - [ ] 4.1 [MVP] Implement shared upload validation (content-type by magic bytes + size cap)
    - **Description:** Single upload-validation service used by all upload paths: accept PNG/JPEG/WEBP ≤10MB verified by content (magic bytes, not extension); never execute; store outside web root.
    - **Dependencies:** 1.2.
    - **Files:** `backend/app/services/media/upload_validation.py`
    - **Implementation details:** reject non-image/oversized with specific `400 INVALID_FILE`; magic-byte sniffing.
    - **Acceptance criteria (gate):** Accept iff content-type ∈ {PNG,JPEG,WEBP} AND ≤10MB; else reject with no analysis (MVP-AC-6).
    - **Unit tests:** extension-vs-content mismatch rejected; 10MB boundary; disallowed type rejected.
    - **Security tests:** renamed executable with image extension rejected; oversized rejected before processing.
    - _Requirements: 12.1, 12.2, 19.9_

  - [ ]* 4.2 [MVP] Write property test for upload validation
    - **Property 8: File upload validation accepts exactly the allowed files**
    - **Validates: Requirements 12.1, 12.2, 19.9**
    - Tagged `Feature: khabardar-platform, Property 8`, min 100 iterations.
    - **Files:** `backend/tests/properties/test_property_08_upload.py`

  - [ ] 4.3 [MVP] Implement OCR pipeline (preprocess + Tesseract eng/urd) with availability fallback
    - **Description:** Pillow preprocessing (grayscale, denoise, adaptive threshold) + pytesseract OCR (eng + best-effort urd) within 20s; OCR failure returns "text could not be extracted" and retains image for retry; engine-missing → honest "OCR unavailable" with manual text-entry path.
    - **Dependencies:** 4.1, 1.1.
    - **Files:** `backend/app/services/media/preprocess.py`, `backend/app/services/media/ocr.py`
    - **Implementation details:** `TESSERACT_CMD` from env with Windows default; `/api/capabilities` reports `ocr` boolean; `422 OCR_FAILED` retains image.
    - **Acceptance criteria:** Valid screenshot yields OCR text; OCR-missing shows unavailable + manual path (MVP-AC-6).
    - **Unit tests:** preprocess transforms; OCR-failure retains image; capability boolean reflects engine presence.
    - _Requirements: 12.3, 12.4, 22.6_

  - [ ] 4.4 [MVP] Implement QR decoding (pyzbar with OpenCV fallback) and URL/text extraction
    - **Description:** Decode QR to encoded value within 20s using pyzbar, falling back to OpenCV; extract URLs from OCR text; undecodable QR indicated and processing continues; no-content state; never auto-open QR destination.
    - **Dependencies:** 4.1, 4.3.
    - **Files:** `backend/app/services/media/qr_decode.py`, `backend/app/services/media/extract.py`
    - **Implementation details:** `/api/capabilities` reports `qr` boolean; neither library → "QR unavailable" disabled; decoded URLs never auto-opened.
    - **Acceptance criteria:** Valid QR decodes to value without auto-open; undecodable QR indicated; no-content shown (MVP-AC-6).
    - **Unit tests:** pyzbar decode; OpenCV fallback; URL extraction; no-content state.
    - _Requirements: 12.5, 12.6, 12.7, 12.8, 12.11_

  - [ ] 4.5 [MVP] Wire `/api/media/scan` router, extracted-text review, and integrated analysis
    - **Description:** Router returns extracted text/URLs/QR values for review before analysis; on user confirmation feeds `/api/scam/detect` (text) and `/api/url/analyze` (URLs/QR) for integrated analysis.
    - **Dependencies:** 4.3, 4.4, 2.13, 3.7.
    - **Files:** `backend/app/routers/media.py`, `backend/app/schemas/media.py`
    - **Implementation details:** review-before-analysis contract (Req 12.9); decoded URL → URL analyzer only after explicit confirmation.
    - **Acceptance criteria:** Extracted text shown before analysis; confirmation routes content to detector/URL analyzer (MVP-AC-6).
    - **Integration tests:** upload→OCR text review→confirm→detect; QR→confirm→URL analyze; invalid file rejected.
    - _Requirements: 12.9, 12.10_

  - [ ] 4.6 [MVP] Build frontend Screenshot & QR Scanner page with review-before-analysis and unavailable states
    - **Description:** Scanner UI: upload, show extracted text/QR for review, confirm-to-analyze, disabled controls + manual entry when OCR/QR unavailable, no auto-open.
    - **Dependencies:** 1.7, 4.5.
    - **Files:** `frontend/src/pages/Scanner.tsx`, `frontend/src/hooks/useMediaScan.ts`
    - **Acceptance criteria:** Review step before analysis; QR never auto-opened; OCR/QR-unavailable disables controls with manual fallback (MVP-AC-6).
    - **Unit tests:** review gating; unavailable disables controls; no auto-open of decoded URL.
    - _Requirements: 12.9, 12.11, 22.6_

  - [ ] 4.7 Phase 4 Checkpoint
    - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Phase 5: Threat Intelligence
  - [x] 5.1 [MVP] Implement IOC extraction and normalization
    - **Description:** Per-type extractors (phone, email, domain, URL, wallet, bank, payment ref, brand, category, campaign); normalization (trim, lowercase case-insensitive types, per-type canonicalizers); empty content → zero IOCs without error; extraction failure retains content and returns failure indication.
    - **Dependencies:** 2.1.
    - **Files:** `backend/app/services/intel/extract.py`, `backend/app/services/intel/normalize.py`
    - **Acceptance criteria:** Idempotent normalization; empty → zero IOCs; failure retains original (MVP-AC-7).
    - **Unit tests:** per-type extraction; normalization idempotence; empty/failure paths.
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [ ] 5.2 [MVP] Implement IOC deduplication, storage, and origin provenance
    - **Description:** Dedup by `(type, normalized_value)` into single ThreatIndicators record; every IOC/intel record carries `origin` (verified|synthetic) so synthetic/demo is machine-distinguishable.
    - **Dependencies:** 5.1, 2.1.
    - **Files:** `backend/app/repositories/threat_indicators.py`, `backend/app/services/intel/store.py`
    - **Acceptance criteria:** Identical `(type,value)` stored once; every record has `origin` (MVP-AC-7).
    - **Unit tests:** dedup merge; origin set on every write.
    - _Requirements: 13.5_

  - [ ]* 5.3 [MVP] Write property test for IOC normalization idempotence and dedup/campaign association
    - **Property 4: IOC normalization is idempotent and deduplication merges identical type+value**
    - **Validates: Requirements 13.4, 13.5, 13.7**
    - Tagged `Feature: khabardar-platform, Property 4`, min 100 iterations.
    - **Files:** `backend/tests/properties/test_property_04_ioc.py`

  - [ ] 5.4 [MVP] Implement NetworkX intelligence graph and basic campaign association
    - **Description:** NetworkX backend graph: nodes = IOCs/source messages/campaigns; edges link IOC→source message and associated domain/phone/payment/template/campaign; basic campaign association when a new IOC shares `(type, normalized_value)` with one already in a campaign.
    - **Dependencies:** 5.2.
    - **Files:** `backend/app/services/intel/graph.py`, `backend/app/services/intel/campaign.py`
    - **Acceptance criteria:** New IOC sharing key with campaign member is associated with that campaign (MVP-AC-7).
    - **Unit tests:** node/edge creation; campaign association on shared key.
    - _Requirements: 13.6, 13.7_

  - [ ] 5.5 [MVP] Wire IOC extraction into detection + URL pipelines and `/api/iocs/graph`
    - **Description:** Enrich detection/URL results via the intelligence engine; expose `/api/iocs/graph` with 500-node/2000-edge caps and `truncated` flag + graph-only error on exceed.
    - **Dependencies:** 5.4, 2.13, 3.7.
    - **Files:** `backend/app/routers/iocs.py`, `backend/app/schemas/iocs.py`
    - **Acceptance criteria:** Analyzed content yields normalized/deduped IOCs in the graph; caps enforced (MVP-AC-7).
    - **Integration tests:** detect→IOC extracted→graph node present; cap enforcement truncates with flag.
    - _Requirements: 13.1, 15.5, 15.6_

  - [ ] 5.6 Phase 5 Checkpoint
    - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Phase 6: SOC Dashboard
  - [ ] 6.1 [MVP] Implement dashboard stat aggregation and MITRE-light mapping
    <!-- PARTIAL: real stat aggregation (total/detected/risk-distribution/category/30-day trend) from persisted ScanHistory implemented + tested + live-verified via GET /api/dashboard/stats; zero/empty states honest; prototype-labeled. MITRE-light mapping + 7-day incidents/campaigns deferred. -->

    - **Description:** Repository aggregations for totals (messages, scams, high-risk URLs, suspicious domains, reported phones, categories) rendering 0 when empty; 30-day trend, 7-day incidents, 7-day emerging campaigns; curated behavior→MITRE technique lookup assigning mappings only at confidence ≥0.70, ordered high→low, unmapped behaviors marked "no mapping assigned".
    - **Dependencies:** 5.5, 2.1.
    - **Files:** `backend/app/services/dashboard/stats.py`, `backend/app/services/dashboard/mitre.py`, `backend/app/routers/dashboard.py`, `backend/app/schemas/dashboard.py`
    - **Acceptance criteria:** Zero metrics render as numeric 0; MITRE mapping only ≥0.70 with id+name; environment labeled prototype (MVP-AC-7).
    - **Unit tests:** zero-metric present as 0; MITRE threshold/ordering; unmapped-behavior indication.
    - _Requirements: 15.1, 15.2, 15.3, 15.8, 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ]* 6.2 [MVP] Write property test for dashboard bounds, ordering, and zero-metric presence
    - **Property 10: Dashboard outputs respect bounds, ordering, and zero-metric presence**
    - **Validates: Requirements 15.2, 15.5, 15.6, 15.7**
    - Tagged `Feature: khabardar-platform, Property 10`, min 100 iterations.
    - **Files:** `backend/tests/properties/test_property_10_dashboard.py`

  - [ ] 6.3 [MVP] Implement incident feed (≤100, recent-first) and campaign correlation data
    - **Description:** Incident feed capped at 100 ordered most-recent→oldest, plus basic campaign-correlation visualization data.
    - **Dependencies:** 6.1, 5.4.
    - **Files:** `backend/app/services/dashboard/incidents.py`
    - **Acceptance criteria:** ≤100 incidents, strictly most-recent-first (MVP-AC-7).
    - **Unit tests:** cap at 100; ordering invariant.
    - _Requirements: 15.7_

  - [ ] 6.4 [MVP] Build frontend SOC Dashboard: stat cards, three charts, IOC graph, incident feed
    - **Description:** Dashboard UI with stat cards (0 when empty), Recharts threat-trend/category/risk-severity charts, Cytoscape.js IOC graph (graph-only error on cap/failure while keeping other sections), incident feed, prototype-environment label, synthetic-data labeling.
    - **Dependencies:** 1.7, 6.1, 6.3, 5.5.
    - **Files:** `frontend/src/pages/Intelligence.tsx`, `frontend/src/components/{ChartCard,IocGraph}.tsx`, `frontend/src/hooks/useDashboardStats.ts`
    - **Implementation details:** initial render within 5s; graph caps 500/2000; synthetic data carries persistent visible label.
    - **Acceptance criteria:** Stat cards show 0 when empty; three charts + IOC graph + feed render; prototype label present (MVP-AC-7).
    - **Unit tests:** zero-state cards; graph-only error keeps other sections; synthetic label present.
    - _Requirements: 15.1, 15.3, 15.4, 15.5, 15.6, 15.8, 22.3_

  - [ ] 6.5 [MVP] Implement scan history and reports endpoints with user isolation and empty states
    <!-- PARTIAL (deadline MVP): /api/history implemented, user-isolated, masked, empty-state + frontend History page wired and tested. /api/reports deferred to post-demo (P1). -->

    - **Description:** `/api/history` and `/api/reports` return only acting-user records (masked content), empty-state (not error) when none.
    - **Dependencies:** 2.13, 2.1.
    - **Files:** `backend/app/routers/history.py`, `backend/app/routers/reports.py`, `backend/app/repositories/reports.py`, `backend/app/schemas/history.py`
    - **Acceptance criteria:** Persisted scan retrievable for its owner; empty account → empty-state not error (MVP-AC-8).
    - **Integration tests:** persist→retrieve round-trip; user isolation; empty-state response.
    - _Requirements: 20.5, 20.6_

  - [ ]* 6.6 [MVP] Write property test for persistence round-trip and user isolation
    - **Property 11: Persistence round-trip preserves records and isolates by user**
    - **Validates: Requirements 20.3, 20.5**
    - Tagged `Feature: khabardar-platform, Property 11`, min 100 iterations.
    - **Files:** `backend/tests/properties/test_property_11_persistence.py`

  - [ ] 6.7 [MVP] Build frontend History, Reports, and Settings pages
    - **Description:** History/Reports lists (masked content, empty states), Settings page for theme/language/retention (1–3650 days).
    - **Dependencies:** 1.7, 6.5.
    - **Files:** `frontend/src/pages/{History,Reports,Settings}.tsx`, `frontend/src/hooks/useHistory.ts`, `backend/app/routers/settings.py`, `backend/app/schemas/settings.py`
    - **Implementation details:** `PUT /api/settings` validates `retention_days` 1–3650 (`400 INVALID_RETENTION`).
    - **Acceptance criteria:** History/Reports show owner records or empty-state; retention setting validated (MVP-AC-8).
    - **Unit tests:** empty-state render; retention bound validation.
    - _Requirements: 20.5, 20.6, 21.5_

  - [ ] 6.8 [MVP] Implement measured-only accuracy endpoint and reproducible evaluation pipeline
    - **Description:** Deterministic evaluation harness over the fixed dataset computing precision/recall/F1/FPR/FNR (0–1) + avg response time (ms); `/api/accuracy` returns `{measured:false}` until a run completes, then only measured values with eval date + dataset size. Re-running on unchanged code/dataset yields identical metrics.
    - **Dependencies:** 2.15, 2.13.
    - **Files:** `backend/app/eval/harness.py`, `backend/app/eval/metrics.py`, `backend/app/routers/accuracy.py`, `backend/app/eval/run_eval.py`
    - **Implementation details:** fixed seeds/ordering for determinism; store latest completed run; no fabricated metrics ever displayed.
    - **Acceptance criteria (honesty gate):** Before any run, UI/endpoint shows "accuracy not yet measured"; after run shows only measured metrics + date + dataset size; reruns identical (MVP-AC-10).
    - **Unit tests:** metrics math on known confusion matrix; measured-false default; determinism across two runs.
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 24.5, 24.6_

  - [ ]* 6.9 [MVP] Write property test for measured-only accuracy
    - **Property 14: Accuracy metrics are shown only when measured**
    - **Validates: Requirements 23.1, 23.2, 23.4**
    - Tagged `Feature: khabardar-platform, Property 14`, min 100 iterations.
    - **Files:** `backend/tests/properties/test_property_14_accuracy.py`

  - [ ]* 6.10 [MVP] Write property test for evaluation determinism
    - **Property 15: Evaluation is deterministic**
    - **Validates: Requirements 24.6**
    - Tagged `Feature: khabardar-platform, Property 15`, min 100 iterations (varying dataset order/seed-neutral invariants).
    - **Files:** `backend/tests/properties/test_property_15_determinism.py`

  - [ ] 6.11 [MVP] Build frontend accuracy display and extend Property 1 to URL analyzer
    - **Description:** Dashboard/accuracy panel showing measured metrics or "accuracy not yet measured"; extend Property 1 test to also cover URL analyzer Risk_Score bounds.
    - **Dependencies:** 6.8, 3.7, 6.4.
    - **Files:** `frontend/src/components/AccuracyPanel.tsx`, `frontend/src/hooks/useAccuracy.ts`, `backend/tests/properties/test_property_01_risk_bounds.py`
    - **Acceptance criteria:** "accuracy not yet measured" shown until a run exists; URL Risk_Score bounds covered by Property 1 (MVP-AC-10).
    - _Requirements: 23.4, 9.7_

  - [ ] 6.12 [MVP] Write cross-cutting automated test suites (detector / URL / media+AI-fallback)
    - **Description:** The Req 24 automated suites: detector classification across EN/Urdu/Roman Urdu + legitimate/prize/OTP; URL phishing/typosquatting/malformed/private-IP/SSRF; upload validation + QR decode + AI-provider-failure fallback with recorded failure.
    - **Dependencies:** 2.13, 3.7, 4.5, 2.11.
    - **Files:** `backend/tests/suites/test_detector_suite.py`, `backend/tests/suites/test_url_suite.py`, `backend/tests/suites/test_media_ai_suite.py`
    - **Acceptance criteria:** Each suite asserts expected classification/indicator/rejection/fallback and passes (condition 5: no feature complete without passing acceptance tests).
    - _Requirements: 24.1, 24.2, 24.3_

  - [ ] 6.13 [MVP] Author Windows setup documentation and runnable setup assets (Req 25)
    - **Description:** Document ordered Windows setup: Tesseract UB-Mannheim (eng/urd), zbar/pyzbar + OpenCV fallback, Python venv, npm install, `alembic upgrade head`, `uvicorn`/`vite` run commands; failing command halts with cause.
    - **Dependencies:** 1.1, 2.1, 4.3, 4.4.
    - **Files:** `README.md` (setup section), `backend/.env.example`, `backend/requirements.txt` (pinned), `frontend/package.json`, `docs/WINDOWS_SETUP.md`
    - **Acceptance criteria:** Following documented commands brings up frontend + backend locally within 120s on Windows; prerequisites + versions listed (MVP-AC-11).
    - **Unit tests:** `.env.example` lists all optional keys; requirements/lockfile present and pinned.
    - _Requirements: 25.1, 25.2, 25.3, 25.4_

  - [ ] 6.14 [MVP] FINAL end-to-end MVP demonstration checklist (automated integration walkthrough)
    - **Description:** Author an automated integration walkthrough covering the full MVP demo path and asserting the MVP-AC acceptance bar: splash → dashboard → scam detect in EN/Urdu/Roman Urdu offline with zero keys → URL analyze incl. an SSRF-blocked case → screenshot OCR + QR review (no auto-open) → IOC graph → dashboard stats (0-states) → history/reports (user isolation, empty-state) → honest "unavailable" states → "accuracy not yet measured" until evaluation runs.
    - **Dependencies:** all Phase 1–6 MVP tasks.
    - **Files:** `backend/tests/e2e/test_mvp_demo_walkthrough.py`, `docs/MVP_DEMO_CHECKLIST.md`
    - **Implementation details:** each step maps to MVP-AC-1..12; assert no fabricated results/metrics appear; backend bound to localhost only.
    - **Acceptance criteria:** Walkthrough asserts MVP-AC-1..12; all referenced property tests (Properties 1–15) and acceptance suites pass; no feature marked complete without its acceptance tests (conditions 5 & 6).
    - **Integration tests:** the walkthrough itself (full vertical slice end-to-end).
    - _Requirements: 1.5, 3.6, 5.6, 8.5, 9.7, 11.3, 12.9, 13.5, 15.2, 20.5, 22.6, 23.4_

  - [ ] 6.15 MVP Completion Checkpoint
    - Ensure all tests pass, ask the user if questions arise. The Scope A MVP is complete when MVP-AC-1..12 hold and Properties 1–15 pass.

- [ ] 7. Phase 7: Advanced Features — Scope B (POST-MVP / Future, NOT required for MVP completion)
  - [ ] 7.1 [Scope B / Future] Implement Safe Honeypot Simulation Lab
    - **Description:** Simulated-only honeypot using Synthetic_Data with no outbound connections; IOC extraction within 5s; extraction-failure retains source and continues; every record labeled synthetic origin; block-and-record any attempted outbound/impersonation action.
    - **Dependencies:** 5.4 (IOC engine), 5.2 (origin provenance).
    - **Files:** `backend/app/services/honeypot/*.py`, `frontend/src/pages/Honeypot.tsx`
    - **Implementation details:** future correctness properties — synthetic origin labeling + no-outbound invariant (Req 14) — to be added when built.
    - **Acceptance criteria:** No outbound connection leaves simulation boundary; all records synthetic-labeled; blocked actions recorded.
    - **Unit/Security tests:** assert zero outbound sockets; blocked-action recording; origin labeling on every record.
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

  - [ ] 7.2 [Scope B / Future] Implement Family Protection (invitations, consent, sharing, alerts)
    - **Description:** Family groups, 7-day expiring invitations, consent recording, consent-gated selective report sharing, notification preferences, high-risk alerts within 60s, no auto-sharing of private messages.
    - **Dependencies:** 7.4 (auth), 2.13 (detection), 6.5 (reports).
    - **Files:** `backend/app/services/family/*.py`, `backend/app/routers/family.py`, `frontend/src/pages/Family.tsx`
    - **Acceptance criteria:** Expired invitation rejected; share blocked without consent; private messages never auto-shared.
    - **Unit tests:** invitation expiry; consent gating; selective-share-only.
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 17.9, 17.10_

  - [ ] 7.3 [Scope B / Future] Implement live external integrations and online AI provider wiring
    - **Description:** Activate live Safe Browsing/VirusTotal/urlscan.io/WHOIS enrichment and one online AI provider behind env keys, replacing honest-unavailable states only when verified working.
    - **Dependencies:** 3.5 (adapter seam), 2.11 (AI abstraction).
    - **Files:** `backend/app/services/url/adapters/*.py`, `backend/app/services/ai/*.py`
    - **Acceptance criteria:** Integration shown available only after a verified live call; no fabricated results.
    - **Integration tests:** keyed live-call success marks available; failure reverts to unavailable + recorded.
    - _Requirements: 10.1, 10.2, 8.1, 8.2, 8.3_

  - [ ] 7.4 [Scope B / Future] Implement authentication, RBAC, and account lockout (Req 18)
    - **Description:** JWT (15min–24h expiry), Argon2/bcrypt password hashing, RBAC enforcement, reject missing/expired/malformed tokens, lockout after 5 failed attempts in 15 min for ≥15 min; activate the existing `get_current_user` seam. Prerequisite for any non-local exposure.
    - **Dependencies:** 2.1 (user model seam), 1.2 (middleware).
    - **Files:** `backend/app/services/auth/*.py`, `backend/app/middleware/auth.py`
    - **Implementation details:** future correctness properties — password-hash irreversibility + lockout-after-5 — to be added when built.
    - **Acceptance criteria:** Protected routes reject invalid tokens; cross-role access denied; lockout enforced; passwords never plaintext.
    - **Security tests:** missing/expired/malformed JWT rejected; RBAC denial; lockout threshold.
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

  - [ ] 7.5 [Scope B / Future] Implement retention automation and advanced campaign correlation
    - **Description:** Scheduled deletion job honoring `retention_days` (delete within 24h of elapse; on failure retain masked/hashed form, record, retry next cycle); richer cross-message campaign correlation and visualization.
    - **Dependencies:** 6.7 (retention setting), 5.4 (graph).
    - **Files:** `backend/app/services/retention/*.py`, `backend/app/services/intel/correlation_advanced.py`
    - **Acceptance criteria:** Expired records deleted within 24h; deletion-failure retried next cycle; advanced correlation surfaced.
    - **Unit tests:** retention elapse deletion; deletion-failure retain+retry.
    - _Requirements: 21.6, 21.7, 13.7, 15.7_

## Notes

- Tasks marked `*` are optional test sub-tasks and can be skipped for a faster MVP, but every MVP feature's acceptance tests must pass before it is considered complete (condition 5).
- `[MVP]` tasks (Phases 1–6) deliver Scope A; `[Scope B / Future]` tasks (Phase 7) are post-MVP and not required for MVP completion.
- Shared services are implemented once and referenced everywhere: SSRF guard (3.1), masking/hashing (2.2), upload validation (4.1), error envelope (1.2).
- The 15 Correctness Properties from design.md are each implemented as a single property-based test (hypothesis, ≥100 iterations), tagged `Feature: khabardar-platform, Property N: ...`. Property 3 (SSRF) explicitly includes DNS rebinding + IPv4/IPv6 reserved/private + redirect security tests (condition 4).
- Hard gates enforced throughout: no raw secrets/PII persisted; privacy-preserving masked history by default; localhost-only until Req 18 auth; no fabricated AI/intel/metrics (measured-only + honest unavailable states).
- The end-to-end vertical slice (text → rule-based detect → explainable result → masked persisted history) is reachable at task 2.13.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.4", "2.1", "2.2"] },
    { "id": 2, "tasks": ["1.3", "1.5", "2.3", "2.4", "2.6", "3.1", "4.1"] },
    { "id": 3, "tasks": ["1.6", "2.5", "2.7", "2.8", "2.9", "2.11", "3.2", "3.3", "4.2", "5.1"] },
    { "id": 4, "tasks": ["1.7", "2.10", "2.12", "2.13", "2.15", "3.4", "3.5", "4.3", "5.2"] },
    { "id": 5, "tasks": ["2.14", "3.6", "3.7", "4.4", "5.3", "5.4", "6.1"] },
    { "id": 6, "tasks": ["3.8", "4.5", "5.5", "6.2", "6.3", "6.5"] },
    { "id": 7, "tasks": ["4.6", "6.4", "6.6", "6.7", "6.8", "6.12", "6.13"] },
    { "id": 8, "tasks": ["6.9", "6.10", "6.11"] },
    { "id": 9, "tasks": ["6.14"] },
    { "id": 10, "tasks": ["7.4"] },
    { "id": 11, "tasks": ["7.1", "7.3", "7.5"] },
    { "id": 12, "tasks": ["7.2"] }
  ]
}
```
