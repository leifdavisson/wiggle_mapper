#!/bin/bash
# Wiggle Mapper Automated Integration Test Script

# Move to script directory's parent to ensure paths are correct
cd "$(dirname "$0")/.."

echo "=================================================="
echo "      Wiggle Mapper Automated Testing Tool"
echo "=================================================="

# Port to run test server on
PORT=8002

# 1. Start Python local HTTP server
echo "Starting local Python HTTP server on port $PORT..."
python3 -m http.server $PORT > /dev/null 2>&1 &
SERVER_PID=$!

# Ensure server cleanup on exit/interruption
trap "echo 'Stopping Python test server...'; kill $SERVER_PID 2>/dev/null; exit" INT TERM EXIT

sleep 2 # Let the server bind

# Check if server is running
if ! ps -p $SERVER_PID > /dev/null; then
    echo "❌ Error: Failed to start Python test server."
    exit 1
fi

echo "✓ Test server running successfully."
echo "--------------------------------------------------"

# 2. Execute Demo Load Test
echo "Running Demo Load Test..."
google-chrome --headless=old --disable-gpu --enable-logging=stderr --virtual-time-budget=6000 "http://localhost:$PORT/index.html?demo=true" > demo_test.log 2>&1

# 3. Execute Large CSV Parse Test
echo "Running Large CSV Parse Test (data/WigleWifi_20260810103955.csv)..."
google-chrome --headless=old --disable-gpu --enable-logging=stderr --virtual-time-budget=10000 "http://localhost:$PORT/index.html?test_file=data/WigleWifi_20260810103955.csv" > parse_test.log 2>&1

# --------------------------------------------------
# 4. Analyze Results
# --------------------------------------------------
echo "--------------------------------------------------"
echo "Analyzing test logs..."

FAILED=0

# Helper function to check log for errors
check_log() {
    local log_file=$1
    local test_name=$2
    local success_pattern=$3

    # Check for Javascript errors
    if grep -Ei "TypeError|ReferenceError|SyntaxError|TEST_ERROR" "$log_file" > /dev/null; then
        echo "❌ $test_name failed: Found runtime errors in console logs."
        grep -Ei "TypeError|ReferenceError|SyntaxError|TEST_ERROR" "$log_file"
        FAILED=1
        return
    fi

    # Check for success pattern if provided
    if [ -n "$success_pattern" ]; then
        if ! grep -q "$success_pattern" "$log_file"; then
            echo "❌ $test_name failed: Expected logs ('$success_pattern') not found."
            FAILED=1
            return
        fi
    fi

    echo "✓ $test_name PASSED."
}

check_log "demo_test.log" "Demo Load Test" ""
check_log "parse_test.log" "Large CSV Parse Test" "TEST_SUCCESS: Loaded 43364 points"

# 5. Cleanup log files if successful
if [ $FAILED -eq 0 ]; then
    echo "=================================================="
    echo "🎉 ALL TESTS PASSED SUCCESSFULLY!"
    echo "=================================================="
    rm -f demo_test.log parse_test.log
else
    echo "=================================================="
    echo "❌ TESTS FAILED. Inspect 'demo_test.log' and 'parse_test.log' for details."
    echo "=================================================="
    exit 1
fi
