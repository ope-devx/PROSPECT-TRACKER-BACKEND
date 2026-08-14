# Prospect Tracker

A personal freelance sales CRM with AI-powered outreach generation. Built to solve a real workflow problem: manually copying prospect data into a chat window to generate cold DMs, then doing it again 24 hours later for follow-ups.

**Live demo:** [prospect-tracker-tawny.vercel.app](https://prospect-tracker-tawny.vercel.app)

---

## What it does

Track freelance prospects through a sales pipeline and generate personalized outreach messages directly from their stored profile data — no copy-pasting required.

- Add prospects with niche, follower count, platform, and notes
- Move them through a status pipeline: `new → contacted → follow_up → meeting_booked → closed / lost`
- Filter by niche and sort by followers
- Generate a cold DM with one click — the model reads the prospect's actual data and writes to their context
- Generate a follow-up message that references the original cold DM — the model sees what was already sent and continues the thread

The follow-up endpoint returns a `400` if no cold DM has been generated yet. The context chain is intentional: a follow-up written without knowing what was said first is useless.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS v4, React Router v6 |
| Backend | FastAPI, psycopg2 |
| Database | PostgreSQL on Supabase |
| AI | OpenRouter API — `nvidia/nemotron-3-ultra-550b-a55b:free` via plain `requests.post()` |
| Hosting | Vercel (frontend) · Render (backend) |

No LLM SDK. API calls are raw HTTP — I wanted to understand the request/response shape before abstracting it away.

---

## AI endpoints

```
POST /prospects/{id}/cold-dm-generator
```
Reads the prospect record from the database, constructs a prompt with their name, niche, follower count, and notes, calls the LLM, saves the generated message to `last_message`, and returns it.

```
POST /prospects/{id}/generate-follow-up-message
```
Reads the prospect record *and* the stored `last_message`. Returns `400` if `last_message` is empty — a follow-up without a prior message has no basis. Otherwise, instructs the model to write a follow-up that acknowledges what was already sent.

---

## Background

Built during SIWES (industrial training) as part of a structured 40-day roadmap toward AI Application Engineering. The tracker started as a localStorage-only React app and was progressively rebuilt: REST backend → PostgreSQL migration → AI integration → production deployment.

The AI feature wasn't planned from the start. It was added when I noticed I was spending 10–15 minutes per prospect manually formatting data for LLM prompts. That friction became the spec.
