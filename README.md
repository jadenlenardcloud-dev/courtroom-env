<<<<<<< HEAD
# ⚖️ Courtroom Argument Simulator

**An OpenEnv-compliant reinforcement learning environment where an AI agent acts as a criminal defense attorney.**

The environment simulates real courtroom proceedings — from opening statement through cross-examination to closing argument — across three tasks of increasing difficulty.

---

## Motivation

Legal reasoning is one of the most demanding real-world tasks: it requires multi-step argumentation, evidence synthesis, witness strategy, and adversarial reasoning under pressure. No existing OpenEnv environment covers this domain. This environment fills that gap with a fully deterministic, graded simulation that mirrors how actual trials proceed, making it ideal for evaluating and training language agents on strategic legal reasoning.

---

## Environment Description

The agent plays a **defense attorney** in a criminal trial. At each step, the agent observes the current trial phase, jury mood, available evidence, the prosecution's latest move, and the current witness — then chooses a legal action.

Trials proceed through five phases:

```
opening → examination → cross-examination → closing → verdict
```

The final verdict is computed deterministically from three state variables:

- **Jury mood** (0.0–1.0): how sympathetic the jury is
- **Case strength** (0.0–1.0): how well the agent has built its defense
- **Judge patience** (0.0–1.0): judicial tolerance for the agent's conduct

| Verdict | Condition |
|---|---|
| Not guilty | score ≥ 0.75 |
| Hung jury | score ≥ 0.55 |
| Guilty (reduced) | score ≥ 0.35 |
| Guilty (full) | score < 0.35 |

---

## OpenEnv API

```python
from environment import CourtroomEnvironment, Action

env = CourtroomEnvironment(task_id="task_easy")
obs = env.reset()                    # → Observation
obs, reward, done, info = env.step(  # → (Observation, Reward, bool, dict)
    Action(
        action_type="present_argument",
        content="The defendant was at City Clinic at the time of the alleged theft...",
        target=None,
    )
)
state = env.state()                  # → full internal state dict
```

---

## Observation Space

| Field | Type | Description |
|---|---|---|
| `turn` | int | Current turn (0-indexed) |
| `max_turns` | int | Episode length |
| `phase` | str | `opening \| examination \| cross \| closing \| verdict` |
| `charge` | str | Criminal charge |
| `defendant_profile` | dict | Name, age, occupation, prior record, alibi |
| `current_witness` | dict \| null | Active witness on stand |
| `evidence_available` | list | Evidence not yet presented |
| `prosecution_last_move` | str | Prosecution's most recent statement |
| `jury_mood` | float | 0.0 (hostile) → 1.0 (sympathetic) |
| `judge_patience` | float | 0.0 (contempt) → 1.0 (patient) |
| `case_strength` | float | Defense narrative strength 0.0–1.0 |
| `objections_remaining` | int | Objections left this phase |
| `message` | str | Narrative description |

---

## Action Space

| `action_type` | Best phase | Description |
|---|---|---|
| `present_argument` | opening, closing | Make a legal argument |
| `cross_examine` | cross | Challenge prosecution witness |
| `raise_objection` | any | Object to prosecution move |
| `present_evidence` | examination, cross | Submit evidence (set `target=evidence_id`) |
| `question_witness` | examination | Question defense witness |
| `negotiate_plea` | opening | Attempt plea negotiation |
| `request_recess` | any | Request a break |
| `deliver_closing` | closing | Final summation |
| `accept_plea` | any | Accept prosecution's plea offer |

---

## Reward Function

```
reward = 0.5 × argument_quality
       + 0.3 × phase_appropriateness
       + 0.2 × jury_impact
       + penalty
```

Partial progress signals throughout:
- Presenting strong evidence → +0.2 argument quality bonus
- Cross-examining in correct phase → +0.1 bonus
- Raising objection with remaining budget → +0.05 jury impact
- Wrong-phase actions → −0.15 to −0.2 penalty
- Exhausted objection budget → −0.3 penalty
- Delivering closing in closing phase → scales with current case strength

Range: `[−1.0, +1.0]` per step.

---

## Tasks

