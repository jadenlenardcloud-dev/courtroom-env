# ⚖️ Courtroom Argument Simulator — Setup & Run Guide

A step-by-step guide to get the Courtroom Argument Simulator running on **Windows**, **macOS**, or **Linux**.

---

## Prerequisites

### Python 3.10+

| OS | How to Install |
|----|---------------|
| **Windows** | Download from [python.org/downloads](https://www.python.org/downloads/). During install, ✅ check **"Add Python to PATH"** |
| **macOS** | Install via Homebrew: `brew install python` — or download from [python.org](https://www.python.org/downloads/) |
| **Linux** | Most distros have it pre-installed. If not: `sudo apt install python3 python3-pip` (Ubuntu/Debian) or `sudo dnf install python3` (Fedora) |

### Verify Python is installed

```bash
# All OS — run in terminal
python --version        # Should show 3.10+
```

> 💡 On macOS/Linux, you may need to use `python3` instead of `python` and `pip3` instead of `pip`.

---

## Step 1: Install Dependencies

Open a terminal in the project folder:

| OS | How to Open Terminal in Project Folder |
|----|---------------------------------------|
| **Windows** | Open the folder in File Explorer → type `cmd` or `powershell` in the address bar → press Enter |
| **macOS** | Open Terminal → `cd /path/to/courtroom` |
| **Linux** | Open Terminal → `cd /path/to/courtroom` |

Then run:

```bash
# Windows (PowerShell or CMD)
pip install -r requirements.txt

# macOS / Linux
pip3 install -r requirements.txt
```

> If `pip` doesn't work on Windows, try: `python -m pip install -r requirements.txt`

---

## Step 2: Choose How to Run

| Mode | What It Does | API Key Needed? |
|------|-------------|-----------------|
| **A) API Server** | Starts a web server with Swagger UI — you play the attorney manually | ❌ No |
| **B) AI Inference** | An LLM automatically plays through the courtroom trials | ✅ Yes |

---

## Option A: Run the API Server (Manual Play)

No API key needed — just start the server and interact via the browser.

### A1. Start the server

```bash
# All OS
python -m uvicorn app:app --host 0.0.0.0 --port 7860
```

