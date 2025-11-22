#!/bin/bash

# Simple test to verify the setup script syntax
echo "Testing Azure setup script syntax..."

if bash -n scripts/setup_azure_resources.sh; then
    echo "✅ Script syntax is valid"
else
    echo "❌ Script has syntax errors"
    exit 1
fi

echo "✅ Azure setup script is ready to use"
echo "To run: bash scripts/setup_azure_resources.sh"