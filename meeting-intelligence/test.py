#!/usr/bin/env python3
"""
Quick test script to verify NEXUS is ready for demo
"""

import os
import sys

def test_env():
    """Test environment setup"""
    print("🧪 Testing NEXUS Setup...")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print("✅ Python version:", sys.version.split()[0])

    # Check API keys
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')

    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not set")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key'")
        return False
    print("✅ Claude API key found:", anthropic_key[:10] + "...")

    if not openai_key:
        print("⚠️  OpenAI API key not set (will use mock transcription)")
    else:
        print("✅ OpenAI API key found:", openai_key[:10] + "...")

    # Check dependencies
    print("\n📦 Checking dependencies...")
    required = ['flask', 'anthropic', 'openai', 'flask_cors']

    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not installed")
            print(f"   Install with: pip install {package}")
            return False

    print("\n" + "=" * 50)
    print("🎉 All checks passed! Ready to demo!")
    print("=" * 50)
    print("\n🚀 Run: python server.py")
    print("📖 Or: ./start.sh")
    return True

if __name__ == '__main__':
    success = test_env()
    sys.exit(0 if success else 1)