> On macOS/Linux, use `python3` if `python` doesn't work.

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:7860 (Press CTRL+C to quit)
```

### A2. Open the Swagger UI

Open your browser and go to: **http://localhost:7860/**

### A3. Start a trial — POST `/reset`

1. Click **POST /reset** → **Try it out**
2. Enter the request body:
   ```json
   {
     "task_id": "task_easy",
     "session_id": null
   }
   ```
   Available tasks: `task_easy`, `task_medium`, `task_hard`
3. Click **Execute**
4. **Copy the `session_id`** from the response — you'll need it for every action

### A4. Take actions — POST `/step`

1. Click **POST /step** → **Try it out**
2. Enter your action (replace `YOUR_SESSION_ID` with the actual session ID):
   ```json
   {
     "session_id": "YOUR_SESSION_ID",
     "action_type": "present_argument",
     "content": "Ladies and gentlemen, Marcus Webb was at City Clinic at the time of the alleged theft, and we have documented proof.",
     "target": null
   }
   ```
3. Click **Execute** — the response shows your reward, jury mood, case strength, etc.
4. **Repeat** with different actions until the trial ends (`"done": true`)

### A5. Available Actions

| Action | Best Phase | target |
|--------|-----------|--------|
| `present_argument` | opening, closing | `null` |
| `question_witness` | examination | witness ID (e.g. `"w1"`) |
| `cross_examine` | cross | witness ID |
| `present_evidence` | examination, cross | evidence ID (e.g. `"ev1"`) |
| `raise_objection` | any | `null` |
| `deliver_closing` | closing | `null` |
| `negotiate_plea` | opening | `null` |
| `request_recess` | any | `null` |
| `accept_plea` | any | `null` |

### A6. Check state anytime — GET `/state/{session_id}`

Shows full trial state including jury mood, case strength, evidence presented, etc.

---

## Option B: Run the AI Agent (Automated Play)

### B1. Get an API Key (pick one — all free)

---

#### 🌟 Recommended: Google AI Studio (Free, no credit card, unlimited)

**Step 1 — Open Google AI Studio**
1. Go to **https://aistudio.google.com/apikey**
2. Sign in with your **Google account** (any Gmail account works)

**Step 2 — Create an API Key**
1. Click the **"Create API key"** button
2. Select an existing Google Cloud project, or let it create one automatically
3. Your API key will be generated — it looks like: `AIzaSy...` (39 characters)
4. Click the **copy icon** to copy it to your clipboard
5. **Save this key somewhere safe** — you'll need it below

> ⚠️ **Important**: Do NOT share this key publicly. Anyone with it can use your API quota.

**Step 3 — Set environment variables**

````powershell
# ── Windows (PowerShell) ──
$env:OPENAI_API_KEY = "AIzaSy_YOUR_KEY_HERE"
$env:API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
$env:MODEL_NAME = "gemini-2.0-flash"
````

````cmd
:: ── Windows (CMD) ──
set OPENAI_API_KEY=AIzaSy_YOUR_KEY_HERE
set API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
set MODEL_NAME=gemini-2.0-flash
````

````bash
# ── macOS / Linux (Bash/Zsh) ──
export OPENAI_API_KEY="AIzaSy_YOUR_KEY_HERE"
export API_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
export MODEL_NAME="gemini-2.0-flash"
````

**Step 4 — Verify it works**

```bash
python -c "from openai import OpenAI; c = OpenAI(api_key='AIzaSy_YOUR_KEY_HERE', base_url='https://generativelanguage.googleapis.com/v1beta/openai/'); r = c.chat.completions.create(model='gemini-2.0-flash', messages=[{'role':'user','content':'Say hello'}], max_tokens=10); print(r.choices[0].message.content)"
```
If you see a response like `Hello!`, your key is working.

**Step 5 — Run the courtroom simulation**

```bash
# Run Task 1 (Easy — Shoplifting case)
python inference.py --task task_easy

# Run all 3 tasks
python inference.py --all
```

> 💡 **Why Google AI Studio?** Completely free, no credit card, generous rate limits, and Gemini works great as an OpenAI-compatible API.

---

#### Option: Hugging Face (Free tier, limited monthly credits)

1. Go to **https://huggingface.co/settings/tokens**
2. Create a **Fine-grained** token → check only **"Make calls to Inference Providers"**
3. Set environment variables:

````powershell
# ── Windows (PowerShell) ──
$env:HF_TOKEN = "hf_your-token"
$env:API_BASE_URL = "https://router.huggingface.co/v1"
$env:MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
````

````cmd
:: ── Windows (CMD) ──
set HF_TOKEN=hf_your-token
set API_BASE_URL=https://router.huggingface.co/v1
set MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
````

````bash
# ── macOS / Linux ──
export HF_TOKEN="hf_your-token"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
````

> ⚠️ HF free tier has limited monthly credits. You may get a 402 error if credits run out.

---

#### Option: OpenAI (Paid, works out of the box)

1. Go to **https://platform.openai.com/api-keys**
2. Sign up → Add payment method → Create API key
3. Set environment variable:

````powershell
# ── Windows (PowerShell) ──
$env:OPENAI_API_KEY = "sk-your-key"
````

````cmd
:: ── Windows (CMD) ──
set OPENAI_API_KEY=sk-your-key
````

````bash
# ── macOS / Linux ──
export OPENAI_API_KEY="sk-your-key"
````

No need to set `API_BASE_URL` or `MODEL_NAME` — defaults to OpenAI's `gpt-4o-mini`.

---

### B2. Run the inference

```bash
# Run one task (all OS)
python inference.py --task task_easy

