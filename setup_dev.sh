#!/bin/bash
SERVICES=(
  "services/core/rag-service"
  "services/core/llm-service"
  "services/core/memory-service"
  "services/core/gateway-service"
  "services/core/agent-service"
  "services/agents/weather-agent"
  "services/agents/search-agent"
)

BASE="/home/ali/projects/AI/agentica"

for SERVICE in "${SERVICES[@]}"; do
  SERVICE_PATH="$BASE/$SERVICE"

  # pyrightconfig.json
  cat > "$SERVICE_PATH/pyrightconfig.json" << 'EOF'
{
  "pythonVersion": "3.11",
  "venvPath": ".",
  "venv": "venv",
  "extraPaths": ["."],
  "executionEnvironments": [
    {
      "root": ".",
      "extraPaths": ["."]
    }
  ]
}
EOF

  # .pylintrc
  cat > "$SERVICE_PATH/.pylintrc" << EOF
[MASTER]
init-hook='import sys; sys.path.insert(0, "$SERVICE_PATH")'
EOF

  echo "configured $SERVICE"
done