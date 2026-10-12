# Improv Faceoff Test-Case Catalog

## Player Journey

```text
Main Menu -> anonymous guest -> Matchmaking -> Media Setup -> Countdown
-> Live Round -> Gemini Judging + Persistence -> Results -> Next Match / Data
```

The catalog follows that journey, so a broken player experience has one clear
section to inspect. Every case has a stable ID, purpose, likely failure point,
and pass condition.

## Test Layers

| Layer | Proves | Normal PR suite? |
| --- | --- | --- |
| Unit | Deterministic rule or transformation. | Yes |
| Backend integration | Flask, Socket.IO, state, and fake providers work together. | Yes |
| Component | UI state, control, dialog, and error rendering works. | Yes, once frontend runner exists |
| Browser E2E | Complete player-visible flow works. | Gameplay/release changes |
| Live API / media smoke | Real credentials, provider route, or WebRTC media connects. | No; before demos/deploys/debugging |

Live API tests use `@pytest.mark.live_api` and require:

```powershell
$env:RUN_LIVE_API_TESTS = "1"
python -m pytest tests/live_api -q
```

They are separate because providers consume quota and can be temporarily down
even when application code is correct.

## 1. Main Menu and Player Identity

**User goal:** Open the app, understand it, and start or resume play.

**Can break:** Home page, local-storage guest UUID, `guest:create`, Socket.IO,
Rules dialog, Progress dialog, Leaderboard navigation, keyboard focus.

| ID | Individual purpose | Pass condition | Layer |
| --- | --- | --- | --- |
| MENU-001 | Load home screen. | Branding, Find Match, Rules, Progress, and Leaderboard render. | Component |
| MENU-002 | Create first identity. | Valid UUID is stored and sent through `guest:create`. | Component/Integration |
| MENU-003 | Restore identity. | Reload uses stored UUID rather than making a second identity. | Component/E2E |
| MENU-004 | Recover duplicate identity. | “Identity connected elsewhere” is explained and fresh-guest recovery works. | E2E |
| MENU-005 | Open/close rules. | Close, Escape, click-outside, and focus return work. | Component |
| MENU-006 | Keyboard navigation. | Main menu has logical tab order and visible focus. | Component |
| MENU-007 | Handle match server unavailable. | Find Match reports recoverable error rather than doing nothing. | Component/E2E |

## 2. Matchmaking

**User goal:** Join the queue, cancel if needed, and enter one shared match.

**Can break:** Socket.IO transport, guest binding, Redis queue, duplicate
protection, pairing, `match:found`, leave, reconnect, scenario generation.

| ID | Individual purpose | Pass condition | Layer |
| --- | --- | --- | --- |
| QUEUE-001 | Join queue. | Searching appears only after successful `queue:join`. | Component/E2E |
| QUEUE-002 | Cancel queue. | `queue:leave` removes guest and returns home state. | Integration/E2E |
| QUEUE-003 | Prevent duplicate position. | Repeated joins never create two waits or two matches. | Integration |
| QUEUE-004 | Pair players. | Both receive same match ID and opposite player slots. | Integration/E2E |
| QUEUE-005 | Handle queue error. | Error is visible, retry works, no infinite search state. | Component/E2E |
| QUEUE-006 | Handle waiting disconnect. | Guest is released and can reconnect/retry without ghost queue entry. | Integration/E2E |
| QUEUE-007 | Handle opponent leaving. | Remaining player is informed and can requeue. | E2E |
| QUEUE-008 | Prepare scenario. | Both get same scenario and distinct roles before countdown. | Integration/E2E |
| QUEUE-009 | Handle scenario failure. | Safe fallback/error is visible; clients never stall. | Integration/E2E |

## 3. Media Setup and Peer Connection

**User goal:** Grant device access, enter one live room, see the other player,
and avoid unexplained connection stalls.

**Can break:** browser permissions/devices, `media:credentials`, LiveKit URL,
token, room, identity, WebSocket, ICE/TURN, local publication, remote discovery,
device toggles, Socket.IO reconnect.

| ID | Individual purpose | Pass condition | Layer |
| --- | --- | --- | --- |
| MEDIA-001 | Grant camera/mic permission. | Local preview and enabled controls appear. | Browser smoke |
| MEDIA-002 | Deny permission. | Specific recovery message; no permanent connecting screen. | Browser smoke |
| MEDIA-003 | Handle missing/busy device. | UI identifies problem and offers retry/settings path. | Browser smoke |
| MEDIA-004 | Issue credentials. | Players get distinct identities/tokens for same room. | Backend integration |
| MEDIA-005 | Reject bad credentials request. | Non-participant/ended match cannot obtain credentials. | Backend integration |
| MEDIA-006 | Connect both peers in time. | Two browsers join same room and see each other within **10 seconds**. | Two-player live media smoke |
| MEDIA-007 | Diagnose stalled connection. | At 10 seconds, report last phase: credentials, room join, publish, or remote discovery. | Two-player live media smoke |
| MEDIA-008 | Clean up timeout. | Timed-out rooms disconnect; neither client stays connecting. | Two-player live media smoke |
| MEDIA-009 | Toggle camera. | Only local camera publication/state changes. | Browser smoke |
| MEDIA-010 | Toggle microphone. | Only local microphone publication/state changes. | Browser smoke |
| MEDIA-011 | Reconnect match transport. | UI shows reconnecting then resumes or gives safe terminal error. | E2E |

