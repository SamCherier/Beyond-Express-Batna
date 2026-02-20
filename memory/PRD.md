# Beyond Express — Product Requirements Document

## Problem Statement
Production-grade white-labeled logistics SaaS platform for the Algerian market (58 wilayas).

## Architecture
- **Frontend**: React + Tailwind + Shadcn UI + Framer Motion + cmdk
- **Backend**: FastAPI + MongoDB (Motor async) + Argon2id
- **AI**: OpenRouter API (meta-llama/llama-3.3-70b-instruct:free + qwen/qwen3-4b:free fallback → simulation)
- **Deployment**: Vercel-ready (vercel.json)

---

## Completed (All Tested via curl + testing agent)

### Core Platform
- [x] Authentication (JWT + Argon2id + Google OAuth)
- [x] Registration — all 3 roles (ecommerce, admin, delivery) ✅
- [x] Command Bar, Responsive Layout, Landing Page

### AI Brain Center (OpenRouter - FREE, 0$)
- [x] Primary: meta-llama/llama-3.3-70b-instruct:free
- [x] Fallback cascade: qwen3-4b:free → simulation (zero red errors)
- [x] All roles can query (delivery, ecommerce, admin) ✅
- [x] No "SIM" badge, no model name exposed, no error messages

### WhatsApp
- [x] All roles: admin, ecommerce, delivery can access sidebar + routes ✅
- [x] MongoDB _id leak fixed in conversations endpoint

### Landing Page
- [x] Pricing Packs (Starter/Pro/Business) — Glassmorphism
- [x] Partners (5 carriers) — hover glow effects
- [x] Hero, Features, Stats, CTA, Footer

### Security & Production
- [x] API keys backend-only (zero trust frontend)
- [x] MongoDB _id exclusion audit
- [x] 23 MongoDB indexes

---

## Known Mocks (Documented & Transparent)
- ZR Express carrier: Mock adapter (no real API available)
- Subscriptions: Simulated payment (no Stripe configured)
- Notifications (legacy): Logs to DB with `simulated: true` flag
- AI fallback: Returns cached simulation responses when OpenRouter unavailable

## Test Results
| Iteration | Backend | Frontend |
|-----------|---------|----------|
| 8 | 100% | 100% |
| 9 | 100% | 100% |
| QA Audit | 9/9 pass | Compiled OK |

## Backlog
- P0: Proforma Invoice generation
- P1: Admin bulk-labels filtering
- P2: Live Map Tracking, AR Scanner, Unit tests

---
*Last updated: February 20, 2026 — QA Senior Audit Complete*
