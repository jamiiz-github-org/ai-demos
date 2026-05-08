#!/bin/bash
# Quick-start script for local development.
# Usage: cd backend && bash start.sh

set -e

if [ ! -f ".env" ]; then
  echo "No .env file found. Copying from .env.example..."
  cp .env.example .env
  echo "Edit backend/.env with your API keys, then run this script again."
  exit 1
fi

echo "Starting Jamiiz AI Demo Lab..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
