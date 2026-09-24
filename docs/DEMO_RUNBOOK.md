# ShiftMate demo runbook — laptop server + tablet

The laptop runs the ShiftMate server. The tablet (operator app) and the console browsers connect to it over the same Wi-Fi. Everything runs locally except the optional language AI (DeepSeek), which needs internet. Without it, the app uses templates.

The minute-by-minute script is in the technical spec, §13.2. This page covers the server side: setting up, starting, connecting the tablet, checking, and recovering.

## 1. One-time setup (laptop)

1. Install Python 3.12, `uv`, Node 22 and `pnpm`.
2. In the repo root, copy `.env.example` to `.env` and set:
   - `DEVICE_SECRET_MASTER_KEY`: 64 hex characters. Generate with `python -c "import secrets; print(secrets.token_hex(32))"`.
   - `DATABASE_URL=sqlite:///./var/shiftmate.db`
   - `DEMO_MODE=true`
   - Optional AI: `AI_ENABLED=true` and `DEEPSEEK_API_KEY=...`. Credits are limited, so leave `AI_ENABLED=false` while rehearsing.
   - Optional console fleet page: `FLEET_SIM_ENABLED=true`.
3. Install server packages: `cd server` then `uv sync`.
4. Allow the port through Windows Firewall once (admin PowerShell):
   `netsh advfirewall firewall add rule name="ShiftMate 8000" dir=in action=allow protocol=TCP localport=8000`
   If Windows asks "Allow Python to communicate on these networks" the first time the server starts, allow **Private networks**.

## 2. Network

- The laptop and tablet must be on the **same network**, and that network must let devices reach each other. Venue and guest Wi-Fi often isolate clients. The safest setup is a **phone hotspot** or the **laptop's own mobile hotspot** (Windows Settings → Network → Mobile hotspot).
- Mark the laptop's network as **Private** in Windows. Firewall rules for "Private" networks do not apply on "Public" ones.
- The tablet's clock must be within **5 minutes** of the laptop's. Every tablet request is signed with a timestamp. Turn on automatic time on both devices.

## 3. Start the server (demo day)

From `server/`:

```powershell
uv run python -m shiftmate.cli demo --reset
```

- `--reset` wipes demo data and re-seeds it for **today**: tasks, handover and forecast are placed relative to the current date. Use it at the start of each run-through. Without `--reset`, the existing data is kept.
- The command updates the database schema, seeds, then prints a banner and serves on all network interfaces, port 8000. Keep this window open. Ctrl+C stops the server.
- `--fleet` / `--no-fleet` switches the fleet simulator on or off for this run. `--port 8080` changes the port.

The banner shows everything you need:

```
  Tablet server URL     http://172.18.9.119:8000        <- enter this in the app (A0 server setup)
  Other addresses       http://192.168.56.1:8000
  Pairing codes         100007 EX-07, 200002 WL-02, 300003 HT-03
  Operators (PIN)       Ravi OP-0007 on EX-07 (1234), Kumar OP-0011 on EX-07 (2468), Senthil OP-0021 on HT-03 (7777)
  Console logins        sup.priya / Priya-Demo-2026, saf.meena / Meena-Demo-2026, trn.arjun / Arjun-Demo-2026, ...
```

If several addresses are listed, use the one on the Wi-Fi or hotspot the tablet is connected to. Addresses like `192.168.56.x` usually belong to VirtualBox or other virtual adapters.

## 4. Connect the tablet

