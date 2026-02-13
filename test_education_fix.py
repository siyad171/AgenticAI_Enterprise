"""
Quick test to verify education matching fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agents.hr_agent import HRAgent
from core.database import Database
from core.llm_service import LLMService

# Initialize
db = Database()
llm = LLMService()
hr_agent = HRAgent(db, llm)

# Test the _normalize_education_level function
print("=== Testing Education Level Normalization ===\n")

test_cases = [
    ("Bachelor's Degree", 3),
    ("Bachelor's in Computer Science or related field", 3),
    ("Master's Degree", 4),
    ("PhD", 5),
    ("High School", 1),
    ("Diploma", 2),
    ("Not Specified", 0),
]

for education_text, expected_level in test_cases:
    level = hr_agent._normalize_education_level(education_text)
    status = "✓" if level == expected_level else "✗"
    print(f"{status} '{education_text}' → Level {level} (expected {expected_level})")

# Test the specific case from user's scenario
print("\n=== Testing User's Scenario ===\n")
candidate_edu = "Bachelor's Degree"
job_requirement = "Bachelor's in Computer Science or related field"

candidate_level = hr_agent._normalize_education_level(candidate_edu)
required_level = hr_agent._normalize_education_level(job_requirement)
edu_met = candidate_level >= required_level

print(f"Candidate education: '{candidate_edu}' → Level {candidate_level}")
print(f"Job requirement: '{job_requirement}' → Level {required_level}")
print(f"Education Met: {edu_met} {'✓ PASS' if edu_met else '✗ FAIL'}")

# Calculate what the new score would be (without penalty)
print("\n=== Score Impact ===\n")
skill_match_pct = 71.43  # From the user's image
old_score_with_penalty = 57.14  # 71.43 * 0.8
new_score_no_penalty = skill_match_pct  # No education penalty applied

print(f"Old Score (with education penalty): {old_score_with_penalty}%")
print(f"New Score (education met, no penalty): {new_score_no_penalty}%")
print(f"Improvement: +{new_score_no_penalty - old_score_with_penalty:.2f}%")
