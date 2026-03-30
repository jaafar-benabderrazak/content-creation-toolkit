# Requirements: Content Creation Toolkit v2.0

**Defined:** 2026-03-30
**Core Value:** One command produces a publish-ready video — from prompt to YouTube upload — fully cloud-hosted with auth, persistent data, and no local GPU needed.

## v2.0 Requirements — Cloud Deploy

### Authentication (Clerk)

- [ ] **AUTH-01**: Dashboard protected by Clerk authentication — unauthenticated users redirected to sign-in
- [ ] **AUTH-02**: Clerk configured via Vercel Marketplace integration (auto-provisioned env vars)
- [ ] **AUTH-03**: User session persists across page reloads and browser restarts

### Database (Supabase)

- [ ] **DB-01**: Video roadmap stored in Supabase `videos` table (replaces video_roadmap.json)
- [ ] **DB-02**: Execution history stored in Supabase `executions` table (replaces execution_log.json)
- [ ] **DB-03**: Generated prompts stored in Supabase `prompts` table (all 8 prompt chain sections per video)
- [ ] **DB-04**: User settings stored in Supabase `settings` table (API keys, webhook URLs, profile configs)
- [ ] **DB-05**: Dashboard reads/writes all data from Supabase — no local JSON file dependencies
- [ ] **DB-06**: Existing 210 roadmap entries migrated from video_roadmap.json to Supabase

### Cloud Pipeline (Modal/Replicate)

- [ ] **CLOUD-01**: Video generation pipeline runs on Modal (GPU A10G) — no local GPU required
- [ ] **CLOUD-02**: Image generation uses Replicate Seedream/Gemini APIs (already cloud, just remove local SD fallback as primary)
- [ ] **CLOUD-03**: Music generation via Suno kie.ai API (already cloud)
- [ ] **CLOUD-04**: Video rendering via Remotion Lambda or cloud render (replace local npx remotion render)
- [ ] **CLOUD-05**: Pipeline triggered from dashboard via API call to Modal endpoint
- [ ] **CLOUD-06**: Pipeline status/logs streamed back to dashboard in real-time

### CI/CD (GitHub + Vercel)

- [ ] **CICD-01**: Dashboard deployed to Vercel via GitHub push (auto-deploy on merge to main)
- [ ] **CICD-02**: GitHub repository created with proper .gitignore, README, and branch protection
- [ ] **CICD-03**: Environment variables managed via Vercel dashboard (Supabase, Clerk, API keys)
- [ ] **CICD-04**: Preview deployments on PR for dashboard changes

### Dashboard Migration

- [ ] **DASH-01**: Replace local pipeline-api proxy with direct Supabase queries
- [ ] **DASH-02**: Replace Cloudflare tunnel dependency — all data from Supabase, pipeline trigger via Modal API
- [ ] **DASH-03**: Roadmap page reads from Supabase `videos` table with real-time updates
- [ ] **DASH-04**: Execution history reads from Supabase `executions` table
- [ ] **DASH-05**: Prompt chain reads from Supabase `prompts` table

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Multi-user / team features | Single user for v2.0, multi-user deferred |
| Stripe billing | No monetization in v2.0 |
| Custom domain | Use Vercel default domain for now |
| Mobile app | Web dashboard is sufficient |
| Local GPU fallback | v2.0 is cloud-only by design |

## Traceability

| Requirement | Phase | Status |
| ----------- | ----- | ------ |
| AUTH-01 | Phase 27 | Pending |
| AUTH-02 | Phase 27 | Pending |
| AUTH-03 | Phase 27 | Pending |
| DB-01 | Phase 25 | Pending |
| DB-02 | Phase 25 | Pending |
| DB-03 | Phase 25 | Pending |
| DB-04 | Phase 25 | Pending |
| DB-05 | Phase 25 | Pending |
| DB-06 | Phase 25 | Pending |
| CLOUD-01 | Phase 28 | Pending |
| CLOUD-02 | Phase 28 | Pending |
| CLOUD-03 | Phase 28 | Pending |
| CLOUD-04 | Phase 28 | Pending |
| CLOUD-05 | Phase 28 | Pending |
| CLOUD-06 | Phase 28 | Pending |
| CICD-01 | Phase 26 | Pending |
| CICD-02 | Phase 26 | Pending |
| CICD-03 | Phase 26 | Pending |
| CICD-04 | Phase 26 | Pending |
| DASH-01 | Phase 29 | Pending |
| DASH-02 | Phase 29 | Pending |
| DASH-03 | Phase 29 | Pending |
| DASH-04 | Phase 29 | Pending |
| DASH-05 | Phase 29 | Pending |

**Coverage:**
- v2.0 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-03-30*
*Traceability updated: 2026-03-30*
