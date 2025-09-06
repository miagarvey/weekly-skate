import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class ConfidenceLevel(Enum):
    """Confidence levels for NLP predictions"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"

@dataclass
class NLPResult:
    """Result of NLP analysis"""
    is_confirmation: bool
    confidence: ConfidenceLevel
    confidence_score: float  # 0.0 to 1.0
    matched_patterns: List[str]
    sentiment: str  # positive, negative, neutral
    context_clues: List[str]
    reasoning: str

class NLPService:
    """Advanced Natural Language Processing service for detecting goalie confirmations"""
    
    # Weighted pattern categories
    CONFIRMATION_PATTERNS = {
        # Explicit confirmations (highest confidence)
        "explicit": {
            "weight": 1.0,
            "patterns": [
                r'\b(got|have|secured|found|confirmed|booked)\s+(a\s+|the\s+)?goalie\b',
                r'\bgoalie\s+(is\s+)?(secured|confirmed|booked|set|ready|found)\b',
                r'\b(yes|yep|yeah|confirmed|done|secured)\b.*\bgoalie\b',
                r'\bgoalie\s+(confirmed|secured|booked|locked\s+in)\b',
            ]
        },
        # Strong positive indicators
        "strong_positive": {
            "weight": 0.9,
            "patterns": [
                r'\b(all\s+set|we\'re\s+good|good\s+to\s+go|we\'re\s+covered)\b.*\bgoalie\b',
                r'\bgoalie.*\b(confirmed|secured|set|ready|good|covered|sorted)\b',
                r'\b(sorted|covered|handled)\b.*\bgoalie\b',
                r'\bgoalie\s+(situation|issue|problem)\s+(is\s+)?(resolved|handled|sorted|fixed)\b',
            ]
        },
        # Moderate positive indicators
        "moderate_positive": {
            "weight": 0.7,
            "patterns": [
                r'\b(think|believe|pretty\s+sure)\s+(i|we)\s+(got|have|found)\s+(a\s+)?goalie\b',
                r'\bgoalie\s+(should\s+be|might\s+be|probably)\s+(ready|set|confirmed)\b',
                r'\b(working\s+on|trying\s+to\s+get|looking\s+for)\s+(a\s+)?goalie\b.*\b(almost|nearly|close)\b',
            ]
        },
        # Weak positive indicators
        "weak_positive": {
            "weight": 0.5,
            "patterns": [
                r'\bgoalie\b.*\b(maybe|possibly|might|could)\b',
                r'\b(hope|hoping|fingers\s+crossed)\b.*\bgoalie\b',
            ]
        }
    }
    
    # Negative patterns that reduce confidence
    NEGATIVE_PATTERNS = {
        "explicit_negative": {
            "weight": -1.0,
            "patterns": [
                r'\b(no|don\'t\s+have|can\'t\s+find|couldn\'t\s+get)\s+(a\s+)?goalie\b',
                r'\bgoalie\s+(cancelled|bailed|can\'t\s+make\s+it|unavailable)\b',
                r'\b(still\s+need|looking\s+for|searching\s+for)\s+(a\s+)?goalie\b',
            ]
        },
        "uncertainty": {
            "weight": -0.5,
            "patterns": [
                r'\b(not\s+sure|uncertain|don\'t\s+know)\b.*\bgoalie\b',
                r'\bgoalie\b.*\b(questionable|iffy|unsure)\b',
            ]
        }
    }
    
    # Context clues that help interpretation
    CONTEXT_PATTERNS = {
        "urgency": [
            r'\b(urgent|asap|quickly|soon|tonight|today)\b',
            r'\b(need\s+to\s+know|let\s+me\s+know|update)\b',
        ],
        "time_references": [
            r'\b(tonight|today|tomorrow|this\s+week|next\s+week)\b',
            r'\b(\d{1,2}:\d{2}|am|pm)\b',
        ],
        "emotional_indicators": [
            r'\b(excited|great|awesome|perfect|excellent)\b',
            r'\b(worried|concerned|stressed|problem)\b',
        ]
    }
    
    # Sentiment indicators
    SENTIMENT_PATTERNS = {
        "positive": [
            r'\b(great|awesome|perfect|excellent|fantastic|good|yes|yep|yeah)\b',
            r'\b(thanks|thank\s+you|appreciate)\b',
            r'[!]{1,3}(?!\w)',  # Exclamation marks
        ],
        "negative": [
            r'\b(no|nope|can\'t|couldn\'t|won\'t|wouldn\'t|sorry|unfortunately)\b',
            r'\b(problem|issue|trouble|difficult|hard)\b',
        ],
        "neutral": [
            r'\b(maybe|perhaps|possibly|might|could|ok|okay)\b',
        ]
    }
    
    @classmethod
    def detect_goalie_confirmation(cls, message_body: str) -> bool:
        """Enhanced goalie confirmation detection with confidence scoring"""
        result = cls.analyze_message(message_body)
        
        print(f"[NLP ADVANCED] Analysis Result:")
        print(f"  - Confirmation: {result.is_confirmation}")
        print(f"  - Confidence: {result.confidence.value} ({result.confidence_score:.2f})")
        print(f"  - Sentiment: {result.sentiment}")
        print(f"  - Matched Patterns: {result.matched_patterns}")
        print(f"  - Context Clues: {result.context_clues}")
        print(f"  - Reasoning: {result.reasoning}")
        print(f"  - Message: \"{message_body}\"")
        
        return result.is_confirmation
    
    @classmethod
    def analyze_message(cls, message_body: str) -> NLPResult:
        """Comprehensive message analysis with confidence scoring"""
        message = message_body.lower().strip()
        
        # Initialize scoring
        total_score = 0.0
        matched_patterns = []
        context_clues = []
        
        # Check positive confirmation patterns
        for category, data in cls.CONFIRMATION_PATTERNS.items():
            for pattern in data["patterns"]:
                if re.search(pattern, message):
                    weight = data["weight"]
                    total_score += weight
                    matched_patterns.append(f"{category}: {pattern}")
        
        # Check negative patterns
        for category, data in cls.NEGATIVE_PATTERNS.items():
            for pattern in data["patterns"]:
                if re.search(pattern, message):
                    weight = data["weight"]
                    total_score += weight  # weight is negative
                    matched_patterns.append(f"negative_{category}: {pattern}")
        
        # Analyze context clues
        for context_type, patterns in cls.CONTEXT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    context_clues.append(context_type)
                    # Small boost for relevant context
                    total_score += 0.1
        
        # Determine sentiment
        sentiment = cls._analyze_sentiment(message)
        
        # Sentiment adjustment
        if sentiment == "positive":
            total_score += 0.2
        elif sentiment == "negative":
            total_score -= 0.2
        
        # Normalize score to 0-1 range
        confidence_score = max(0.0, min(1.0, (total_score + 1.0) / 2.0))
        
        # Determine confidence level
        if confidence_score >= 0.9:
            confidence = ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.7:
            confidence = ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            confidence = ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.3:
            confidence = ConfidenceLevel.LOW
        else:
            confidence = ConfidenceLevel.VERY_LOW
        
        # Determine if it's a confirmation (threshold: 0.5)
        is_confirmation = confidence_score >= 0.5
        
        # Generate reasoning
        reasoning = cls._generate_reasoning(
            total_score, matched_patterns, context_clues, sentiment, is_confirmation
        )
        
        return NLPResult(
            is_confirmation=is_confirmation,
            confidence=confidence,
            confidence_score=confidence_score,
            matched_patterns=matched_patterns,
            sentiment=sentiment,
            context_clues=context_clues,
            reasoning=reasoning
        )
    
    @classmethod
    def _analyze_sentiment(cls, message: str) -> str:
        """Analyze sentiment of the message"""
        positive_score = 0
        negative_score = 0
        neutral_score = 0
        
        for pattern in cls.SENTIMENT_PATTERNS["positive"]:
            positive_score += len(re.findall(pattern, message))
        
        for pattern in cls.SENTIMENT_PATTERNS["negative"]:
            negative_score += len(re.findall(pattern, message))
        
        for pattern in cls.SENTIMENT_PATTERNS["neutral"]:
            neutral_score += len(re.findall(pattern, message))
        
        if positive_score > negative_score and positive_score > neutral_score:
            return "positive"
        elif negative_score > positive_score and negative_score > neutral_score:
            return "negative"
        else:
            return "neutral"
    
    @classmethod
    def _generate_reasoning(cls, score: float, patterns: List[str], context: List[str], 
                          sentiment: str, is_confirmation: bool) -> str:
        """Generate human-readable reasoning for the decision"""
        reasoning_parts = []
        
        if is_confirmation:
            reasoning_parts.append(f"CONFIRMED goalie (score: {score:.2f})")
        else:
            reasoning_parts.append(f"NOT confirmed (score: {score:.2f})")
        
        if patterns:
            reasoning_parts.append(f"Matched {len(patterns)} pattern(s)")
        
        if sentiment != "neutral":
            reasoning_parts.append(f"{sentiment} sentiment detected")
        
        if context:
            reasoning_parts.append(f"Context: {', '.join(set(context))}")
        
        return " | ".join(reasoning_parts)
    
    @staticmethod
    def extract_venmo_username(message_body: str) -> str | None:
        """Extract Venmo username from message with improved patterns"""
        # Try different Venmo username patterns
        patterns = [
            r'@([\w\-\.]{3,30})',  # Standard @username
            r'venmo[:\s]+@?([\w\-\.]{3,30})',  # "venmo: username" or "venmo @username"
            r'username[:\s]+@?([\w\-\.]{3,30})',  # "username: @user"
            r'my\s+venmo\s+is\s+@?([\w\-\.]{3,30})',  # "my venmo is @user"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_body, re.IGNORECASE)
            if match:
                username = match.group(1)
                if 3 <= len(username) <= 30 and not username.startswith('.') and not username.endswith('.'):
                    return username
        
        return None
    
    @classmethod
    def get_confidence_threshold(cls) -> float:
        """Get the confidence threshold for confirmations"""
        return 0.5
    
    @classmethod
    def is_high_confidence(cls, message_body: str) -> bool:
        """Check if message is high confidence confirmation"""
        result = cls.analyze_message(message_body)
        return result.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]
