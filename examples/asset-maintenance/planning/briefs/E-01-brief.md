# Worker Brief — E-01: Repository Foundation

- **Work-Item ID:** `E-01`
- **Assigned Worker Model:** `gemini-3.8-flash`, thinking level `medium`
- **Coordinator:** `gemini-3.8-flash`, thinking level `high`
- **Branch:** `gemini/E-01-repo-foundation`
- **Dependencies & Input Commits:** Depends on `E-00` (commit `f06090c`)

---

## 1. Outcome

A fully configured Next.js 14 + TypeScript + Vitest repository skeleton adhering to the approved stack in `planning/implementation-manifest.md`. All local developer commands (`npm run dev`, `npm run test`, `npm run lint`, `npm run type-check`, `npm run build`) execute cleanly with zero errors.

---

## 2. Owned Files & Excluded Files

### Owned Files
- `package.json`
- `tsconfig.json`
- `next.config.mjs`
- `vitest.config.ts`
- `.eslintrc.json`
- `.prettierrc`
- `.env.example`
- `.gitignore`
- `src/domain/` (skeleton)
- `src/adapters/` (skeleton)
- `src/app/` (skeleton Next.js App Router entry)
- `src/components/` (skeleton)
- `tests/setup.ts`
- `tests/foundation.test.ts`

### Excluded Files
- `planning/*` (Coordinator owned)
- Domain entities, schemas, and logic (Owned by `E-02`)
- Ingestion, database adapters, and seed fixtures (Owned by `E-03`)
- UI components and charts (Owned by `E-05`)

---

## 3. Exact Requirements & Non-Goals

### Exact Requirements
1. Initialize `package.json` with exact pinned dependencies:
   - Next.js `14.2.x`, React `18.3.x`, React DOM `18.3.x`
   - TypeScript `5.4.x`
   - `recharts` `2.12.x`
   - `lucide-react` (clean industrial icons)
   - Dev dependencies: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `eslint`, `eslint-config-next`, `prettier`, `@types/react`, `@types/node`
2. Configure `tsconfig.json` with strict type checking, path alias `@/*` -> `./src/*`.
3. Configure `vitest.config.ts` with JSDOM environment and React testing library support.
4. Configure `.env.example` declaring environment schema (with no required secret keys for the local baseline).
5. Ensure `.gitignore` protects against committing `node_modules/`, `.next/`, `.env.local`, coverage reports.
6. Provide a basic smoke test `tests/foundation.test.ts` verifying testing harness works.

### Non-Goals
- Do not install TailwindCSS (Manifest ADR-0005 pins Vanilla CSS / CSS Modules).
- Do not install Supabase, MongoDB, Prisma, Axios, or external cloud SDKs.
- Do not add speculative AI/LLM libraries (LangChain, LangGraph).

---

## 4. Acceptance Criteria

- `npm install` completes cleanly.
- `npm run test` passes smoke test.
- `npm run type-check` executes with 0 errors.
- `npm run lint` executes with 0 warnings/errors.
- `npm run build` succeeds.

---

## 5. Security, Safety, Data & Offline Risks

- Ensure zero telemetry or analytics tracking enabled by default in Next.js.
- Ensure `.env.example` has no hardcoded credentials or API tokens.
- Ensure no remote telemetry calls occur during build or test execution.

---

## 6. Required Verification Commands

- `npm install`
- `npm run test`
- `npm run type-check`
- `npm run lint`
- `npm run build`
