<div align="center">

# 📬 Inbox to Action

### Turn email overload into an organized, actionable task list — automatically.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Fly.io](https://img.shields.io/badge/Deployed_on-Fly.io-8B5CF6?logo=flydotio&logoColor=white)](https://fly.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[**Live Demo**](https://your-app-name.fly.dev) · [**Report Bug**](../../issues) · [**Request Feature**](../../issues)

</div>

---

## 📖 Overview

**Inbox to Action** is a full-stack, AI-powered productivity SaaS that eliminates email overload by automatically converting unread Gmail messages into structured, actionable tasks.

Users sign in securely, connect their Gmail account through Google OAuth 2.0, and let the app do the rest. Each unread email is analyzed by **Llama 3 (via the Groq API)**, which extracts a clear task title, assigns a priority, and resolves relative due dates such as *"by next Friday"* or *"tomorrow evening"* into real calendar dates. Tasks are stored in PostgreSQL, and processed emails are automatically marked as read so nothing is ever duplicated.

---

## ✨ Features

- 🔐 **Secure multi-user authentication** powered by Supabase Auth
- 📧 **Seamless Gmail integration** via Google OAuth 2.0
- 🤖 **AI task extraction** with Groq + Llama 3: title, priority and due date from raw email text
- 🗓️ **Relative date resolution**: converts phrases like "next Monday" into absolute dates
- 🚦 **Automatic prioritization** (High / Medium / Low)
- ✅ **Duplicate prevention**: processed emails are marked as read in Gmail
- 🗄️ **Persistent storage** in PostgreSQL with per-user data isolation
- 🎬 **Cinematic, responsive UI** built with Tailwind CSS
- 🐳 **Containerized** with Docker for consistent environments
- ☁️ **Zero-cost, scalable deployment** on Fly.io

---

## 🏗️ Architecture

```mermaid
flowchart LR
    U[User] -->|Sign in| A[Supabase Auth]
    U -->|Connect Gmail| G[Google OAuth 2.0]
    U --> F[Tailwind Frontend]
    F --> B[FastAPI Backend]
    B -->|Fetch unread emails| GM[Gmail API]
    B -->|Parse email text| L[Groq API / Llama 3]
    L -->|Title, priority, due date| B
    B -->|Store tasks| DB[(PostgreSQL)]
    B -->|Mark as read| GM
```

**Workflow**

1. The user authenticates through Supabase and grants Gmail access via Google OAuth 2.0.
2. The backend fetches unread emails from the Gmail API.
3. Each email body is sent to Llama 3 on Groq, which returns structured JSON (title, priority, due date).
4. Tasks are saved to PostgreSQL, linked to the authenticated user.
5. The source email is marked as read to avoid reprocessing.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, FastAPI |
| **Frontend** | HTML, Tailwind CSS, JavaScript |
| **Authentication** | Supabase Auth |
| **Email Integration** | Gmail API, Google OAuth 2.0 |
| **AI / LLM** | Groq API, Llama 3 |
| **Database** | PostgreSQL |
| **Containerization** | Docker |
| **Deployment** | Fly.io |

---

## 📂 Project Structure

> Adjust this to match your actual repository layout.

```
inbox-to-action/
├── app/
│   ├── main.py            # FastAPI entry point
│   ├── routes/            # API routes (auth, gmail, tasks)
│   ├── services/          # Gmail, Groq and Supabase service logic
│   ├── models/            # Pydantic schemas / DB models
│   └── core/              # Config and settings
├── static/                # Frontend assets
├── templates/             # Frontend pages
├── Dockerfile
├── fly.toml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com/) project (Auth + PostgreSQL)
- A [Google Cloud](https://console.cloud.google.com/) project with the Gmail API enabled and OAuth 2.0 credentials
- A [Groq](https://console.groq.com/) API key
- Docker (optional) and the [Fly CLI](https://fly.io/docs/flyctl/install/) for deployment

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/inbox-to-action.git
cd inbox-to-action
```

### 2. Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

```env
# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_or_service_key
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Google OAuth 2.0
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Groq
GROQ_API_KEY=your_groq_api_key

# App
SECRET_KEY=your_random_secret_key
```

### 4. Configure Google OAuth

1. Open the [Google Cloud Console](https://console.cloud.google.com/) and enable the **Gmail API**.
2. Create **OAuth 2.0 Client ID** credentials (Web application).
3. Add `http://localhost:8000/auth/google/callback` as an authorized redirect URI.
4. Request the Gmail scope needed to read and modify messages (for marking emails as read).

### 5. Run locally

```bash
uvicorn app.main:app --reload
```

The app will be available at **http://localhost:8000**, and the interactive API docs at **http://localhost:8000/docs**.

---

## 🐳 Run with Docker

```bash
docker build -t inbox-to-action .
docker run -p 8000:8000 --env-file .env inbox-to-action
```

---

## ☁️ Deploy to Fly.io

```bash
# Install the CLI and log in
fly auth login

# Launch the app (generates fly.toml)
fly launch

# Set your secrets
fly secrets set \
  SUPABASE_URL=... \
  SUPABASE_KEY=... \
  DATABASE_URL=... \
  GOOGLE_CLIENT_ID=... \
  GOOGLE_CLIENT_SECRET=... \
  GOOGLE_REDIRECT_URI=https://<your-app>.fly.dev/auth/google/callback \
  GROQ_API_KEY=... \
  SECRET_KEY=...

# Deploy
fly deploy
```

> Remember to add your production redirect URI to the Google Cloud Console.

---

## 🔌 API Overview

> Example endpoints. Update to match your implementation.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/auth/google/login` | Start the Google OAuth flow |
| `GET` | `/auth/google/callback` | Handle the OAuth callback |
| `POST` | `/emails/sync` | Fetch unread emails and convert them to tasks |
| `GET` | `/tasks` | List the authenticated user's tasks |
| `PATCH` | `/tasks/{id}` | Update a task (status, priority, due date) |
| `DELETE` | `/tasks/{id}` | Delete a task |

---

## 🗃️ Example Output

**Input email**

> *"Hi team, please send the Q4 budget report to finance by next Friday. It's urgent."*

**Extracted task**

```json
{
  "title": "Send Q4 budget report to finance",
  "priority": "high",
  "due_date": "2026-12-04",
  "source": "gmail"
}
```

---

## 🔒 Security

- Authentication and session handling are managed by Supabase.
- OAuth tokens and API keys are stored as environment variables or secrets, never committed to the repository.
- Task data is scoped per user so accounts cannot access each other's data.
- Email content is sent to the LLM only for task extraction.

---

## 🗺️ Roadmap

- [ ] Scheduled background syncing
- [ ] Task categories and labels
- [ ] Calendar integration (Google Calendar)
- [ ] Email reply drafts
- [ ] Push and email reminders for due tasks
- [ ] Support for additional email providers (Outlook)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m "Add amazing feature"`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

---

## 👤 Author

**Vigneshwararaj M**

- GitHub: [vigneshwararaj-md](https://github.com/vigneshwararaj-md)
- LinkedIn: [vigneshwararaj-md](https://linkedin.com/in/vigneshwararaj-md)

---

<div align="center">

⭐ If you found this project useful, please consider giving it a star!

</div>