`MEDIA-006` is the demo-stall test. Use two independent browser contexts, a
disposable LiveKit environment, and synthetic tracks—not real player devices.
A token-only backend test cannot detect browser WebRTC stalls.

## 4. In-Game Round

**User goal:** Understand the scene, take turns, use Switches fairly, and see
an accurate live transcript.

**Can break:** readiness/countdown/timer, speaker ownership, keyboard handling,
Switch validation/idempotency, transcript persistence, Deepgram, interruption,
event broadcast, round cutoff.

| ID | Individual purpose | Pass condition | Layer |
| --- | --- | --- | --- |
| GAME-001 | Require both players ready. | Second ready begins shared countdown; first alone cannot start. | Integration/E2E |
| GAME-002 | Display countdown. | Both see synchronized 3-2-1 before play. | Component/E2E |
| GAME-003 | Keep timer authoritative. | Server ends round at configured duration. | Integration |
| GAME-004 | Display timer safely. | Timer follows server, never negative, and visibly ends. | Component/E2E |
| GAME-005 | Show active speaker. | Both clients distinguish speaker/listener. | Component/E2E |
| GAME-006 | Change turn. | Canonical final speech advances turn exactly once. | Integration |
| GAME-007 | Start transcription. | Authorized stream starts with correct PCM limits and provider status. | Integration |
| GAME-008 | Reject invalid audio. | Empty, oversized, wrong-player, or no-stream input fails safely. | Integration |
| GAME-009 | Display transcript. | Partial/final lines are attributed, chronological, authoritative. | Component/E2E |
| GAME-010 | Preserve canonical dialogue. | Only active player final speech is accepted scene dialogue. | Unit/Integration |
| GAME-011 | Enforce Switch eligibility. | Only listener may Switch in active round with inventory. | Unit/Integration |
| GAME-012 | Update Switch inventory. | Valid Switch spends one; invalid/duplicate spends none. | Unit/Integration |
| GAME-013 | Preserve speaker on Switch. | Switch interrupts but does not change turn owner. | Integration |
| GAME-014 | Explain Switch. | Both clients show one feedback event for each accepted Switch. | Component/E2E |
| GAME-015 | Keyboard Switch. | Space works only when allowed, never while typing/disabled. | Component/E2E |
| GAME-016 | Rapid Switches. | Replacement/rejected speech stays distinct; no double debit/visual. | Integration/E2E |
| GAME-017 | Remove STT cumulative prefix. | Provider hypotheses never duplicate prior text. | Unit |
| GAME-018 | Gate replacement STT. | Rejected end turn cannot attach to new speech; ready gates fresh audio. | Unit/Integration |
| GAME-019 | End round cleanly. | Last speech truncates correctly; later gameplay input is rejected. | Integration |
| GAME-020 | Handle opponent disconnect. | Remaining player sees explanation and safe termination. | Integration/E2E |

## 5. End Results and Next Match

**User goal:** Get one clear result even if AI fails, then leave or play again.

**Can break:** scoring transition, judge input, Gemini request/retry/schema,
speed scoring, winner selection, result delivery, reconnect retention, cleanup.

| ID | Individual purpose | Pass condition | Layer |
| --- | --- | --- | --- |
| RESULTS-001 | Start judging once. | Ended match makes one judge request and one authoritative result. | Integration |
| RESULTS-002 | Build judge input. | Scenario, canonical/rejected speech, Switches, and latency follow contract. | Unit |
| RESULTS-003 | Validate normal judgment. | Valid provider reply creates scores, coaching, valid highlights. | Unit |
| RESULTS-004 | Retry transient AI failure. | First timeout/network failure then success returns normal result. | Unit |
| RESULTS-005 | Handle malformed AI output. | Retry max is respected; match never crashes. | Unit/Integration |
| RESULTS-006 | Fall back after AI failure. | Retained fallback/objective results replace infinite judging state. | Integration/E2E |
| RESULTS-007 | Keep results identical. | Both players receive matching winner, scores, and feedback. | Integration/E2E |
| RESULTS-008 | Score Switch recovery. | Known timestamps match configured speed curve. | Unit |
| RESULTS-009 | Determine winner/tie. | Same input always selects same winner or explicit tie. | Unit |
| RESULTS-010 | Render normal screen. | Scores, winner, coaching, highlights, navigation render. | Component |
| RESULTS-011 | Render unavailable coaching. | Failure is explained but next-match navigation works. | Component/E2E |
| RESULTS-012 | Restore after refresh. | Reconnect receives original retained `results:ready`. | Integration/E2E |
| RESULTS-013 | Start next match. | Prior match releases correctly and player can queue again. | Integration/E2E |
| RESULTS-014 | Clean abandoned results. | Both disconnected guests release after grace period. | Integration |

