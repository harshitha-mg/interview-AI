#!/bin/bash
set -e

echo "Render provided PORT=$PORT"

# Start FastAPI backend on internal port 8000
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit on the external port Render expects
streamlit run streamlit_app.py \
  --server.port $PORT \
  --server.headless true \
  --server.address 0.0.0.0
