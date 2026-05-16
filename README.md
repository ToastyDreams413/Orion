# Threat Awareness Simulator V4

A browser-based air-and-space threat awareness prototype with:
- Guided and Analyst modes
- 2D tactical view plus optional 3D globe view via CesiumJS (internet needed for the CDN/library)
- physics-flavored propagation for aircraft, drones, ballistic objects, satellites, and a mock close-approach asteroid
- noisy sensor simulation and Kalman-lite tracking
- interpretable threat sub-scores from a C++ engine
- AI anomaly detection using Isolation Forest
- optional public-data enrichment from OpenSky, CelesTrak, and NASA/JPL APIs

## Run

Open a terminal in the project root and run:

```powershell
cmake -S engine -B engine\build
cmake --build engine\build --config Release
pip install -r backend\requirements.txt
python -m uvicorn backend.app.main:app --reload
```

Then open http://127.0.0.1:8000

## Notes

- `engine\build` is generated locally by CMake. This zip does **not** need a prebuilt `build` folder.
- The 3D globe view and live public-data hints work best when the machine running the app has internet access.
- If public APIs are unavailable or rate-limited, the simulator still runs in pure local simulation mode.
- This is a prototype for demonstration and portfolio use. It is not an operational defense system.


## Orion assistants (grounded GPT-4o-mini optional)

Orion has two assistant surfaces:

1. **Project Q&A Bot**: answers how the project was built using retrieved project knowledge.
2. **AI Scenario Advisor**: answers commander-style questions about the live simulation. It now uses a hybrid architecture: deterministic threat/playbook analysis and optional trained policy output are computed first, then an LLM turns that grounded packet into a stronger conversational recommendation when an API key is available. If the LLM is unavailable, Orion falls back to the local advisor so the demo still works.

The Project Q&A panel can run in two modes:

- **Grounded LLM mode** when `OPENAI_API_KEY` is set. Orion retrieves relevant chunks from `backend/app/kb/orion_kb.json` and sends only that grounded context to GPT-4o-mini.
- **Local retrieval mode** when no API key is present. Orion answers directly from the local knowledge base without an LLM.

To enable the LLM version, copy `.env.example` to `.env` and set your OpenAI API key:

```powershell
copy .env.example .env
```

Then edit `.env` and set:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
# Optional: use a different model specifically for the Scenario Advisor
# OPENAI_ADVISOR_MODEL=gpt-4o-mini
```

The Project Q&A assistant is intentionally scope-limited: for unrelated questions it should say the question is outside Orion's scope instead of guessing. The Scenario Advisor is scope-limited to the active simulation state and simulated response categories; it should not invent tracks or provide real-world military instructions.

## Optional: train the AI Advisor policy model

The project runs out of the box with a transparent advisor playbook plus Orion's existing rule/ML fusion scores. With `OPENAI_API_KEY` set, the Scenario Advisor uses the LLM as the front-end reasoning/synthesis layer over that same grounded playbook packet. If you want to show an additional trained model component, you can train a synthetic response-policy model:

```powershell
python -m backend.app.scoring.train_advisor_model
```

That creates:

```text
backend/app/scoring/advisor_policy_model.joblib
```

When that file exists, the Scenario Advisor automatically loads it and reports it as an optional trained Random Forest second opinion. The advisor still keeps the transparent playbook reasoning visible so the demo remains inspectable.

The model is intentionally trained on synthetic simulation policy labels, not real operational doctrine. It is useful for demonstrating an AI workflow: generate synthetic state/action examples, train a classifier, compare the learned recommendation against interpretable rules, and surface disagreement for operator review.

## v48 advisor and global-view notes

- The Scenario Advisor now has a wider local reasoning layer for demo reliability. It handles status/risk questions, score lookups, multi-track comparisons, class-confidence questions, hypothetical missile response questions, locations, timelines, environmental effects, and broad command sitreps.
- The advisor panel shows whether the LLM synthesis layer is active. If `OPENAI_API_KEY` is missing, responses come from the local playbook/ML fallback and may appear immediately.
- The region selector was removed from the top bar because Orion now presents a global operating picture rather than a local-region view.
- 3D objects use SVG billboard graphics again while keeping their name tags and priority styling.
