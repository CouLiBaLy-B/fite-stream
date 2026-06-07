# FitStream Frontend v2 — Next.js Dashboard

Réécriture complète du frontend en **Next.js 14 + TypeScript + Tailwind**.

## ✨ Nouveau design

- **Style Dashboard Pro** inspiré Linear/Vercel
- Sidebar fixe 240px, dark glassmorphism
- Command palette (⌘K)
- Animations Framer Motion
- Temps réel WebSocket
- 100% responsive

## 🚀 Installation

```bash
cd frontend-next
npm install
npm run dev
# → http://localhost:3000
```

Le frontend proxy vers l'API FastAPI sur http://localhost:8000

## 📁 Structure

```
app/
  page.tsx          → Home
  create/page.tsx   → Creator Studio (6 pipelines)
  gallery/page.tsx  → Gallery avec recherche
  monitor/page.tsx  → Dashboard temps réel
components/
  Sidebar.tsx       → Navigation
lib/
  utils.ts          → Helpers
```

## 🎬 Fonctionnalités

- **6 pipelines** : Animate, Story, Try-On, Compose, Style, Real-Time
- **Drag & drop** upload avec previews
- **WebSocket** progression live
- **Gallery** hover-to-play, filtres
- **Monitor** : GPU, p50/p95, cache, analytics 24h
- **Toasts** Sonner pour feedback
- **Templates** prompts prêts à l'emploi

## 🔧 API

Toutes les routes `/api/*` sont proxifiées vers `localhost:8000` via next.config.js

## 🎨 Design System

- Couleurs : bg #050507, panel #0a0a0f, purple #8b5cf6
- Glass : backdrop-blur-2xl + white/[0.02]
- Radius : 12-20px
- Font : Inter

Remplace l'ancien frontend statique dans `/frontend/`