### Task 1 — Easy: The Shoplifting Alibi
> **Charge:** Petty theft, $320  
> **Max turns:** 10 | **Target score:** ≥ 0.65  

Marcus Webb is accused of shoplifting based on blurry CCTV footage. He has a documented medical appointment as alibi. The agent must present the alibi evidence and discredit the identification. An LLM with basic legal reasoning should pass this.

**Key evidence:** Medical record (ev1), bus pass log (ev3), CCTV expert analysis (ev2)  
**Win condition:** `not_guilty` or `hung_jury`

---

### Task 2 — Medium: The Embezzlement Trial
> **Charge:** Embezzlement + wire fraud, $2.1M  
> **Max turns:** 15 | **Target score:** ≥ 0.50  

CFO Priya Nair faces financial fraud charges with a hostile whistleblower and forensic accountant as prosecution witnesses. The agent must present board authorization documents, expose the whistleblower's conflict of interest, and counter the forensic analysis.

**Key evidence:** Board minutes (ev1), HR complaint (ev2), audit trail (ev3)  
**Win condition:** `not_guilty`, `hung_jury`, or `guilty_reduced`

---

### Task 3 — Hard: The Premeditated Murder Trial
> **Charge:** First-degree premeditated murder  
> **Max turns:** 20 | **Target score:** ≥ 0.40  

Elias Vance faces murder charges with a hostile jury (initial mood: 0.2) and an aggressive prosecution. All evidence is circumstantial. The agent must suppress illegally obtained evidence, dismantle each prosecution witness, build an alibi timeline, and deliver a compelling closing argument.

**Key evidence:** Phone metadata (ev1), mediation agreement (ev2), suppression motion (ev3)  
**Win condition:** `not_guilty` or `hung_jury` only

---

## Grader Scoring (0.0–1.0)

Each task is scored deterministically on completion:

| Component | Easy weight | Medium weight | Hard weight |
|---|---|---|---|
| Verdict outcome | 50% | 40% | 40% |
| Evidence presented | 20% | 25% | 25% |
| Jury mood | 20% | 20% | 20% |
| Judge patience / Case strength | 10% | 15% | — |
| Action discipline | — | — | 15% |

---

## Baseline Scores

Baseline scores using `gpt-4o-mini`:

| Task | Score | Verdict | Passed |
|---|---|---|---|
| task_easy | ~0.71 | not_guilty | ✓ |
| task_medium | ~0.52 | hung_jury | ✓ |
| task_hard | ~0.38 | guilty_reduced | ✗ |
| **Average** | **~0.54** | | **2/3** |

---

## Setup & Usage

### Local (Python)

```bash
git clone https://huggingface.co/spaces/your-username/courtroom-env
cd courtroom-env
pip install -r requirements.txt

# Run baseline on one task
export OPENAI_API_KEY=sk-...
python inference.py --task task_easy

# Run all tasks
python inference.py --all

# Use a different model
python inference.py --all --model gpt-4o
```

### Docker

```bash
docker build -t courtroom-env .
docker run -p 7860:7860 -e OPENAI_API_KEY=sk-... courtroom-env
```

API docs available at: `http://localhost:7860/`

### REST API (HF Spaces)

```bash
# Start episode
curl -X POST https://your-space.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_easy"}'

# Take action
curl -X POST https://your-space.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123",
    "action_type": "present_evidence",
    "content": "I present the medical appointment record showing my client was across town.",
    "target": "ev1"
  }'
```

---

## Project Structure

```
courtroom-env/
├── environment.py     # Core OpenEnv environment (Observation, Action, Reward, step/reset/state)
├── tasks.py           # Task definitions (3 scenarios with witnesses, evidence, reward config)
├── grader.py          # Deterministic graders producing 0.0–1.0 scores
├── inference.py       # Baseline LLM agent using OpenAI API
├── app.py             # FastAPI server for Hugging Face Spaces
├── openenv.yaml       # OpenEnv spec metadata
├── Dockerfile         # Container definition
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

## License

MIT
=======
# courtroom-env
court room rl 
>>>>>>> 6c447534fef49eccc859b05505f89bf45ac8987f
