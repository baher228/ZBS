# Tech Debt Tracker

### [P1] TracePilot demo is scenario-specific and should be replaced by visible AI demo-room flow
- **Added:** 2026-04-25
- **Category:** architecture
- **Location:** `backend/app/demo_controller/actions.py`
- **Impact:** The current browser-demo prototype proves bounded actions, but it does not match the intended product demo of an AI demo-room builder with page-local actions and visible cursor playback.
- **Suggested Fix:** Introduce a generic `DemoManifest` with global knowledge, page-local knowledge, allowed actions, and visual event playback. Keep TracePilot as a sample scenario only if needed.
- **Status:** Open

### [P2] Full frontend lint fails on pre-existing formatting issues
- **Added:** 2026-04-25
- **Category:** code-quality
- **Location:** `frontend/src`
- **Impact:** `npm run lint` fails outside the new sandbox files, making it harder to use lint as a quality gate for future UI work.
- **Suggested Fix:** Run Prettier across existing frontend files in a dedicated formatting-only change.
- **Status:** Open