# Run all 3 tasks
python inference.py --all
```

> On macOS/Linux, use `python3` if `python` doesn't work.

### B3. Understand the output

```
[START] task=task_easy env=courtroom-simulator model=...
[STEP]  step=1 action=present_argument(target=None) reward=0.42 done=false error=null
[STEP]  step=2 action=present_evidence(target=ev1)  reward=0.55 done=false error=null
...
[END]   success=true steps=10 score=0.80 rewards=0.42,0.55,...
```

- **reward**: Score for each action (-1.0 to +1.0)
- **done**: `true` when the trial ends
- **score**: Final grade (0.0 to 1.0)
- **success**: Whether the target score was met

---

## Option C: Docker (Any OS)

Docker works the same on all platforms. Install Docker first:

| OS | Install Docker |
|----|---------------|
| **Windows** | [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) |
| **macOS** | [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) |
| **Linux** | `sudo apt install docker.io` (Ubuntu) or [docs.docker.com](https://docs.docker.com/engine/install/) |

Then run:

```bash
# Build the image
docker build -t courtroom-env .

# Run the container (replace with your API key)
docker run -p 7860:7860 -e OPENAI_API_KEY=your-key-here courtroom-env
```

Open **http://localhost:7860/** for the API docs.

---

## The 3 Trial Scenarios

| Task | Charge | Difficulty | Turns | Target Score | Win Condition |
|------|--------|-----------|-------|-------------|---------------|
| `task_easy` | Petty theft ($320) | Easy | 10 | ≥ 0.65 | Not guilty / Hung jury |
| `task_medium` | Embezzlement ($2.1M) | Medium | 15 | ≥ 0.50 | Not guilty / Hung / Reduced |
| `task_hard` | First-degree murder | Hard | 20 | ≥ 0.40 | Not guilty / Hung jury only |

---

## How Scoring Works

The verdict is determined by three factors:
- **Jury mood** (0.0–1.0) — how sympathetic the jury is
- **Case strength** (0.0–1.0) — quality of your defense
- **Judge patience** (0.0–1.0) — judicial tolerance

| Verdict | Combined Score |
|---------|---------------|
| Not guilty | ≥ 0.75 |
| Hung jury | ≥ 0.55 |
| Guilty (reduced) | ≥ 0.35 |
| Guilty (full) | < 0.35 |

---

## Project File Structure

```
courtroom/
├── app.py             # FastAPI server (Swagger UI)
├── environment.py     # Core simulation engine
├── tasks.py           # 3 trial scenario definitions
├── grader.py          # Scoring/grading system
├── inference.py       # AI agent that auto-plays trials
├── openenv.yaml       # Environment spec metadata
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container setup
└── README.md          # Project documentation
```

---

## Troubleshooting

| Issue | OS | Fix |
|-------|----|-----|
| `python` not recognized | Windows | Reinstall Python and ✅ check "Add to PATH". Or use full path: `C:\Python312\python.exe` |
| `python` not found | macOS/Linux | Use `python3` instead of `python` |
| `pip` not recognized | Windows | Use `python -m pip install -r requirements.txt` |
| `pip` not found | macOS/Linux | Use `pip3` or `python3 -m pip install -r requirements.txt` |
| Port already in use | All | Change the port: `--port 8080` or kill the process using that port |
| `HF_TOKEN not set` | All | Set the environment variable (see Step B1 for your OS) |
| HF credits depleted (402) | All | Switch to Google AI Studio (free, no limits) |
| `Module not found` | All | Make sure you're running from the project folder and dependencies are installed |
| Permission denied | Linux/macOS | Prefix with `sudo` or use a virtual environment: `python3 -m venv venv && source venv/bin/activate` |
| Docker permission denied | Linux | Add yourself to docker group: `sudo usermod -aG docker $USER` then log out and back in |
