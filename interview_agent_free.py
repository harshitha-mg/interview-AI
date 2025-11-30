import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import re
from typing import Dict, List, Any, Tuple
from collections import Counter
import random

# Download required NLTK data
try:
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)
except:
    pass

class FreeInterviewAgent:
    def __init__(self):
        print("Loading AI models...")
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        print("AI models loaded successfully!")
        
        # Non-answer indicators - responses that indicate the user doesn't know
        self.non_answer_indicators = [
            "i don't know", "i do not know", "no idea", "not sure", "don't know",
            "idk", "nope", "no", "nothing", "none", "can't answer", "cannot answer",
            "no answer", "skip", "pass", "next", "i have no", "no experience",
            "never done", "never did", "haven't done", "have not done", "n/a",
            "not applicable", "sorry", "i'm not", "i am not", "no clue"
        ]
        
        # Category-specific keywords
        self.category_keywords = {
            "technical": {
                "keywords": ["algorithm", "code", "programming", "database", "system", "design", "debug", "test", 
                           "framework", "api", "cloud", "security", "performance", "optimization", "architecture",
                           "software", "development", "application", "interface", "protocol", "object", "class",
                           "function", "method", "variable", "loop", "inheritance", "polymorphism",
                           "encapsulation", "abstraction", "implementation", "deployment", "server",
                           "python", "java", "javascript", "html", "css", "react", "node", "docker",
                           "aws", "azure", "git", "agile", "scrum", "devops", "testing", "data",
                           "backend", "frontend", "fullstack", "web", "mobile", "app", "sql", "nosql",
                           "microservices", "rest", "graphql", "kubernetes", "ci", "cd", "pipeline"],
                "weight": 1.0
            },
            "behavioral": {
                "keywords": ["team", "leadership", "challenge", "problem", "solution", "experience", "learn", 
                           "improve", "conflict", "communication", "collaboration", "feedback", "success", "failure",
                           "project", "deadline", "pressure", "adapt", "change", "resolution", "situation",
                           "example", "story", "scenario", "outcome", "result", "achievement", "accomplishment",
                           "worked", "managed", "led", "organized", "coordinated", "resolved",
                           "achieved", "delivered", "implemented", "created", "developed", "improved", "solved",
                           "helped", "supported", "mentored", "trained", "guided", "motivated"],
                "weight": 0.9
            },
            "management": {
                "keywords": ["lead", "manage", "team", "strategy", "plan", "delegate", "motivate", "performance",
                           "budget", "resource", "project", "stakeholder", "decision", "vision", "goal",
                           "direction", "coordinate", "evaluate", "mentor", "develop", "guide", "supervise",
                           "oversee", "responsible", "accountable", "initiative", "roadmap",
                           "kpi", "metric", "efficiency", "productivity", "timeline", "milestone",
                           "hiring", "training", "career", "growth", "retention", "leadership",
                           "executive", "director", "manager", "supervisor", "coordinator"],
                "weight": 0.95
            },
            "sales": {
                "keywords": ["client", "customer", "sale", "relationship", "pipeline", "revenue", "negotiate",
                           "objection", "metric", "campaign", "market", "competitor", "proposal", "close", "deal",
                           "growth", "partnership", "retention", "acquisition", "demo", "presentation",
                           "pitch", "value", "benefit", "solution", "need", "requirement",
                           "roi", "conversion", "lead", "prospect", "qualify", "follow-up",
                           "trust", "credibility", "expertise", "consultative", "target", "quota"],
                "weight": 0.9
            }
        }
        
        # Question templates - 20 per category
        self.question_templates = {
            "technical": [
                "Explain the concept of object-oriented programming and its main principles.",
                "What are the main differences between SQL and NoSQL databases?",
                "How would you approach debugging a complex performance issue?",
                "Describe your experience with cloud platforms and services.",
                "What are the key considerations when designing a scalable system?",
                "How do you ensure code quality and maintainability?",
                "What experience do you have with version control systems?",
                "How do you handle software testing and quality assurance?",
                "Describe your experience with RESTful APIs.",
                "What's your approach to learning new technologies?",
                "How do you optimize application performance?",
                "What security best practices do you follow?",
                "Describe your experience with database design.",
                "How do you approach code reviews?",
                "What's your experience with agile methodologies?",
                "How do you handle technical debt?",
                "Describe a challenging technical problem you solved.",
                "What's your experience with containerization?",
                "How do you stay updated with technology trends?",
                "What metrics do you track for application performance?"
            ],
            "behavioral": [
                "Tell me about a time you faced a significant challenge and how you overcame it.",
                "Describe a situation where you had to work with a difficult team member.",
                "How do you prioritize tasks with multiple tight deadlines?",
                "Give an example of a time you made a mistake and what you learned.",
                "Describe a project where you demonstrated leadership.",
                "How do you handle receiving critical feedback?",
                "Tell me about a time you had to adapt to significant changes.",
                "Describe a situation where you persuaded others to adopt your idea.",
                "How do you handle disagreements with your manager?",
                "Tell me about a time you went above and beyond.",
                "Describe a decision you made with incomplete information.",
                "How do you build relationships with new team members?",
                "Tell me about a time you failed and what you learned.",
                "Describe how you manage conflicting priorities.",
                "How do you handle stress and pressure?",
                "Tell me about your biggest professional achievement.",
                "Describe a time you received negative feedback.",
                "How do you approach continuous learning?",
                "Tell me about a time you had to learn something quickly.",
                "Describe a situation where you stood up for what was right."
            ],
            "management": [
                "What's your approach to delegating tasks to team members?",
                "How do you handle underperforming team members?",
                "Describe your experience with project planning.",
                "What strategies do you use to motivate your team?",
                "How do you measure project success?",
                "Describe a difficult decision you made as a manager.",
                "How do you set goals and expectations for your team?",
                "What's your experience with budget management?",
                "How do you handle conflicts between team members?",
                "Describe your approach to performance reviews.",
                "What strategies do you use for risk management?",
                "How do you balance technical and people management?",
                "Describe your experience with hiring and building teams.",
                "How do you foster innovation in your team?",
                "What's your approach to stakeholder management?",
                "How do you handle scope changes in projects?",
                "Describe your experience with cross-functional teams.",
                "How do you ensure team alignment with company goals?",
                "What metrics do you track for team performance?",
                "How do you mentor and develop junior team members?"
            ],
            "sales": [
                "How do you approach building relationships with new clients?",
                "Describe your process for managing a sales pipeline.",
                "What strategies do you use to handle customer objections?",
                "How do you stay informed about industry trends?",
                "Describe your most successful sales campaign.",
                "What key metrics do you track for sales performance?",
                "How do you identify and qualify new leads?",
                "Describe your experience with CRM systems.",
                "How do you tailor your approach for different customers?",
                "What's your strategy for maintaining client relationships?",
                "How do you handle price negotiations?",
                "Describe a time you lost a major deal and what you learned.",
                "How do you differentiate from competitors?",
                "What's your approach to sales presentations?",
                "How do you handle rejection and maintain motivation?",
                "Describe your experience with contract negotiation.",
                "How do you collaborate with marketing teams?",
                "What's your strategy for upselling to existing clients?",
                "How do you use data to improve sales performance?",
                "Describe your approach to sales forecasting."
            ]
        }

    def generate_questions(self, category: str, count: int = 8) -> List[str]:
        """Generate 8 random questions from the 20 available per category"""
        try:
            if category not in self.question_templates:
                category = "technical"
            
            all_questions = self.question_templates[category]
            selected_questions = random.sample(all_questions, min(count, len(all_questions)))
            
            print(f"Selected {len(selected_questions)} questions for {category} category")
            return selected_questions
            
        except Exception as e:
            print(f"Error generating questions: {e}")
            return self._get_fallback_questions(category, count)

    def _is_non_answer(self, response: str) -> bool:
        """Check if the response is a non-answer (user doesn't know)"""
        response_lower = response.lower().strip()
        
        # Check for very short responses
        if len(response_lower) < 10:
            return True
        
        # Check word count
        word_count = len(response_lower.split())
        if word_count < 5:
            return True
        
        # Check for non-answer indicators
        for indicator in self.non_answer_indicators:
            if indicator in response_lower:
                # Make sure it's a significant part of the response
                if len(response_lower) < 50 or response_lower.startswith(indicator):
                    return True
        
        return False

    def _get_response_quality(self, response: str, category: str) -> str:
        """Determine the quality level of a response"""
        response_lower = response.lower().strip()
        word_count = len(response.split())
        
        # Check for non-answer
        if self._is_non_answer(response):
            return "non_answer"
        
        # Check for very short responses
        if word_count < 15:
            return "very_short"
        
        # Check for short responses
        if word_count < 30:
            return "short"
        
        # Count keywords
        keywords = self.category_keywords.get(category, {}).get("keywords", [])
        keyword_matches = sum(1 for kw in keywords if kw in response_lower)
        
        # Determine quality
        if word_count >= 80 and keyword_matches >= 3:
            return "excellent"
        elif word_count >= 50 and keyword_matches >= 2:
            return "good"
        elif word_count >= 30:
            return "adequate"
        else:
            return "short"

    def analyze_response(self, question: str, response: str, category: str) -> Dict[str, Any]:
        """Analyze candidate response with ACCURATE scoring"""
        try:
            word_count = len(response.split())
            response_quality = self._get_response_quality(response, category)
            
            print(f"=== RESPONSE ANALYSIS ===")
            print(f"Response: {response[:100]}...")
            print(f"Word count: {word_count}")
            print(f"Quality level: {response_quality}")
            
            # Handle non-answers appropriately
            if response_quality == "non_answer":
                return self._get_non_answer_analysis()
            
            # Calculate all scores
            keyword_score = self._calculate_keyword_relevance(response, category)
            sentiment_scores = self.sentiment_analyzer.polarity_scores(response)
            readability_score = self._calculate_readability(response, word_count)
            specificity_score = self._calculate_specificity(response, word_count)
            similarity_score = self._calculate_semantic_similarity(question, response)
            
            # Debug output
            print(f"Keyword score: {keyword_score:.3f}")
            print(f"Similarity score: {similarity_score:.3f}")
            print(f"Readability score: {readability_score:.3f}")
            print(f"Specificity score: {specificity_score:.3f}")
            print(f"=========================")
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                keyword_score, similarity_score, readability_score, 
                specificity_score, word_count, sentiment_scores, response_quality
            )
            
            # Generate ACCURATE feedback based on actual scores
            strengths, improvements = self._generate_accurate_feedback(
                keyword_score, similarity_score, readability_score,
                specificity_score, word_count, sentiment_scores, 
                overall_score, response_quality
            )
            
            # Calculate individual scores - ACCURATE based on response quality
            relevance = round(keyword_score * 10, 1)
            completeness = round(specificity_score * 10, 1)
            clarity = round(readability_score * 10, 1)
            technical_accuracy = round(similarity_score * 10, 1)
            
            return {
                "relevance_score": float(relevance),
                "completeness_score": float(completeness),
                "clarity_score": float(clarity),
                "technical_accuracy": float(technical_accuracy),
                "overall_score": float(round(overall_score, 1)),
                "word_count": int(word_count),
                "sentiment_compound": float(round(sentiment_scores['compound'], 2)),
                "strengths": strengths,
                "improvement_areas": improvements,
                "feedback": self._generate_detailed_feedback(strengths, improvements, overall_score, response_quality)
            }
            
        except Exception as e:
            print(f"Error analyzing response: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_analysis()

    def _get_non_answer_analysis(self) -> Dict[str, Any]:
        """Return analysis for non-answers (I don't know, etc.)"""
        return {
            "relevance_score": 1.0,
            "completeness_score": 1.0,
            "clarity_score": 2.0,
            "technical_accuracy": 1.0,
            "overall_score": 1.5,
            "word_count": 0,
            "sentiment_compound": 0.0,
            "strengths": ["Honest about limitations"],
            "improvement_areas": [
                "Provide an actual answer to the question",
                "Share any relevant experience or knowledge",
                "Even partial answers are better than no answer"
            ],
            "feedback": "You indicated you don't know the answer. Try to provide at least a partial response or share related experience."
        }

    def _calculate_keyword_relevance(self, response: str, category: str) -> float:
        """Calculate keyword relevance - ACCURATE"""
        if category not in self.category_keywords:
            return 0.3
        
        keywords = self.category_keywords[category]["keywords"]
        response_lower = response.lower()
        word_count = len(response.split())
        
        # Very short responses can't have good relevance
        if word_count < 10:
            return 0.1
        
        # Count matches
        matches = sum(1 for keyword in keywords if keyword in response_lower)
        
        # Calculate score based on matches and response length
        if matches == 0:
            return 0.15
        elif matches == 1:
            return 0.3
        elif matches == 2:
            return 0.5
        elif matches <= 4:
            return 0.65
        elif matches <= 6:
            return 0.75
        else:
            return min(0.85 + (matches * 0.02), 1.0)

    def _calculate_semantic_similarity(self, question: str, response: str) -> float:
        """Calculate semantic similarity - ACCURATE"""
        try:
            if not question or not response:
                return 0.2
            
            question = question.strip()
            response = response.strip()
            word_count = len(response.split())
            
            # Very short responses have low similarity
            if word_count < 5:
                return 0.15
            if word_count < 10:
                return 0.25
            
            # Encode texts
            embeddings = self.sentence_model.encode([question, response])
            
            # Calculate similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            similarity = float(similarity)
            
            # Keep raw similarity more accurate (typically 0.1-0.7 range)
            # Just ensure it's in valid range
            normalized = max(0.1, min(similarity, 0.95))
            
            print(f"Semantic similarity: raw={similarity:.3f}, normalized={normalized:.3f}")
            
            return normalized
            
        except Exception as e:
            print(f"Error in semantic similarity: {e}")
            return 0.3

    def _calculate_readability(self, text: str, word_count: int) -> float:
        """Calculate readability score - ACCURATE"""
        # Very short responses have low readability score
        if word_count < 5:
            return 0.2
        if word_count < 10:
            return 0.35
        if word_count < 15:
            return 0.45
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        
        if len(sentences) == 0:
            sentences = [text]
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Score based on readability metrics
        if avg_sentence_length < 15 and avg_word_length < 6:
            base_score = 0.85
        elif avg_sentence_length < 20 and avg_word_length < 7:
            base_score = 0.7
        elif avg_sentence_length < 30 and avg_word_length < 8:
            base_score = 0.55
        else:
            base_score = 0.4
        
        return base_score

    def _calculate_specificity(self, text: str, word_count: int) -> float:
        """Calculate specificity score - ACCURATE"""
        # Very short responses lack specificity
        if word_count < 5:
            return 0.1
        if word_count < 10:
            return 0.2
        if word_count < 20:
            return 0.35
        
        text_lower = text.lower()
        unique_words = set(word.lower() for word in text.split())
        
        specific_indicators = [
            'because', 'example', 'specifically', 'instance', 
            'experience', 'when i', 'project', 'previously', 'successfully',
            'implemented', 'developed', 'created', 'built', 'designed', 'achieved',
            'resulted', 'led to', 'contributed', 'my role', 'team', 'we',
            'company', 'client', 'customer', 'product', 'service', 'system',
            'increased', 'decreased', 'improved', 'reduced', 'saved', 'managed'
        ]
        
        indicator_count = sum(1 for ind in specific_indicators if ind in text_lower)
        uniqueness_ratio = len(unique_words) / word_count if word_count > 0 else 0
        
        # Calculate score
        if indicator_count == 0:
            base_score = 0.25 + (uniqueness_ratio * 0.3)
        elif indicator_count == 1:
            base_score = 0.4 + (uniqueness_ratio * 0.3)
        elif indicator_count == 2:
            base_score = 0.55 + (uniqueness_ratio * 0.2)
        elif indicator_count <= 4:
            base_score = 0.7 + (uniqueness_ratio * 0.15)
        else:
            base_score = 0.8 + min(indicator_count * 0.02, 0.15)
        
        return min(base_score, 1.0)

    def _calculate_overall_score(
        self,
        keyword_score: float,
        similarity_score: float,
        readability_score: float,
        specificity_score: float,
        word_count: int,
        sentiment_scores: Dict,
        response_quality: str,
    ) -> float:

        # Base weighted score in 0–1
        base_score = (
            keyword_score * 0.22 +
            similarity_score * 0.33 +
            readability_score * 0.20 +
            specificity_score * 0.25
        )

        # Length adjustment (still matters, but gently)
        length_adj = 0.0
        if word_count >= 100:
            length_adj = 0.10
        elif word_count >= 70:
            length_adj = 0.07
        elif word_count >= 40:
            length_adj = 0.04
        elif word_count >= 25:
            length_adj = 0.02
        elif word_count < 12:
            length_adj = -0.08  # very short answers penalized

        # Sentiment adjustment (slight boost for positive, slight penalty for very negative)
        sentiment = sentiment_scores.get("compound", 0)
        sentiment_adj = 0.0
        if sentiment >= 0.3:
            sentiment_adj = 0.04
        elif sentiment >= 0.1:
            sentiment_adj = 0.02
        elif sentiment < -0.3:
            sentiment_adj = -0.03

        # Combine into base 0–10 score
        combined = base_score + length_adj + sentiment_adj
        final_score = combined * 10.0

        # Hard cap between 1 and 10 before floors
        final_score = max(min(final_score, 10.0), 1.0)

        # Quality-based floors (this is where we make it more lenient)
        if response_quality == "non_answer":
            # Still strict here
            return 1.5

        if response_quality == "very_short":
            # Very short but not pure "I don't know"
            return min(final_score, 4.0)

        if response_quality == "short":
            # Short but meaningful
            final_score = max(final_score, 5.0)
        elif response_quality == "adequate":
            final_score = max(final_score, 6.0)
        elif response_quality == "good":
            final_score = max(final_score, 7.5)
        elif response_quality == "excellent":
            final_score = max(final_score, 8.5)

        # Final clamp and rounding
        return float(round(max(min(final_score, 10.0), 1.0), 1))
    
    def _generate_accurate_feedback(self, keyword_score: float, similarity_score: float,
                                   readability_score: float, specificity_score: float,
                                   word_count: int, sentiment_scores: Dict, 
                                   overall_score: float, response_quality: str) -> Tuple[List[str], List[str]]:
        """Generate ACCURATE feedback based on actual scores"""
        strengths = []
        improvements = []
        
        # Handle non-answers and very short responses
        if response_quality == "non_answer":
            return ["Honest about limitations"], [
                "Provide an actual answer",
                "Share any relevant experience",
                "Even partial answers help"
            ]
        
        if response_quality == "very_short":
            return ["Attempted to respond"], [
                "Provide a more detailed answer",
                "Aim for at least 30-50 words",
                "Include specific examples"
            ]
        
        # Generate strengths based on ACTUAL high scores
        if keyword_score >= 0.6:
            strengths.append("Good use of relevant terminology")
        if similarity_score >= 0.5:
            strengths.append("Response addresses the question well")
        if readability_score >= 0.65:
            strengths.append("Clear and well-structured answer")
        if specificity_score >= 0.55:
            strengths.append("Includes specific details and examples")
        if word_count >= 60:
            strengths.append("Comprehensive and detailed response")
        if sentiment_scores.get('compound', 0) >= 0.2:
            strengths.append("Confident and professional tone")
        
        # Generate improvements based on ACTUAL low scores
        if keyword_score < 0.4:
            improvements.append("Include more relevant industry terminology")
        if similarity_score < 0.4:
            improvements.append("Focus more directly on the question asked")
        if readability_score < 0.5:
            improvements.append("Improve clarity and structure of response")
        if specificity_score < 0.4:
            improvements.append("Add more specific examples from experience")
        if word_count < 30:
            improvements.append("Provide a more detailed explanation")
        if word_count > 200:
            improvements.append("Consider being more concise")
        if sentiment_scores.get('compound', 0) < 0:
            improvements.append("Use a more positive and confident tone")
        
        # Ensure we have at least one item in each list
        if not strengths:
            if word_count >= 20:
                strengths.append("Attempted to answer the question")
            else:
                strengths.append("Response recorded")
        
        if not improvements:
            if overall_score >= 8:
                improvements.append("Excellent response - keep this approach")
            elif overall_score >= 6:
                improvements.append("Good response - minor refinements possible")
            else:
                improvements.append("Practice providing more detailed answers")
        
        return strengths[:3], improvements[:3]

    def _generate_detailed_feedback(self, strengths: List[str], improvements: List[str], 
                                   score: float, response_quality: str) -> str:
        """Generate feedback text"""
        if response_quality == "non_answer":
            return "You didn't provide a substantive answer. Try to share any relevant knowledge or experience, even if partial."
        
        if response_quality == "very_short":
            return "Your response is too brief. Please provide more detail and specific examples to demonstrate your knowledge."
        
        if score >= 8:
            base = "Excellent response! "
        elif score >= 6.5:
            base = "Very good response. "
        elif score >= 5:
            base = "Good response. "
        elif score >= 3.5:
            base = "Adequate response, but needs improvement. "
        else:
            base = "Response needs significant improvement. "
        
        return f"{base}Strengths: {', '.join(strengths)}. Areas to improve: {', '.join(improvements)}."

    def calculate_final_score(self, all_scores: List[Dict]) -> Dict[str, Any]:
        """Calculate final interview score"""
        if not all_scores:
            return self._get_default_final_result()
        
        # Calculate average overall score
        total_score = sum(float(score.get('overall_score', 0)) for score in all_scores)
        avg_score = float(total_score / len(all_scores))
        
        # Collect all strengths and improvements
        all_strengths = []
        all_improvements = []
        
        for score in all_scores:
            all_strengths.extend(score.get('strengths', []))
            all_improvements.extend(score.get('improvement_areas', []))
        
        # Get most common (but filter out generic ones for low scores)
        strength_counter = Counter(all_strengths)
        improvement_counter = Counter(all_improvements)
        
        # Filter out "Response recorded" and similar if we have better options
        filtered_strengths = [s for s in strength_counter.most_common(5) 
                            if s[0] not in ["Response recorded", "Attempted to respond"]]
        if filtered_strengths:
            common_strengths = [item for item, _ in filtered_strengths[:3]]
        else:
            common_strengths = [item for item, _ in strength_counter.most_common(3)]
        
        common_improvements = [item for item, _ in improvement_counter.most_common(3)]
        
        # Calculate category breakdown
        category_breakdown = {}
        
        for cat, key in [('relevance', 'relevance_score'), ('completeness', 'completeness_score'),
                        ('clarity', 'clarity_score'), ('technical_accuracy', 'technical_accuracy')]:
            scores = [float(s.get(key, 3.0)) for s in all_scores]
            avg = sum(scores) / len(scores) if scores else 3.0
            category_breakdown[cat] = float(round(avg, 1))
        
        # Generate feedback based on score
        if avg_score >= 8:
            feedback = "Outstanding performance! You demonstrated excellent communication skills and strong knowledge."
        elif avg_score >= 6.5:
            feedback = "Very good performance! You showed solid understanding with room for minor improvements."
        elif avg_score >= 5:
            feedback = "Good performance. Focus on providing more specific examples and detailed answers."
        elif avg_score >= 3:
            feedback = "Fair performance. Work on providing more comprehensive answers with relevant details."
        else:
            feedback = "Needs improvement. Practice providing detailed, structured responses with specific examples."
        
        return {
            "overall_score": float(round(avg_score, 1)),
            "detailed_feedback": feedback,
            "areas_for_improvement": common_improvements if common_improvements else ["Practice more detailed responses"],
            "strength_analysis": common_strengths if common_strengths else ["Completed the interview"],
            "category_breakdown": category_breakdown
        }

    def _get_fallback_questions(self, category: str, count: int) -> List[str]:
        """Fallback questions"""
        fallback = {
            "technical": [
                "Explain object-oriented programming principles.",
                "What's the difference between SQL and NoSQL?",
                "How do you approach debugging?",
                "Describe your experience with cloud services.",
                "How do you ensure code quality?",
                "What's your experience with version control?",
                "How do you handle testing?",
                "Describe a technical challenge you solved."
            ],
            "behavioral": [
                "Tell me about a challenge you overcame.",
                "How do you handle team conflicts?",
                "Describe a leadership experience.",
                "How do you prioritize tasks?",
                "Tell me about a mistake and what you learned.",
                "How do you handle feedback?",
                "Describe adapting to change.",
                "Tell me about going above and beyond."
            ],
            "management": [
                "How do you delegate tasks?",
                "How do you motivate team members?",
                "Describe your project planning approach.",
                "How do you handle underperformers?",
                "How do you measure success?",
                "Describe a difficult decision you made.",
                "How do you set team goals?",
                "How do you handle conflicts?"
            ],
            "sales": [
                "How do you build client relationships?",
                "Describe your sales process.",
                "How do you handle objections?",
                "What metrics do you track?",
                "Describe a successful campaign.",
                "How do you qualify leads?",
                "How do you handle rejection?",
                "Describe your closing approach."
            ]
        }
        return fallback.get(category, fallback["technical"])[:count]

    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Fallback analysis"""
        return {
            "relevance_score": 3.0,
            "completeness_score": 3.0,
            "clarity_score": 3.0,
            "technical_accuracy": 3.0,
            "overall_score": 3.0,
            "word_count": 0,
            "sentiment_compound": 0.0,
            "strengths": ["Response recorded"],
            "improvement_areas": ["Unable to analyze - please try again"],
            "feedback": "There was an issue analyzing your response. Please try again."
        }

    def _get_default_final_result(self) -> Dict[str, Any]:
        """Default final result"""
        return {
            "overall_score": 1.0,
            "detailed_feedback": "No responses were provided.",
            "areas_for_improvement": ["Complete all questions"],
            "strength_analysis": [],
            "category_breakdown": {
                "relevance": 1.0,
                "completeness": 1.0,
                "clarity": 1.0,
                "technical_accuracy": 1.0
            }
        }