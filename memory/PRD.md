# Beyond Express — Product Requirements Document

## Problem Statement
Production-grade white-labeled logistics SaaS platform for the Algerian market (58 wilayas). Features include order management, carrier integration, AI-powered analytics, WhatsApp notifications, and financial reconciliation.

## Architecture
- **Frontend**: React + Tailwind + Shadcn UI + Framer Motion + cmdk
- **Backend**: FastAPI + MongoDB (Motor async) + Argon2id
- **AI**: OpenRouter API (meta-llama/llama-3.3-70b-instruct:free + qwen/qwen3-4b:free fallback)
- **Caching**: Redis (optional)
- **Deployment**: Vercel-ready (vercel.json)

## Credentials
- Admin: cherier.sam@beyondexpress-batna.com / admin123456
- Test: test_reg_check@test.com / test123456

---

## Completed (All Tested)

### Core Platform
- [x] White-Label (Beyond Express branding)
- [x] Authentication (JWT + Sessions, Google OAuth, Argon2id)
- [x] Registration (all 3 roles: ecommerce, admin, delivery)
- [x] Command Bar (Cmd+K)
- [x] Responsive Layout

### Logistics Operations
- [x] Orders CRUD with pagination
- [x] Warehouse management
- [x] Returns/RMA with smart routing
- [x] Carrier integration (Yalidine, ZR Express, DHD)
- [x] Shipping labels (A6 thermal, fixed overlap bug)
- [x] Financial COD reconciliation

### AI & Intelligence (OpenRouter - FREE)
- [x] AI Brain Center — OpenRouter integration (LIVE mode, 0$ cost)
  - Primary: meta-llama/llama-3.3-70b-instruct:free
  - Fallback: qwen/qwen3-4b:free → simulation
  - Silent error handling (no red errors ever)
  - 3 agents: Logisticien, Analyste, Moniteur

### Communication
- [x] WhatsApp integration — ALL ROLES (admin, ecommerce, delivery)
- [x] Notification system

### Performance & Security
- [x] Centralized API client with retry
- [x] MongoDB indexes (23 indexes)
- [x] Security audit — API keys backend-only
- [x] Vercel deployment config

### Landing Page (Premium Dark Tech)
- [x] Hero with video backgrounds
- [x] Features grid with animations
- [x] Stats widgets (10K+ orders, 500+ merchants)
- [x] **Pricing Packs** (Starter/Pro/Business) — Glassmorphism
- [x] **Partners section** (5 carriers, hover glow effects)
- [x] CTA + Footer

---

## Test Results
| Iteration | Backend | Frontend | Notes |
|-----------|---------|----------|-------|
| 8 | 100% | 100% | OpenRouter, Registration, Labels |
| 9 | 100% | 100% | AI silent fallback, WhatsApp roles, Packs/Partners |

---

## Backlog

### P0 — Proforma Invoice
- "Décharge de colis — Facture Proforma" generation

### P1 — Enhancements
- Admin bulk-labels user filtering fix
- Real carrier API live integration

### P2 — Future
- Live Map Tracking (Leaflet)
- AR Package Scanner mock
- Interactive Shipment Timeline
- Unit tests (Jest/Pytest >80%)

---
*Last updated: February 20, 2026*
