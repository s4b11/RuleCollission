# RuleCollision web app

One React app with three areas: the patient assistant (`/a/:slug`, `/case`), the staff dashboard (`/ops`) and Agent Studio (`/studio`).

```bash
npm install
npm run dev      # http://localhost:5173, expects the backend on http://localhost:8000
npm run build
```

Set `VITE_API_URL` to the backend address when building for deployment. See the [project README](../README.md).
