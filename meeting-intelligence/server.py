#!/usr/bin/env python3
"""
NEXUS - Meeting Intelligence with Persistent Memory
Flask backend with Claude API + Whisper API integration
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import anthropic
import openai
import json
import os
from datetime import datetime
import hashlib

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# API Keys
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Initialize Claude client
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Simple in-memory storage (for demo purposes)
MEETINGS_DB = []
TEAM_CONTEXT = {
    "team_type": "engineering",
    "current_sprint": "Sprint 23",
    "ongoing_projects": [
        "Database optimization",
        "User authentication refactor",
        "API rate limiting implementation"
    ],
    "team_members": [
        {"name": "Mike", "role": "Backend Lead"},
        {"name": "Sarah", "role": "Frontend Developer"},
        {"name": "Alex", "role": "DevOps Engineer"},
        {"name": "Jamie", "role": "QA Engineer"}
    ],
    "tech_stack": ["Python", "React", "PostgreSQL", "Redis", "AWS"]
}


def transcribe_audio(audio_file):
    """Transcribe audio using Whisper API"""
    if not OPENAI_API_KEY:
        # Mock transcription for demo
        return """
Mike: Alright team, let's start our standup. Sarah, how's the frontend refactor going?

Sarah: I'm making good progress on the authentication UI. I should have the login page done by tomorrow. But I'm blocked on the API endpoints - they're still returning 500 errors.

Alex: Yeah, sorry about that. The database migration didn't go smoothly yesterday. I'm working on fixing the connection pool issues we discussed last week.

Mike: Wait, didn't we already fix connection pool issues in Sprint 21?

Alex: That was for the read replicas. This is for the main database. Different issue.

Jamie: I've noticed the response times are way higher than last sprint. Is that related?

Alex: Probably. Once I fix the connection pool, it should improve.

Mike: Okay. Sarah, can you document the API errors you're seeing? Alex, let's make the database fix priority one.

Sarah: Will do. I'll also start working on the password reset flow while I wait.

Mike: Good. Jamie, anything blocking you?

Jamie: Nope, I'm writing tests for the new rate limiting feature. Should be done by Friday.

Mike: Perfect. Let's regroup tomorrow. Thanks everyone!
"""

    try:
        openai.api_key = OPENAI_API_KEY
        with open(audio_file, 'rb') as f:
            transcript = openai.Audio.transcribe("whisper-1", f)
        return transcript['text']
    except Exception as e:
        print(f"Transcription error: {e}")
        return None


def analyze_meeting_with_claude(transcript, past_meetings):
    """Analyze meeting using Claude API with team context and memory"""

    # Build context from past meetings
    past_context = ""
    if past_meetings:
        past_context = "\n\n## PAST MEETINGS CONTEXT:\n"
        for i, meeting in enumerate(past_meetings[-3:], 1):  # Last 3 meetings
            past_context += f"\n### Meeting {i} ({meeting['date']}):\n"
            past_context += f"Summary: {meeting.get('summary', 'N/A')}\n"
            if meeting.get('action_items'):
                past_context += f"Action Items: {json.dumps(meeting['action_items'], indent=2)}\n"
            if meeting.get('decisions'):
                past_context += f"Decisions: {json.dumps(meeting['decisions'], indent=2)}\n"

    # Build the comprehensive prompt
    prompt = f"""You are NEXUS, an intelligent meeting analyst for engineering teams with PERSISTENT MEMORY.

## YOUR UNIQUE CAPABILITY:
Unlike basic transcription tools, you REMEMBER past meetings and understand the team's ongoing context.

## TEAM CONTEXT:
- Team Type: {TEAM_CONTEXT['team_type']}
- Current Sprint: {TEAM_CONTEXT['current_sprint']}
- Ongoing Projects: {', '.join(TEAM_CONTEXT['ongoing_projects'])}
- Tech Stack: {', '.join(TEAM_CONTEXT['tech_stack'])}
- Team Members: {json.dumps(TEAM_CONTEXT['team_members'], indent=2)}

{past_context}

## CURRENT MEETING TRANSCRIPT:
{transcript}

## YOUR TASK:
Analyze this meeting and provide:

1. **Executive Summary** (2-3 sentences)

2. **Action Items** (extract ALL commitments with):
   - Who is responsible
   - What needs to be done
   - When (deadline/timeline)
   - Context (why this matters)

3. **Key Decisions Made**

