# Beyond Express — PRD

## Architecture
- **Frontend**: React + Tailwind + Shadcn UI + Framer Motion + react-barcode
- **Backend**: FastAPI + MongoDB + Argon2id
- **AI**: Multi-Provider (OpenRouter/Groq/Together/Moonshot) + per-agent matrix
- **Deploy**: Vercel-ready

## Completed (Iterations 8-12, All Tested)

### Core: Auth, Registration (3 roles), Command Bar, Responsive Layout
### Logistics: Orders CRUD, Warehouse, Returns, Carrier Integration, Labels (A6 fixed), COD
### Documents: Facture Proforma (BEY-XXXX, 12-col, A4 print CSS)
### AI Multi-Agent: 4 providers, 3 agents, matrix config, silent fallback
### AI Chat: OpenRouter httpx (fallback: "Assistant en maintenance"), session history
### Driver App: Tasks, status update (JSON body), stats, WhatsApp, AI access
### WhatsApp: ALL roles (admin/ecommerce/delivery)
### Landing: Packs (Starter/Pro/Business), Partners (5 carriers)
### Security: Keys backend-only, _id exclusion, 23 indexes

## Test Results
| Iter | Backend | Frontend |
|------|---------|----------|
| 8-9 | 100% | 100% |
| 10 | 100% | 100% |
| 11 | 20/20 | 100% |
| 12 | 17/17 | 100% |

## Note: OpenRouter key expired (402). New key needed for LIVE AI mode.

## Backlog
- P1: New OpenRouter API key for LIVE AI
- P2: Live Map Tracking, AR Scanner
- P3: Unit tests, TypeScript

*Updated: Feb 24, 2026*
