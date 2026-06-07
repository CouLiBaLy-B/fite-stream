# 📱 FitStream Mobile

React Native / Expo mobile app for FitStream.

## Setup

```bash
cd mobile
npm install
npx expo start
```

## Screens

- **Create** — Upload photo, select mode/style, write prompt, generate
- **Gallery** — Browse generated videos with pull-to-refresh and pagination
- **Settings** — Configure server URL, check GPU status, about

## Architecture

```
mobile/
├── src/
│   ├── App.js                 # Entry + Navigation
│   ├── screens/
│   │   ├── CreateScreen.js    # Generation UI
│   │   ├── GalleryScreen.js   # Video gallery
│   │   └── SettingsScreen.js  # Config + status
│   └── services/
│       └── api.js             # FitStream API client (uses /m/ endpoints)
├── package.json
└── app.json
```

## API

Uses the mobile-optimized `/m/` endpoints:
- `GET /m/status` — Quick server status
- `POST /m/generate` — Submit generation (supports file upload)
- `GET /m/job/{id}` — Compact job status
- `GET /m/gallery` — Paginated gallery
- `GET /m/styles` — Available styles
- `GET /m/templates` — Prompt templates

## Connect to Server

1. Start the FitStream server: `python -m fitstream.api.server`
2. In the app Settings tab, enter the server URL
3. Test the connection
