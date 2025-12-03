#!/bin/bash
echo "============================================"
echo "🎬 NEXUS LIVE DEMO"
echo "============================================"
echo ""
echo "Opening demo in your browser..."
echo ""
echo "📍 Demo URL: file://$(pwd)/demo-offline.html"
echo ""
echo "You should see:"
echo "✅ Beautiful NEXUS dashboard"
echo "✅ Real meeting transcript"
echo "✅ Auto-analysis with persistent memory"
echo "✅ The UNIQUE 'Connections to Past' feature"
echo ""
echo "============================================"

# Try to open in browser
if command -v xdg-open &> /dev/null; then
    xdg-open demo-offline.html
elif command -v open &> /dev/null; then
    open demo-offline.html
else
    echo "Please open this file in your browser:"
    echo "$(pwd)/demo-offline.html"
fi
