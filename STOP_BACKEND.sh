#!/bin/bash

# Kill backend process running on port 8000
echo "🛑 Stopping backend on port 8000..."

PID=$(lsof -ti:8000)

if [ -z "$PID" ]; then
    echo "✅ No process running on port 8000"
else
    kill -9 $PID
    echo "✅ Killed process $PID"
fi
