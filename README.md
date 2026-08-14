# Crew Lead Agent

A V1 airline crew disruption decision-support prototype for crew operations.

## What this project does

This project helps a Crew Lead analyze a disruption scenario by:

- identifying the affected flight and crew
- checking crew availability and role fit
- checking duty-time risk and legal feasibility at a prototype level
- finding eligible replacement crew
- evaluating downstream crew impact
- recommending the best operational recovery option
- exposing the workflow through a FastAPI backend and a Streamlit UI

This is a decision-support system, not a system that automatically executes operational changes.

## Core business problem

When a disruption occurs, the Crew Lead needs to quickly understand:

- which flight is affected
- which crew members are involved
- what downstream flights are at risk
- which replacement crew can legally and operationally cover the issue
- what the best recovery option is before the issue escalates

## V1 scope

The first working version focuses on these scenarios:

1. Crew unavailable
2. Duty-time / legality risk
3. Flight delay causing downstream crew conflict
4. Best replacement crew selection

## Architecture

The project is structured in four layers:

- Data layer: dummy airline operational data in CSV files
- Rule engine: deterministic crew availability, qualification, duty, schedule checks
- Agent workflow: LangGraph-style orchestration in the workflow and graph layers
- Interface layer: FastAPI API and Streamlit frontend

## Project structure

- src/crew_lead/workflow.py: deterministic crew disruption logic and recommendation engine
- src/crew_lead/graph.py: graph orchestration for the disruption workflow
- src/crew_lead/agent.py: LLM-based agent with operational tools
- src/crew_lead/tools/: supporting data lookup and operational tools
- data/: dummy flight, crew, assignment, and standby data
- api.py: FastAPI backend
- main.py: alternate app entry for API
- frontend.py: Streamlit crew lead UI
- tests/test_v1_workflow.py: validation tests for the V1 flow

## Setup

From the project root:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

The repository includes `requirements.txt` for the Python services.

## Run the backend

```bash
uvicorn api:app --reload
```

or:

```bash
uvicorn main:app --reload
```

## Run the Streamlit frontend

```bash
streamlit run frontend.py
```

## Run the Bolt React UI with the Python backend

The React UI is in `project/` and uses the Python API as its data source.
The Vite development proxy forwards `/api/*` to `http://127.0.0.1:8000`.

Terminal 1 - backend from the project root:

```bash
uvicorn api:app --reload
```

Terminal 2 - Bolt UI:

```bash
cd project
npm install
npm run dev
```

The UI reads `/api/ui/flights`, `/api/ui/crew`, `/api/ui/disruptions`,
`/api/ui/issues`, and `/api/ui/analyze` through the proxy. To point a
production build at another backend, set `VITE_API_BASE_URL`, for example:

```bash
VITE_API_BASE_URL=https://your-api.example.com npm run build
```

## Example API calls

### Health check

```bash
curl http://127.0.0.1:8000/health
```

### Assess a flight

```bash
curl http://127.0.0.1:8000/assess/6E123
```

### Ask a question

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"message":"Assess flight 6E123"}'
```

## Validation

The V1 workflow is tested using pytest.

```bash
.venv\Scripts\python.exe -m pytest tests/test_v1_workflow.py -q
```

Current verification result:

```text
4 passed in 0.11s
```

## Important limitation

This is a prototype using dummy operational data. It does not yet connect to real airline systems or a production crew legality engine. It is intended to demonstrate the decision-support workflow and recovery reasoning process.

## Final status

The project is complete as a working V1 Crew Lead Agent prototype for crew disruption assessment and recovery recommendation.
