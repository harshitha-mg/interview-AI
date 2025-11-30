#!/bin/bash
# Run FastAPI backend on port 8000
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Run Streamlit frontend on port 8501
streamlit run streamlit_app.py --server.port 8501 --server.headless true --server.address 0.0.0.0