## 6. Leaderboard and Progress

**User goal:** View durable results without losing a completed match when
optional data services fail.

**Can break:** PostgreSQL, transaction ordering, idempotent writes, ranking,
feedback API, local guest UUID, charts, fallback fixture, dialog state.

| ID | Individual purpose | Pass condition | Layer |
| --- | --- | --- | --- |
| DATA-001 | Persist before notification. | Feedback exists before `results:ready`. | Integration |
| DATA-002 | Persist idempotently. | Repeated scoring cannot duplicate match/guest history. | Integration |
| DATA-003 | Survive database outage. | Players receive results; store failure is observable. | Integration |
| DATA-004 | Rank leaderboard. | Best score ranks; ties use timestamp then guest UUID. | Unit/Integration |
| DATA-005 | Render leaderboard states. | Loading, empty, live, unavailable, sample fallback are distinct. | Component/E2E |
| DATA-006 | Isolate progress. | Endpoint returns only requested guest history. | Integration |
| DATA-007 | Keep chronology stable. | Oldest-first records have stable match number and ID. | Integration |
| DATA-008 | Render progress states. | Loading, sample, live, error, retry are distinct. | Component |
| DATA-009 | Expose feedback accessibly. | Chart point/tooltip/record shows score, skills, feedback, match ID. | Component |

## 7. Live API and Deployment

**User goal:** Never reach a demo with missing credentials, broken provider
network route, invalid model, or incomplete deployment configuration.

**Can break:** env loading, Gemini model/key/network/schema, Deepgram Flux
WebSocket, LiveKit credentials, Redis/PostgreSQL config, health/readiness,
public WebSocket/CORS.

Do not use player transcripts here—use fixtures, empty streams, and synthetic
media only.

| ID | Individual purpose | Pass condition | Layer |
| --- | --- | --- | --- |
| API-READY-001 | Backend health. | `GET /api/health` is 200 without providers. | Integration/Deploy smoke |
| API-READY-002 | Missing configuration. | `/api/ready` is 503 with variable names, never values. | Integration |
| API-READY-003 | Configured readiness. | Full environment reports ready. | Integration/Deploy smoke |
| API-READY-004 | Public Socket.IO transport. | Deployment accepts WebSocket-only handshake. | Deploy smoke |
| API-GEMINI-001 | Real Gemini request. | Fixture reaches configured model and returns `JudgeResult` before timeout. | Live API smoke |
| API-GEMINI-002 | Gemini response compatibility. | Response passes schema and highlight sanitization. | Live API smoke |
| API-GEMINI-003 | Gemini outage player behavior. | Simulated network/timeout yields fallback, not stuck screen. | Integration/E2E |
| API-STT-001 | Real Deepgram connection. | Flux WebSocket opens/closes with configured key/model and no audio. | Live API smoke |
| API-STT-002 | Deepgram failure behavior. | `STT_CONNECTION_FAILED` is surfaced; no infinite connecting. | Integration/Browser smoke |
| API-LIVEKIT-001 | Real peer media. | `MEDIA-006` passes in disposable environment within 10 seconds. | Live media smoke |
| API-DATA-001 | Database readiness. | Migration plus expected read/write succeeds. | Deploy smoke |

```powershell
# Ordinary tests: no external provider requests.
python -m pytest -m "not live_api" -q

# Actual Gemini + Deepgram connection checks.
$env:RUN_LIVE_API_TESTS = "1"
python -m pytest tests/live_api -q

# Health, readiness, public WebSocket probe.
python scripts/check_deployment.py https://your-backend.example
```

## 8. Cross-Cutting Experience Requirements

| ID | Individual purpose | Pass condition | Layer |
| --- | --- | --- | --- |
| XC-001 | Keyboard navigation. | All critical controls/dialogs have logical focus order. | Component/E2E |
| XC-002 | Screen-reader status. | Queue, connection, countdown, errors, results announce useful changes. | Component |
| XC-003 | Error clarity. | Every error explains failure and supported recovery. | Component/E2E |
| XC-004 | Narrow-screen use. | Media, Switch, transcript, error, results usable at mobile width. | Visual/E2E |
| XC-005 | No secret leakage. | Browser payloads/errors/test output never expose API keys or credentials. | Unit/Integration |
| XC-006 | Contract compatibility. | HTTP/Socket.IO payloads validate against `shared/` contracts. | Contract |

## Release Gates

| When | Required checks |
| --- | --- |
| Every pull request | Unit, contracts, backend integration, lint, frontend build |
| Gameplay / Socket.IO change | Pull-request checks plus affected two-player E2E cases |
| Media / LiveKit change | `MEDIA-004`–`MEDIA-008`, especially 10-second `MEDIA-006` |
| AI / transcription change | Relevant ordinary tests plus `API-GEMINI-001` / `API-STT-001` |
| Before demo | Deployment probe, Gemini, Deepgram, and two-peer media smoke tests |

## Intentional MVP Exclusions

Accounts, private rooms, best-of-three, modifiers, recordings, advanced
moderation, and computer-vision scoring are not MVP features. Add their test
cases when the feature enters scope.
