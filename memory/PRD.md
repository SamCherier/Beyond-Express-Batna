# Beyond Express — Product Requirements Document

## Problem Statement
Production-grade white-labeled logistics SaaS platform for the Algerian market (58 wilayas).

## Architecture
- **Frontend**: React + Tailwind + Shadcn UI + Framer Motion + cmdk + react-barcode
- **Backend**: FastAPI + MongoDB (Motor async) + Argon2id
- **AI**: OpenRouter API (Llama 3.3 70B free → Qwen 3 4B free → Simulation)
- **Deployment**: Vercel-ready (vercel.json)

---

## Completed (All Tested)

### Core Platform
- [x] Authentication (JWT + Sessions + Google OAuth + Argon2id)
- [x] Registration — all 3 roles (ecommerce, admin, delivery)
- [x] Command Bar, Responsive Layout, Landing Page

### Logistics Operations
- [x] Orders CRUD with server-side pagination
- [x] Warehouse management (zones + depots)
- [x] Returns/RMA with smart routing
- [x] Carrier integration (Yalidine, ZR Express, DHD)
- [x] Shipping labels (A6 thermal, fixed overlap)
- [x] Bulk label generation
- [x] Financial COD reconciliation
- [x] Smart Circuit Routing (Haversine, 58 wilayas)

### Documents & Invoicing
- [x] **Facture Proforma / Décharge de colis** (NEW)
  - Backend: POST /api/invoices/proforma/generate
  - Auto-increment reference (BEY-0001, BEY-0002...)
  - A4 print-optimized with @media print
  - Header: Logo + Title + Barcode (react-barcode)
  - Client info section
  - 12-column order table
  - Totals: Montant, Livraison, Prestation (15%), Net
  - Signature area
  - Button in Orders page (data-testid: generate-proforma-button)

### AI Brain Center (OpenRouter - FREE, 0$)
- [x] Primary: meta-llama/llama-3.3-70b-instruct:free
- [x] Fallback cascade: qwen3-4b:free → simulation
- [x] Silent error handling (zero red errors, graceful degradation)
- [x] All roles can query

### Communication
- [x] WhatsApp — ALL ROLES (admin, ecommerce, delivery)
- [x] WhatsApp Meta Cloud API integration

### Landing Page
- [x] Pricing Packs (Starter/Pro/Business)
- [x] Partners section (5 carriers, hover glow)
- [x] Hero, Features, Stats, CTA, Footer

### Security & Performance
- [x] API keys backend-only (zero trust)
- [x] MongoDB _id exclusion audit
- [x] 23 MongoDB indexes
- [x] Vercel deployment config

---

## Test Results
| Iteration | Backend | Frontend | Feature |
|-----------|---------|----------|---------|
| 8 | 100% | 100% | OpenRouter, Registration, Labels |
| 9 | 100% | 100% | AI silent fallback, WhatsApp roles, Packs |
| 10 | 100% | 100% | Facture Proforma |

## Backlog
- P1: Admin bulk-labels filtering
- P2: Live Map Tracking (Leaflet)
- P2: AR Scanner, Interactive Timeline
- P3: Unit tests, TypeScript migration

---
*Last updated: February 20, 2026*
