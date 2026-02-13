# tools package — import all tool modules with graceful fallbacks

from tools.email_service import EmailService
from tools.local_executor import LocalPythonExecutor
from tools.code_executor import CodeExecutor
from tools.ai_code_analyzer import AICodeAnalyzer
from tools.technical_interview_chat import TechnicalInterviewChat
from tools.psychometric_assessment import PsychometricAssessment
from tools.interview_storage import InterviewStorage

# Optional heavy-dependency tools
try:
    from tools.video_analyzer import VideoConfidenceAnalyzer, analyze_candidate_video
    VIDEO_ANALYZER_AVAILABLE = True
except ImportError:
    VIDEO_ANALYZER_AVAILABLE = False

try:
    from tools.video_analyzer_hybrid import HybridVideoAnalyzer, analyze_candidate_video_ai
    HYBRID_VIDEO_AVAILABLE = True
except ImportError:
    HYBRID_VIDEO_AVAILABLE = False

__all__ = [
    'EmailService',
    'LocalPythonExecutor',
    'CodeExecutor',
    'AICodeAnalyzer',
    'TechnicalInterviewChat',
    'PsychometricAssessment',
    'InterviewStorage',
    'VIDEO_ANALYZER_AVAILABLE',
    'HYBRID_VIDEO_AVAILABLE',
]
