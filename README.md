# AI Voice Calling Agent — Admissions Lead Qualification (POC)

An AI voice agent that calls leads, collects admission information (name, email, program of interest), qualifies interested students, and produces a clean list of qualified leads for the admissions team.

## Stack

- Backend: FastAPI + PostgreSQL (SQLAlchemy)
- Voice calls: Vapi
- Admin panel: React (Vite)

## Project structure

```
backend/
  app/
    main.py            FastAPI entry point, starts background dialer
    config/            settings and database connection
    models/            leads, calls, campaign tables
    schemas/           request/response models
    api/               routes: auth, leads, campaign, webhooks, export
    services/          lead import, Vapi calls, qualification, CRM sync
    workers/           background dialer loop
    utils/             phone/email validation, JWT security
admin-panel/           React admin dashboard with login
```

## 1. Backend setup

Requirements: Python 3.11+, PostgreSQL running locally.

```
cd backend
python -m venv venv
venv\Scripts\activate        (Windows)
source venv/bin/activate     (Linux/Mac)
pip install -r requirements.txt
```

Create the database:

```
createdb voice_agent
```

Copy `.env.example` to `.env` and fill in your values (database URL, admin username/password, JWT secret, Vapi keys).

Run the backend:

```
uvicorn app.main:app --reload --port 8000
```

Tables are created automatically on first start. API docs: http://localhost:8000/docs

## 2. Admin panel setup

Requirements: Node.js 18+.

```
cd admin-panel
npm install
npm run dev
```

Open http://localhost:5173 and log in with the ADMIN_USERNAME / ADMIN_PASSWORD from your backend `.env`.

## 3. Vapi setup

The assistant configuration — system prompt, voice, transcriber, and structured data schema — lives in code at `backend/app/services/assistant_prompt.py` and is sent to Vapi as a transient inline `assistant` object with every call, instead of referencing an assistant created in the dashboard. Edit that file to change the script or voice.

1. Create an account at vapi.ai and get your private API key → `VAPI_API_KEY`.
2. Add a phone number in Vapi (for Pakistan, connect a local SIP trunk via BYO SIP) → `VAPI_PHONE_NUMBER_ID`.
3. Set the webhook Server URL so Vapi can send call results back to your backend. Either:
   - Set it on the phone number in the Vapi dashboard, or
   - Set `VAPI_SERVER_URL` in `.env` (e.g. your ngrok URL during local testing) — `build_assistant()` reads it and includes a `server.url` field in the inline assistant object automatically.
   ```
   https://your-public-domain/api/webhooks/vapi
   ```
   For local testing, expose your backend with ngrok: `ngrok http 8000` and use the ngrok URL.
   Set a secret in Vapi and put the same value in `VAPI_WEBHOOK_SECRET`.

## 4. Running a campaign

1. Log in to the admin panel.
2. Leads page → Import CSV. The file needs a `phone` column; optional columns: `name`, `email`, `program`, `crm_id`. Numbers are normalized to +92 format, duplicates and invalid numbers are skipped automatically.
3. Campaign page → set calling hours, concurrency, retries → Start campaign.
4. The background dialer calls pending leads only within calling hours, retries no-answers, and updates each lead when Vapi reports the call result.
5. Dashboard shows live progress. Leads page → Export qualified leads downloads the final CSV for the admissions team.

## 5. CRM sync

Set `CRM_WEBHOOK_URL` in `.env` to an endpoint that accepts lead updates as JSON. Finished leads are pushed there automatically and marked as synced. Leave it empty to skip syncing and rely on the CSV export instead.

## Notes for the POC

- Test Vapi calling to Pakistani numbers and confirm per-minute cost before running the full campaign.
- Test the assistant voice and script on your own number first; tune until it sounds natural in Urdu/English mix.
- Pilot with ~100 leads before the full 5,000.
