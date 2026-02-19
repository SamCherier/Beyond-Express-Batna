# Beyond Express — Deployment Notes

## Architecture
- **Frontend**: React (CRA + CRACO) → Static build
- **Backend**: FastAPI (Python) → Requires separate deployment
- **Database**: MongoDB → MongoDB Atlas recommended
- **Cache**: Redis → Upstash Redis recommended

## Environment Variables Required

### Backend (.env)
```
MONGO_URL=mongodb+srv://<user>:<pass>@cluster.mongodb.net
DB_NAME=beyond_express_db
GROQ_API_KEY=gsk_xxxxxxxxxxxx
WHATSAPP_PHONE_ID=123456789
WHATSAPP_ACCESS_TOKEN=EAAxxxxx
REDIS_URL=redis://default:xxx@xxx.upstash.io:6379
JWT_SECRET=<random-64-char-string>
CORS_ORIGINS=https://your-domain.vercel.app
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://your-backend-url.com
```

## Security Checklist
- [ ] All API keys in backend .env ONLY (never frontend)
- [ ] Frontend calls /api/* endpoints, backend proxies to external services
- [ ] CORS restricted to production domain
- [ ] JWT tokens with expiration
- [ ] MongoDB unique indexes on email, tracking_id
- [ ] Redis cache with TTL (no stale data)

## Vercel Deployment
1. Connect GitHub repo to Vercel
2. Set root directory to `frontend`
3. Build command: `yarn build`
4. Output: `build`
5. Add environment variables in Vercel dashboard
6. Deploy backend separately (Railway, Render, or Vercel Serverless)
