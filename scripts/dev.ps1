# Dev server for llm-usage-metering
$env:LLM_MODE = "mock"
uvicorn backend.main:app --reload --port 8000
