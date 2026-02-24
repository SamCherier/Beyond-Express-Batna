# Beyond Express — Product Requirements Document

## Problem Statement
Production-grade white-labeled logistics SaaS platform for the Algerian market (58 wilayas).

## Architecture
- **Frontend**: React + Tailwind + Shadcn UI + Framer Motion + cmdk + react-barcode
- **Backend**: FastAPI + MongoDB (Motor async) + Argon2id
- **AI**: Multi-Provider Mesh (OpenRouter, Groq, Together AI, Moonshot/Kimi) — per-agent model assignment
- **Deployment**: Vercel-ready (vercel.json)

---

## Completed

### Core
- [x] Auth (JWT + Sessions + Google OAuth + Argon2id)
- [x] Registration (3 roles), Command Bar, Responsive Layout

### Logistics
- [x] Orders CRUD, Warehouse, Returns/RMA, Carrier Integration
- [x] Shipping Labels (A6, fixed overlap), Bulk Labels
- [x] COD Reconciliation, Smart Routing (58 wilayas)
- [x] **Facture Proforma** (BEY-XXXX, 12-col table, print CSS)

### AI Multi-Agent Architecture (NEW)
- [x] **4 Providers**: OpenRouter, Groq, Together AI, Moonshot/Kimi
- [x] **Per-provider API key management** (save, mask, test connection)
- [x] **3 Agents**: Logisticien, Analyste, Moniteur
- [x] **Agent Matrix**: Admin assigns provider+model per agent via dropdown
- [x] **Graceful error handling**: 402/429 → amber warning, never red crash
- [x] **Zero Trust**: Keys stored in DB, never exposed to frontend

### Communication
- [x] WhatsApp — ALL ROLES

### Landing Page
- [x] Packs (Starter/Pro/Business), Partners (5 carriers)

### Security
- [x] API keys backend-only, MongoDB _id exclusion, 23 indexes

---

## Test Results
| Iter | Backend | Frontend | Feature |
|------|---------|----------|---------|
| 8 | 100% | 100% | OpenRouter, Registration, Labels |
| 9 | 100% | 100% | AI fallback, WhatsApp roles, Packs |
| 10 | 100% | 100% | Facture Proforma |
| 11 | 100% (20/20) | 100% | Multi-Provider AI Config |

## Backlog
- P1: Admin bulk-labels filtering
- P2: Live Map Tracking, AR Scanner, Timeline
- P3: Unit tests, TypeScript migration

---
*Last updated: February 24, 2026*
