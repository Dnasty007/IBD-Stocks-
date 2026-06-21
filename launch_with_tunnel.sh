#!/usr/bin/env bash
# Launch Streamlit with a public tunnel for mobile access
# Usage: bash launch_with_tunnel.sh

set -e

PORT=${PORT:-8501}

echo "Starting Streamlit on port $PORT..."
streamlit run app.py --server.port="$PORT" --server.address=0.0.0.0 --server.headless=true &
STREAMLIT_PID=$!
sleep 5

if ! curl -s "http://localhost:$PORT/_stcore/health" | grep -q ok; then
    echo "ERROR: Streamlit failed to start"
    kill $STREAMLIT_PID 2>/dev/null
    exit 1
fi

echo "Streamlit is running on http://localhost:$PORT"
echo ""
echo "Starting public tunnel..."
npx --yes localtunnel --port "$PORT" &
TUNNEL_PID=$!
sleep 8

echo ""
echo "==================================="
echo " Local:  http://localhost:$PORT"
echo " Share the public URL above with any device"
echo "==================================="
echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $STREAMLIT_PID $TUNNEL_PID 2>/dev/null; exit 0" INT TERM
wait
