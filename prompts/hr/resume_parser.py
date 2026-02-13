"""Prompts for resume parsing"""

SYSTEM_PROMPT = "Expert resume parser. Return valid JSON only."

def parse_prompt(resume_text):
    return (
        f"Analyze this resume:\n\n{resume_text[:3000]}\n\n"
        'Return JSON: {"skills":["..."],"experience_years":<int>,'
        '"education":"Bachelor\'s Degree|Master\'s Degree|PhD|Diploma|High School|Not Specified"}'
    )