4. **Blockers & Dependencies** (what's blocking progress)

5. **Technical Context** (engineering-specific details)

6. **Connections to Past Meetings** (THIS IS YOUR SUPERPOWER):
   - What was discussed before about these topics?
   - Are there recurring issues?
   - Which action items from past meetings relate to today's discussion?
   - Any conflicting decisions or changed priorities?

7. **Unspoken Concerns** (read between the lines):
   - What might be missing from the discussion?
   - Any risks not explicitly mentioned?

8. **Meeting Efficiency Score** (1-10):
   - Rate how productive this meeting was
   - Suggest improvements

Return your analysis as a JSON object with this structure:
{{
    "summary": "...",
    "action_items": [
        {{
            "assignee": "...",
            "task": "...",
            "deadline": "...",
            "priority": "high|medium|low",
            "context": "..."
        }}
    ],
    "decisions": ["..."],
    "blockers": [
        {{
            "blocker": "...",
            "affects": "...",
            "suggested_resolution": "..."
        }}
    ],
    "technical_details": {{
        "technologies_mentioned": [],
        "architecture_discussions": "",
        "code_or_systems_affected": []
    }},
    "connections_to_past": [
        {{
            "topic": "...",
            "past_meeting_reference": "...",
            "insight": "...",
            "pattern": "recurring_issue|follow_up|contradiction|progress"
        }}
    ],
    "unspoken_concerns": ["..."],
    "efficiency_score": {{
        "score": 8,
        "reasoning": "...",
        "improvements": ["..."]
    }}
}}
"""

    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract JSON from response
        response_text = message.content[0].text

        # Try to parse JSON from the response
        # Claude might wrap it in markdown code blocks
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        analysis = json.loads(json_str)
        return analysis

    except Exception as e:
        print(f"Claude API error: {e}")
        return {
            "error": str(e),
            "summary": "Analysis failed"
        }


@app.route('/')
def index():
    """Serve the main page"""
    return app.send_static_file('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_meeting():
    """Main endpoint: Analyze a meeting transcript"""

    try:
        data = request.get_json()
        transcript = data.get('transcript', '')

        if not transcript:
            # Check if audio file was uploaded
            if 'audio' in request.files:
                audio_file = request.files['audio']
                # Save temporarily
                temp_path = f"/tmp/{hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()}.mp3"
                audio_file.save(temp_path)
                transcript = transcribe_audio(temp_path)
                os.remove(temp_path)
            else:
                return jsonify({"error": "No transcript or audio provided"}), 400

        # Analyze with Claude using past meetings context
        analysis = analyze_meeting_with_claude(transcript, MEETINGS_DB)

        # Store this meeting in our "database"
        meeting_record = {
            "id": len(MEETINGS_DB) + 1,
            "date": datetime.now().isoformat(),
            "transcript": transcript,
            "analysis": analysis,
            "summary": analysis.get('summary', ''),
            "action_items": analysis.get('action_items', []),
            "decisions": analysis.get('decisions', [])
        }
        MEETINGS_DB.append(meeting_record)

        return jsonify({
            "success": True,
            "meeting_id": meeting_record["id"],
            "analysis": analysis,
            "context_used": {
                "past_meetings_count": len(MEETINGS_DB) - 1,
                "team_context": TEAM_CONTEXT
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/meetings', methods=['GET'])
def get_meetings():
    """Get all past meetings"""
    return jsonify({
        "meetings": [
            {
                "id": m["id"],
                "date": m["date"],
                "summary": m.get("summary", "")
            }
            for m in MEETINGS_DB
        ]
    })


@app.route('/api/meeting/<int:meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    """Get a specific meeting"""
    meeting = next((m for m in MEETINGS_DB if m["id"] == meeting_id), None)
    if meeting:
        return jsonify(meeting)
    return jsonify({"error": "Meeting not found"}), 404


@app.route('/api/demo', methods=['POST'])
def quick_demo():
    """Quick demo with pre-populated data"""

    # Add some past meetings to show memory
    if len(MEETINGS_DB) == 0:
        past_meeting_1 = {
            "id": 1,
            "date": "2024-11-26T10:00:00",
            "summary": "Sprint 22 planning - Discussed database connection pool issues causing 500 errors in production. Mike assigned Alex to investigate and fix by end of sprint.",
            "action_items": [
                {
                    "assignee": "Alex",
                    "task": "Fix database connection pool issues",
                    "deadline": "End of Sprint 22",
                    "priority": "high"
                }
            ],
            "decisions": ["Prioritize database stability over new features"]
        }

        past_meeting_2 = {
            "id": 2,
            "date": "2024-11-29T14:00:00",
            "summary": "Frontend sync - Sarah reported API endpoints returning errors. Authentication refactor blocked until backend issues resolved.",
            "action_items": [
                {
                    "assignee": "Sarah",
                    "task": "Document API errors for backend team",
                    "deadline": "Next standup",
                    "priority": "medium"
                }
            ],
            "decisions": ["Sarah will work on frontend components that don't require API while waiting"]
        }

        MEETINGS_DB.extend([past_meeting_1, past_meeting_2])

    # Now analyze the current meeting
    return analyze_meeting()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "claude_api": "configured" if ANTHROPIC_API_KEY else "missing",
        "whisper_api": "configured" if OPENAI_API_KEY else "missing (using mock)",
        "meetings_stored": len(MEETINGS_DB)
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 NEXUS - Meeting Intelligence Server")
    print("=" * 60)
    print(f"Claude API: {'✅ Configured' if ANTHROPIC_API_KEY else '❌ Missing'}")
    print(f"Whisper API: {'✅ Configured' if OPENAI_API_KEY else '⚠️  Using mock transcription'}")
    print("\n📡 Server starting on http://localhost:5000")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