1. On the tablet's browser, open `http://<laptop-ip>:8000/api/v1/health`. It should show `"status":"ok"`. If it does not load, see §6.
2. Start the operator app from the repo root: `pnpm --filter @shiftmate/operator start --lan`. Scan the QR code with **Expo Go** on the tablet. Metro serves the app from port **8081**, so allow that port in the firewall too: `netsh advfirewall firewall add rule name="Expo Metro 8081" dir=in action=allow protocol=TCP localport=8081`.
3. On the app's **Device setup** screen, leave the mode on **Site server** and type the server address from the banner (`http://<laptop-ip>:8000`). Then tap **EX-07**. The pairing code field can stay empty; the demo code 100007 is used. Use **HT-03** (300003) for the haul-truck part via the presenter's "Switch machine". To pre-fill the address, set `EXPO_PUBLIC_DEFAULT_SERVER_URL=http://<laptop-ip>:8000` in `apps/operator/.env` before starting Expo.
4. The status bar shows **Online**, and "N waiting" drops to 0 within about 5 s of each action. **Status & sync** (A14) shows the server, the last sync, and any rejected records. The presenter panel (long-press the clock, or F2) has **Simulate no signal / Restore signal** for the offline beat, and **Sync now**.
5. Pairing codes are reusable in demo mode. After `demo --reset` the server no longer knows the tablet: the status screen says "pair again". Use the presenter's **Switch machine** and pair again.

## 5. Checks (T − 30 min)

| Check | How | Expected |
|---|---|---|
| Server healthy | `uv run python -m shiftmate.cli doctor` | "Database connection: OK" and the banner with 100 machines, 48 operators, 2 models |
| Server-side demo flow | `uv run pytest tests/test_demo_flow.py -v` | 2 passed (J1 excavator day, J2 haul-truck switch) |
| Whole server suite | `uv run pytest` | all passed. It makes no AI calls. |
| Tablet reaches the laptop | tablet browser → `/api/v1/health` | `ok` |
| AI (only if used) | banner line "Language AI" | "on (DeepSeek, key set)". Needs internet. It falls back to templates silently if the network drops. |
| Results file for 4:45 | `uv run python -m shiftmate_ml.eval.report` | writes `eval/results/results.md` with the SIMULATED DATA banner |

Run the checks **before** `demo --reset`. The test suite uses its own temporary database and never touches the demo data.

## 6. Recovery

| Problem | Action |
|---|---|
| Tablet cannot open `/api/v1/health` | Check both devices are on the same network, and the network is Private. Run the `netsh` rule from §1. Try the other address from the banner. Or switch to a hotspot. |
| Tablet gets 401 on every request | The tablet clock is off by more than 5 minutes: fix the time. Or the device was revoked or reset: pair again with the code. |
| "database is locked" or odd errors | Stop the server (Ctrl+C) and start it again with the same command. |
| Demo state is messed up | Ctrl+C, then `uv run python -m shiftmate.cli demo --reset` (about 5 s). Reset the app on the tablet and pair again. |
| AI answers stop | Expected without internet: templates take over. Nothing to fix during the demo. |
| Server laptop crashes | The tablet keeps working offline. Restart the server; queued records sync once when it is back. |

## 7. Say during the demo

Machine signals and detections are simulated. Estimates come from a model trained on **simulated** data. Thresholds are illustrative. The LoRa SOS path and SMS are simulated. The server runs on a laptop over plain HTTP on the local network.

## 8. Known server-side limits for this demo

- **Web app at `/app`** (the spec's backup path) needs two things from the app side: an export built with base path `/app`, and a secure context on the tablet. The current export loads its files from `/_expo/…`, so it does not load under `/app`. Over plain `http://<ip>` the browser storage it needs is blocked unless Chrome's `chrome://flags/#unsafely-treat-insecure-origin-as-secure` lists `http://<laptop-ip>:8000`. The native Android app has neither problem.
- **Console pages** (`/console`) are served only once the console app is built (`STATIC_CONSOLE_DIR`). Until then, `/docs` can show read-only console data after logging in there. It cannot run write actions such as review or approve, because they need the `X-Requested-With: shiftmate-console` header. `tests/test_demo_flow.py` proves those steps on the server.
- The server uses SQLite on the laptop and one worker, which is fine for one tablet and a few console sessions.
