# Beyond Express — Product Requirements Document

## Problem Statement
Production-grade white-labeled logistics SaaS platform for the Algerian market (58 wilayas). Features include order management, carrier integration, AI-powered analytics, WhatsApp notifications, and financial reconciliation.

## Architecture
- **Frontend**: React + Tailwind + Shadcn UI + Framer Motion + cmdk
- **Backend**: FastAPI + MongoDB (Motor async) + Argon2id
- **AI**: OpenRouter API (meta-llama/llama-3.3-70b-instruct:free) — replaces Groq
- **Caching**: Redis (optional)
- **Deployment**: Vercel-ready (vercel.json)

## Credentials
- Admin: cherier.sam@beyondexpress-batna.com / admin123456
- Driver: driver@beyond.com / driver123
- Test: test_reg_check@test.com / test123456

---

## Completed (All Tested)

### Core Platform
- [x] White-Label (Beyond Express branding)
- [x] Authentication (JWT + Sessions, Google OAuth, Argon2id)
- [x] 30-min inactivity timeout with warning
- [x] Command Bar (Cmd+K)
- [x] Responsive Layout (Desktop/Tablet/Mobile)
- [x] Login Page (Split layout with branding)
- [x] Registration (all 3 roles: ecommerce, admin, delivery)

### Logistics Operations
- [x] Orders CRUD with server-side pagination
- [x] Warehouse management (zones + depots)
- [x] Returns/RMA with smart decision logic
- [x] Smart Circuit Routing (Haversine algorithm, 58 wilayas)
- [x] Carrier integration framework (Yalidine, ZR Express, DHD...)
- [x] Shipping label generation (A6 thermal format, PDF)
- [x] Bulk label generation (merged PDF)
- [x] Financial COD reconciliation
- [x] Pricing table management

### AI & Intelligence
- [x] AI Brain Center — OpenRouter integration (LIVE mode)
  - Provider: OpenRouter (meta-llama/llama-3.3-70b-instruct:free)
  - Fallback: qwen/qwen3-4b:free
  - 3 agents: Logisticien, Analyste, Moniteur
  - Graceful rate-limit handling + simulation fallback
- [x] AI Chat (Emergent LLM)
- [x] AI Assistant routes

### Communication
- [x] WhatsApp Meta Cloud API integration
- [x] Twilio WhatsApp integration
- [x] Notification system

### Performance & Security
- [x] Centralized API client with exponential backoff retry
- [x] MongoDB indexes (23 indexes on critical collections)
- [x] Redis caching layer (optional)
- [x] Full security audit — API keys backend-only
- [x] Immutable audit log with hash chaining
- [x] Vercel deployment configuration

### Design System
- [x] Premium Dark Tech / Glassmorphism theme
- [x] Landing page with video backgrounds
- [x] Framer Motion animations
- [x] Inter + JetBrains Mono fonts

---

## Test Results
| Iteration | Backend | Frontend | Notes |
|-----------|---------|----------|-------|
| 1-7 | 100% | 100% | Previous features |
| 8 | 100% | 100% | OpenRouter, Registration, Labels |

---

## Backlog

### P0 — Proforma Invoice
- New feature: "Décharge de colis — Facture Proforma"
- Pixel-perfect: header, barcode, client info, order table, totals, signature
- New React component + API endpoint

### P1 — Remaining Fixes
- Investigate /api/shipping/bulk-labels user_id filtering for admin users

### P2 — Future Features
- Live Map Tracking (Google Maps / Leaflet)
- AR Package Scanner mock
- Interactive Shipment Timeline
- Real 3D Bin Packing AI
- Full carrier API integrations

### P3 — Technical Debt
- TypeScript migration
- Unit tests (>80% coverage)
- Refactor OrdersPageAdvanced.js (large file)
- Bundle optimization

---
*Last updated: February 20, 2026*
