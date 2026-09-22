# Demo Fallback Matrix & Contingency Protocol

> **Purpose:** Guarantee zero live presentation crashes during judge evaluation.  
> **Source:** `PRESENTATION_SYSTEM_PLAN.md` Section 14.

---

## Failure Mode & Fallback Action Table

| Risk / Failure Mode | Root Cause | Immediate Fallback Protocol | Time to Recover |
|---|---|---|:---:|
| **Local Port Conflict / Dev Server Down** | Port 3000 occupied or process killed | Run `npm run build && npm run start` on backup port 3001. Fallback to pre-recorded walkthrough video. | < 15 seconds |
| **Corrupted In-Memory State** | Accidental sequence mismatch during rehearsal | Click "↺ Reset Demo State" in header or send `POST /api/admin/reset`. Restores pristine seed fixtures immediately. | < 2 seconds |
| **Network Loss / Wi-Fi Disconnect** | Venue internet congestion | The application baseline operates 100% locally with deterministic fixtures. Zero internet connection required. Demonstrate offline queue as an active feature! | 0 seconds (By Design) |
| **Browser Rendering / WebGL Freeze** | GPU acceleration glitch in presentation laptop | Hard refresh (`Ctrl + F5`) or open clean Incognito window. | < 5 seconds |
| **Judge Asks to Inspect Code / Proof** | Technical deep-dive challenge | Open `tests/cartridges/asset-maintenance/e2e-hero-path.test.ts` and run `npm test`. Show the current verified result and limitations. | < 10 seconds |

---

## Known-Good Checkpoint
- Git Commit: `e33125c`
- Local URL: `http://localhost:3000`
- Deterministic Seed: `seed_cat_2026_v1`
