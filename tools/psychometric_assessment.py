"""
Psychometric Assessment — 20-question personality / aptitude test
Weighted scoring: EQ 30%, AQ 25%, BQ 25%, SQ 20%
"""
import os, json
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()


class PsychometricAssessment:
    """
    Psychometric assessment with 20 scenario-based questions across 4 dimensions:
    - Emotional Quotient (EQ) — empathy, conflict resolution, emotional awareness
    - Adaptability Quotient (AQ) — change tolerance, learning agility, resilience
    - Behavioral Quotient (BQ) — teamwork, communication, ethics
    - Social Quotient (SQ) — leadership, influence, networking
    """

    DIMENSION_WEIGHTS = {'EQ': 0.30, 'AQ': 0.25, 'BQ': 0.25, 'SQ': 0.20}

    QUESTIONS = [
        # ── EQ Questions (1-5) ────────────────────────────
        {'id': 1, 'dimension': 'EQ', 'category': 'Empathy',
         'scenario': "A colleague is visibly upset after receiving negative feedback. "
                     "What would you do?",
         'options': [
             {'text': 'Give them space — they need time alone', 'score': 2},
             {'text': 'Ask if they want to talk and listen without judgment', 'score': 5},
             {'text': 'Tell them to not take it personally', 'score': 1},
             {'text': 'Share a similar experience of yours and how you handled it', 'score': 4}]},
        {'id': 2, 'dimension': 'EQ', 'category': 'Conflict Resolution',
         'scenario': "Two team members have a heated disagreement during a meeting. You are the third member. "
                     "What do you do?",
         'options': [
             {'text': 'Stay quiet and let them sort it out', 'score': 1},
             {'text': 'Suggest a break and speak to each privately afterward', 'score': 5},
             {'text': 'Take the side you agree with', 'score': 2},
             {'text': 'Redirect discussion to facts rather than opinions', 'score': 4}]},
        {'id': 3, 'dimension': 'EQ', 'category': 'Self-awareness',
         'scenario': "You realize you made a significant error in a project. What is your first instinct?",
         'options': [
             {'text': 'Hope no one notices and fix it quietly', 'score': 1},
             {'text': 'Inform your manager immediately with a proposed fix', 'score': 5},
             {'text': 'Blame the unclear requirements', 'score': 0},
             {'text': 'Ask a trusted colleague for advice first', 'score': 3}]},
        {'id': 4, 'dimension': 'EQ', 'category': 'Emotional Management',
         'scenario': "You're under a tight deadline and receive additional urgent tasks. "
                     "How do you react?",
         'options': [
             {'text': 'Feel overwhelmed and complain to coworkers', 'score': 1},
             {'text': 'Prioritize tasks calmly and communicate realistic timelines', 'score': 5},
             {'text': 'Work overtime without telling anyone', 'score': 2},
             {'text': 'Delegate everything possible immediately', 'score': 3}]},
        {'id': 5, 'dimension': 'EQ', 'category': 'Motivation',
         'scenario': "A project you were passionate about gets cancelled. What do you do?",
         'options': [
             {'text': 'Feel demotivated for weeks', 'score': 1},
             {'text': 'Understand the reasons and redirect your energy to new goals', 'score': 5},
             {'text': 'Argue that the project should continue', 'score': 2},
             {'text': 'Start looking for opportunities elsewhere', 'score': 1}]},

        # ── AQ Questions (6-10) ───────────────────────────
        {'id': 6, 'dimension': 'AQ', 'category': 'Change Tolerance',
         'scenario': "Your company switches to a completely new tech stack you've never used. Your reaction?",
         'options': [
             {'text': 'Resist the change and argue for the old stack', 'score': 1},
             {'text': 'Start learning immediately — exciting opportunity', 'score': 5},
             {'text': 'Wait for training to be provided', 'score': 3},
             {'text': 'Focus on transferable concepts between stacks', 'score': 4}]},
        {'id': 7, 'dimension': 'AQ', 'category': 'Learning Agility',
         'scenario': "You need to present on a topic you know little about in 48 hours. What's your plan?",
         'options': [
             {'text': 'Ask someone else to present instead', 'score': 1},
             {'text': 'Immerse yourself: read docs, tutorials, build a demo', 'score': 5},
             {'text': 'Cover only the basics and acknowledge limitations', 'score': 3},
             {'text': 'Use the time to become an expert through focused study', 'score': 4}]},
        {'id': 8, 'dimension': 'AQ', 'category': 'Resilience',
         'scenario': "You've been rejected from a promotion you deserved. How do you proceed?",
         'options': [
             {'text': 'Become disengaged from work', 'score': 0},
             {'text': 'Ask for specific feedback and create a growth plan', 'score': 5},
             {'text': 'Accept it and move on without asking why', 'score': 2},
             {'text': 'Prove yourself by taking on more challenging projects', 'score': 4}]},
        {'id': 9, 'dimension': 'AQ', 'category': 'Problem Solving Under Pressure',
         'scenario': "A critical production system goes down at 11 PM. You're on call. What do you do?",
         'options': [
             {'text': 'Panic and call your manager immediately', 'score': 2},
             {'text': 'Systematically diagnose, document steps, and escalate if needed', 'score': 5},
             {'text': 'Try random fixes until something works', 'score': 1},
             {'text': 'Follow the runbook step by step', 'score': 4}]},
        {'id': 10, 'dimension': 'AQ', 'category': 'Innovation',
         'scenario': "Your manager asks for ideas to improve a process. You think the current process is fine. What do you do?",
         'options': [
             {'text': 'Say it\'s fine as is', 'score': 1},
             {'text': 'Research industry best practices and propose improvements', 'score': 5},
             {'text': 'Ask colleagues for their pain points first', 'score': 4},
             {'text': 'Suggest minor cosmetic changes', 'score': 2}]},

        # ── BQ Questions (11-15) ──────────────────────────
        {'id': 11, 'dimension': 'BQ', 'category': 'Teamwork',
         'scenario': "A team member consistently misses deadlines, affecting your work. What's your approach?",
         'options': [
             {'text': 'Complain to the manager', 'score': 2},
             {'text': 'Have a private conversation to understand their challenges and offer help', 'score': 5},
             {'text': 'Do their work yourself to meet the deadline', 'score': 1},
             {'text': 'Set up regular check-ins to track progress together', 'score': 4}]},
        {'id': 12, 'dimension': 'BQ', 'category': 'Communication',
         'scenario': "You disagree with a technical decision made by a senior engineer. What do you do?",
         'options': [
             {'text': 'Stay quiet — they\'re more experienced', 'score': 1},
             {'text': 'Present your alternative with data/reasoning respectfully', 'score': 5},
             {'text': 'Complain to peers about the decision', 'score': 0},
             {'text': 'Implement their approach but document your concerns', 'score': 3}]},
        {'id': 13, 'dimension': 'BQ', 'category': 'Ethics',
         'scenario': "You discover a colleague is padding their expense reports. What do you do?",
         'options': [
             {'text': 'Ignore it — not your business', 'score': 0},
             {'text': 'Report it through proper channels', 'score': 5},
             {'text': 'Confront the colleague directly', 'score': 3},
             {'text': 'Mention it to your manager casually', 'score': 4}]},
        {'id': 14, 'dimension': 'BQ', 'category': 'Work Ethic',
         'scenario': "You finish your tasks early. There's no immediate work assigned. What do you do?",
         'options': [
             {'text': 'Relax until new work comes in', 'score': 1},
             {'text': 'Proactively ask team members if they need help', 'score': 5},
             {'text': 'Work on personal skill development', 'score': 4},
             {'text': 'Document processes or fix minor issues', 'score': 4}]},
        {'id': 15, 'dimension': 'BQ', 'category': 'Decision Making',
         'scenario': "You have to choose between a quick fix and a proper solution. Deadline is tomorrow.",
         'options': [
             {'text': 'Quick fix now, proper solution never', 'score': 1},
             {'text': 'Quick fix with documented tech debt and a plan to fix properly', 'score': 5},
             {'text': 'Miss the deadline to do it properly', 'score': 3},
             {'text': 'Ask for a deadline extension', 'score': 3}]},

        # ── SQ Questions (16-20) ──────────────────────────
        {'id': 16, 'dimension': 'SQ', 'category': 'Leadership',
         'scenario': "You're leading a project and two approaches are equally valid. How do you decide?",
         'options': [
             {'text': 'Pick the one you prefer', 'score': 2},
             {'text': 'Discuss trade-offs with the team and build consensus', 'score': 5},
             {'text': 'Let the team vote', 'score': 3},
             {'text': 'Ask your manager to decide', 'score': 1}]},
        {'id': 17, 'dimension': 'SQ', 'category': 'Influence',
         'scenario': "You have a great idea but your team is skeptical. How do you convince them?",
         'options': [
             {'text': 'Drop the idea since no one supports it', 'score': 1},
             {'text': 'Build a proof of concept and demonstrate value', 'score': 5},
             {'text': 'Keep pushing in meetings until they agree', 'score': 1},
             {'text': 'Find an ally who can help champion the idea', 'score': 4}]},
        {'id': 18, 'dimension': 'SQ', 'category': 'Networking',
         'scenario': "At a company event, you notice a senior leader you admire. What do you do?",
         'options': [
             {'text': 'Avoid approaching — they\'re too important', 'score': 1},
             {'text': 'Introduce yourself, mention a project you admire, ask a thoughtful question', 'score': 5},
             {'text': 'Ask them directly for career advice', 'score': 2},
             {'text': 'Connect on LinkedIn afterward with a personalized message', 'score': 4}]},
        {'id': 19, 'dimension': 'SQ', 'category': 'Cultural Awareness',
         'scenario': "You join a team with diverse cultural backgrounds. Some members communicate very differently. "
                     "How do you adapt?",
         'options': [
             {'text': 'Expect everyone to adapt to your communication style', 'score': 0},
             {'text': 'Observe, ask about preferences, and adjust your approach', 'score': 5},
             {'text': 'Treat everyone the same regardless', 'score': 2},
             {'text': 'Default to written communication to avoid misunderstanding', 'score': 3}]},
        {'id': 20, 'dimension': 'SQ', 'category': 'Mentoring',
         'scenario': "A new junior developer asks you to help them debug a problem. You're busy. What do you do?",
         'options': [
             {'text': 'Tell them you\'re busy and to figure it out', 'score': 1},
             {'text': 'Schedule 15 minutes, teach them debugging approach rather than just fixing it', 'score': 5},
             {'text': 'Fix it for them quickly', 'score': 2},
             {'text': 'Point them to relevant documentation', 'score': 3}]},
    ]

    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.answers: Dict[int, int] = {}

    def get_questions(self) -> List[Dict]:
        """Return all questions (options shuffled order preserved for scoring)."""
        return self.QUESTIONS

    def get_question_by_id(self, qid: int) -> Dict:
        for q in self.QUESTIONS:
            if q['id'] == qid:
                return q
        return {}

    def submit_answer(self, question_id: int, option_index: int) -> Dict:
        """Record an answer (option_index 0-3)."""
        q = self.get_question_by_id(question_id)
        if not q:
            return {'status': 'error', 'message': 'Invalid question ID'}
        if not (0 <= option_index < len(q['options'])):
            return {'status': 'error', 'message': 'Invalid option index'}
        self.answers[question_id] = option_index
        return {
            'status': 'success', 'question_id': question_id,
            'answered': len(self.answers), 'total': len(self.QUESTIONS)
        }

    def calculate_results(self) -> Dict:
        """Calculate weighted final score with AI-generated feedback."""
        if len(self.answers) < len(self.QUESTIONS):
            return {'status': 'incomplete',
                    'answered': len(self.answers), 'total': len(self.QUESTIONS)}

        dimension_scores = {'EQ': [], 'AQ': [], 'BQ': [], 'SQ': []}

        for q in self.QUESTIONS:
            idx = self.answers.get(q['id'])
            if idx is not None:
                score = q['options'][idx]['score']
                dimension_scores[q['dimension']].append(score)

        # Normalize each dimension to 0-100
        dim_results = {}
        for dim, scores in dimension_scores.items():
            max_possible = 5 * len(scores)  # each question max 5
            raw = sum(scores)
            percentage = (raw / max_possible * 100) if max_possible else 0
            dim_results[dim] = {
                'raw_score': raw, 'max_score': max_possible,
                'percentage': round(percentage, 1), 'count': len(scores)
            }

        # Weighted overall
        weighted_total = sum(
            dim_results[dim]['percentage'] * self.DIMENSION_WEIGHTS[dim]
            for dim in self.DIMENSION_WEIGHTS
        )

        ai_feedback = self._generate_ai_feedback(dim_results, weighted_total)

        return {
            'status': 'complete',
            'overall_score': round(weighted_total, 1),
            'dimensions': {
                'emotional_quotient': dim_results['EQ'],
                'adaptability_quotient': dim_results['AQ'],
                'behavioral_quotient': dim_results['BQ'],
                'social_quotient': dim_results['SQ'],
            },
            'dimension_weights': self.DIMENSION_WEIGHTS,
            'ai_feedback': ai_feedback,
            'total_questions': len(self.QUESTIONS),
            'answers_given': len(self.answers),
        }

    def _generate_ai_feedback(self, dimensions: Dict, overall: float) -> Dict:
        """Use Groq AI to provide personalized feedback."""
        prompt = (
            f"Candidate psychometric results:\n"
            f"Overall: {overall:.1f}/100\n"
            f"EQ: {dimensions['EQ']['percentage']:.1f}%\n"
            f"AQ: {dimensions['AQ']['percentage']:.1f}%\n"
            f"BQ: {dimensions['BQ']['percentage']:.1f}%\n"
            f"SQ: {dimensions['SQ']['percentage']:.1f}%\n\n"
            "Provide JSON:\n"
            '{"summary":"2 sentence overall","strengths":["top 2"],'
            '"development_areas":["top 2"],"team_fit":"1 sentence",'
            '"leadership_potential":"1 sentence"}'
        )
        try:
            resp = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Expert organizational psychologist. Be constructive."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.5, max_tokens=500
            )
            return json.loads(resp.choices[0].message.content)
        except Exception:
            return {
                'summary': f'Score: {overall:.1f}/100. See dimension breakdown.',
                'strengths': [], 'development_areas': [],
                'team_fit': 'Review with HR', 'leadership_potential': 'Review with HR'
            }

    def get_dimension_descriptions(self) -> Dict:
        return {
            'EQ': 'Emotional Quotient — empathy, conflict resolution, self-awareness, emotional management',
            'AQ': 'Adaptability Quotient — change tolerance, learning agility, resilience, innovation',
            'BQ': 'Behavioral Quotient — teamwork, communication, ethics, work ethic, decision making',
            'SQ': 'Social Quotient — leadership, influence, networking, cultural awareness, mentoring',
        }
