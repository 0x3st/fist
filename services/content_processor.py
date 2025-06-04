"""
Intelligent Content Processing Service for FIST Content Moderation System.

This module provides advanced content processing algorithms including:
- Semantic-aware content segmentation
- Dynamic threshold management
- Content-type specific processing strategies
- Intelligent text piercing based on content analysis
"""
import logging
import re
import random
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from config import Config


class ContentType(Enum):
    """Content type classifications."""
    SOCIAL_MEDIA = "social_media"
    NEWS_ARTICLE = "news_article"
    REVIEW = "review"
    COMMENT = "comment"
    QUESTION = "question"
    PROMOTIONAL = "promotional"
    TECHNICAL = "technical"
    GENERAL = "general"


class SegmentationType(Enum):
    """Content segmentation strategies."""
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    RANDOM = "random"
    IMPORTANCE_BASED = "importance_based"


@dataclass
class ContentSegment:
    """Represents a segment of content."""
    text: str
    start_position: int
    end_position: int
    importance_score: float
    segment_type: str
    metadata: Dict[str, Any]


@dataclass
class ProcessingStrategy:
    """Content processing strategy configuration."""
    segmentation_type: SegmentationType
    min_segment_length: int
    max_segment_length: int
    overlap_percentage: float
    importance_threshold: float
    preserve_structure: bool


@dataclass
class ProcessingResult:
    """Result of content processing."""
    selected_segments: List[ContentSegment]
    total_segments: int
    selection_ratio: float
    processing_strategy: ProcessingStrategy
    content_type: ContentType
    confidence: float


class IntelligentContentProcessor:
    """Advanced content processing with semantic awareness."""
    
    def __init__(self):
        """Initialize the content processor."""
        self.logger = logging.getLogger(__name__)
        
        # Content type detection patterns
        self.content_patterns = {
            ContentType.SOCIAL_MEDIA: [
                r'#\w+',  # Hashtags
                r'@\w+',  # Mentions
                r'\b(like|share|follow|retweet|RT)\b',
                r'\b(lol|omg|wtf|lmao|rofl)\b'
            ],
            ContentType.NEWS_ARTICLE: [
                r'\b(breaking|update|report|announced)\b',
                r'\d{4}-\d{2}-\d{2}',  # Dates
                r'\b(according to|sources say|reported)\b',
                r'\b(journalist|reporter|correspondent)\b'
            ],
            ContentType.REVIEW: [
                r'\b(rating|stars|review|recommend)\b',
                r'\b\d+/\d+\b',  # Ratings
                r'\b(pros|cons|verdict|overall)\b',
                r'\b(would recommend|not recommend)\b'
            ],
            ContentType.COMMENT: [
                r'\b(think|opinion|believe|feel)\b',
                r'\b(agree|disagree|exactly|totally)\b',
                r'\b(imho|imo|tbh|honestly)\b'
            ],
            ContentType.QUESTION: [
                r'\?',
                r'\b(how|what|why|when|where|who)\b',
                r'\b(help|advice|suggestion|anyone know)\b',
                r'\b(can someone|does anyone)\b'
            ],
            ContentType.PROMOTIONAL: [
                r'\b(buy|sale|discount|offer|deal)\b',
                r'\$\d+',
                r'\b(limited time|act now|don\'t miss)\b',
                r'\b(free shipping|money back)\b'
            ],
            ContentType.TECHNICAL: [
                r'\b(algorithm|function|variable|code)\b',
                r'\b(API|SDK|framework|library)\b',
                r'\b(debug|compile|execute|deploy)\b',
                r'```[\s\S]*?```'  # Code blocks
            ]
        }
        
        # Importance indicators
        self.importance_indicators = {
            'high': [
                r'\b(important|critical|urgent|warning)\b',
                r'\b(error|failure|problem|issue)\b',
                r'\b(security|privacy|confidential)\b',
                r'[A-Z]{2,}',  # All caps words
                r'!{2,}'  # Multiple exclamation marks
            ],
            'medium': [
                r'\b(note|notice|attention|please)\b',
                r'\b(update|change|new|latest)\b',
                r'\b(recommend|suggest|advise)\b'
            ],
            'low': [
                r'\b(maybe|perhaps|possibly|might)\b',
                r'\b(optional|additional|extra)\b'
            ]
        }
        
        # Structural elements
        self.structural_patterns = {
            'sentence_boundary': r'[.!?]+\s+',
            'paragraph_boundary': r'\n\s*\n',
            'list_item': r'^\s*[-*•]\s+',
            'heading': r'^#+\s+',
            'quote': r'^>\s+',
            'code_block': r'```[\s\S]*?```',
            'inline_code': r'`[^`]+`'
        }
        
        self.logger.info("Intelligent content processor initialized")
    
    def detect_content_type(self, text: str) -> Tuple[ContentType, float]:
        """
        Detect the type of content based on patterns and structure.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (content_type, confidence)
        """
        text_lower = text.lower()
        type_scores = {}
        
        for content_type, patterns in self.content_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                score += matches
            
            if score > 0:
                # Normalize score by text length
                normalized_score = score / len(text.split()) if text.split() else 0
                type_scores[content_type] = normalized_score
        
        if not type_scores:
            return ContentType.GENERAL, 0.5
        
        best_type = max(type_scores.keys(), key=lambda k: type_scores[k])
        confidence = min(1.0, type_scores[best_type] * 10)  # Scale confidence
        
        return best_type, confidence
    
    def calculate_importance_score(self, text: str) -> float:
        """
        Calculate importance score for a text segment.
        
        Args:
            text: Text to analyze
            
        Returns:
            Importance score (0.0 to 1.0)
        """
        score = 0.5  # Base score
        text_lower = text.lower()
        
        # Check for importance indicators
        for level, patterns in self.importance_indicators.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                if level == 'high':
                    score += matches * 0.3
                elif level == 'medium':
                    score += matches * 0.2
                elif level == 'low':
                    score -= matches * 0.1
        
        # Adjust based on position (beginning and end are more important)
        # This would be calculated relative to the full text in practice
        
        # Adjust based on length (very short or very long segments are less important)
        word_count = len(text.split())
        if word_count < 5:
            score *= 0.7
        elif word_count > 50:
            score *= 0.8
        
        return max(0.0, min(1.0, score))
    
    def segment_content_semantic(self, text: str, strategy: ProcessingStrategy) -> List[ContentSegment]:
        """
        Segment content based on semantic boundaries.
        
        Args:
            text: Text to segment
            strategy: Processing strategy
            
        Returns:
            List of content segments
        """
        segments = []
        
        # First, try to segment by sentences
        sentences = re.split(self.structural_patterns['sentence_boundary'], text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        current_segment = ""
        start_pos = 0
        
        for sentence in sentences:
            # Check if adding this sentence would exceed max length
            potential_segment = current_segment + " " + sentence if current_segment else sentence
            
            if len(potential_segment.split()) <= strategy.max_segment_length:
                current_segment = potential_segment
            else:
                # Save current segment if it meets minimum length
                if len(current_segment.split()) >= strategy.min_segment_length:
                    importance = self.calculate_importance_score(current_segment)
                    segments.append(ContentSegment(
                        text=current_segment,
                        start_position=start_pos,
                        end_position=start_pos + len(current_segment),
                        importance_score=importance,
                        segment_type="semantic",
                        metadata={"sentence_count": len(re.split(r'[.!?]+', current_segment))}
                    ))
                    start_pos += len(current_segment) + 1
                
                # Start new segment
                current_segment = sentence
        
        # Add final segment
        if current_segment and len(current_segment.split()) >= strategy.min_segment_length:
            importance = self.calculate_importance_score(current_segment)
            segments.append(ContentSegment(
                text=current_segment,
                start_position=start_pos,
                end_position=start_pos + len(current_segment),
                importance_score=importance,
                segment_type="semantic",
                metadata={"sentence_count": len(re.split(r'[.!?]+', current_segment))}
            ))
        
        return segments
    
    def segment_content_structural(self, text: str, strategy: ProcessingStrategy) -> List[ContentSegment]:
        """
        Segment content based on structural elements.
        
        Args:
            text: Text to segment
            strategy: Processing strategy
            
        Returns:
            List of content segments
        """
        segments = []
        
        # Split by paragraphs first
        paragraphs = re.split(self.structural_patterns['paragraph_boundary'], text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            words = paragraph.split()
            
            if len(words) <= strategy.max_segment_length:
                # Paragraph fits in one segment
                if len(words) >= strategy.min_segment_length:
                    importance = self.calculate_importance_score(paragraph)
                    segments.append(ContentSegment(
                        text=paragraph,
                        start_position=0,  # Would calculate actual position in full implementation
                        end_position=len(paragraph),
                        importance_score=importance,
                        segment_type="structural",
                        metadata={"paragraph_index": i, "is_complete_paragraph": True}
                    ))
            else:
                # Split paragraph into smaller segments
                current_segment = ""
                for word in words:
                    if len((current_segment + " " + word).split()) <= strategy.max_segment_length:
                        current_segment = current_segment + " " + word if current_segment else word
                    else:
                        if len(current_segment.split()) >= strategy.min_segment_length:
                            importance = self.calculate_importance_score(current_segment)
                            segments.append(ContentSegment(
                                text=current_segment,
                                start_position=0,
                                end_position=len(current_segment),
                                importance_score=importance,
                                segment_type="structural",
                                metadata={"paragraph_index": i, "is_complete_paragraph": False}
                            ))
                        current_segment = word
                
                # Add final segment from paragraph
                if current_segment and len(current_segment.split()) >= strategy.min_segment_length:
                    importance = self.calculate_importance_score(current_segment)
                    segments.append(ContentSegment(
                        text=current_segment,
                        start_position=0,
                        end_position=len(current_segment),
                        importance_score=importance,
                        segment_type="structural",
                        metadata={"paragraph_index": i, "is_complete_paragraph": False}
                    ))
        
        return segments
    
    def segment_content_random(self, text: str, strategy: ProcessingStrategy) -> List[ContentSegment]:
        """
        Segment content randomly (improved version of original algorithm).
        
        Args:
            text: Text to segment
            strategy: Processing strategy
            
        Returns:
            List of content segments
        """
        words = text.split()
        segments = []
        
        if len(words) <= strategy.max_segment_length:
            # Text is short enough to be one segment
            importance = self.calculate_importance_score(text)
            segments.append(ContentSegment(
                text=text,
                start_position=0,
                end_position=len(text),
                importance_score=importance,
                segment_type="random",
                metadata={"total_words": len(words)}
            ))
            return segments
        
        # Create multiple random segments
        remaining_words = words.copy()
        segment_count = 0
        
        while remaining_words and segment_count < 10:  # Limit to prevent infinite loops
            # Random segment length between min and max
            segment_length = random.randint(strategy.min_segment_length, 
                                          min(strategy.max_segment_length, len(remaining_words)))
            
            # Random starting position (not always from beginning)
            if len(remaining_words) > segment_length:
                max_start = len(remaining_words) - segment_length
                start_idx = random.randint(0, max_start)
            else:
                start_idx = 0
                segment_length = len(remaining_words)
            
            # Extract segment
            segment_words = remaining_words[start_idx:start_idx + segment_length]
            segment_text = " ".join(segment_words)
            
            importance = self.calculate_importance_score(segment_text)
            segments.append(ContentSegment(
                text=segment_text,
                start_position=start_idx,
                end_position=start_idx + segment_length,
                importance_score=importance,
                segment_type="random",
                metadata={"segment_index": segment_count, "random_start": start_idx}
            ))
            
            # Remove used words (with some overlap if specified)
            overlap_words = int(segment_length * strategy.overlap_percentage)
            remove_count = segment_length - overlap_words
            
            if start_idx == 0:
                remaining_words = remaining_words[remove_count:]
            else:
                # Remove from middle, keep some context
                remaining_words = remaining_words[:start_idx] + remaining_words[start_idx + remove_count:]
            
            segment_count += 1
        
        return segments
    
    def segment_content_importance(self, text: str, strategy: ProcessingStrategy) -> List[ContentSegment]:
        """
        Segment content based on importance scoring.
        
        Args:
            text: Text to segment
            strategy: Processing strategy
            
        Returns:
            List of content segments
        """
        # First get semantic segments
        semantic_segments = self.segment_content_semantic(text, strategy)
        
        # Sort by importance score
        semantic_segments.sort(key=lambda x: x.importance_score, reverse=True)
        
        # Select top segments that meet importance threshold
        important_segments = [
            seg for seg in semantic_segments 
            if seg.importance_score >= strategy.importance_threshold
        ]
        
        # If no segments meet threshold, take top segments
        if not important_segments:
            important_segments = semantic_segments[:3]  # Take top 3
        
        # Update segment type
        for segment in important_segments:
            segment.segment_type = "importance_based"
            segment.metadata["selected_by_importance"] = True
        
        return important_segments
    
    def get_processing_strategy(self, content_type: ContentType, text_length: int) -> ProcessingStrategy:
        """
        Get optimal processing strategy based on content type and length.
        
        Args:
            content_type: Type of content
            text_length: Length of text in words
            
        Returns:
            Processing strategy
        """
        # Base strategy
        strategy = ProcessingStrategy(
            segmentation_type=SegmentationType.SEMANTIC,
            min_segment_length=10,
            max_segment_length=50,
            overlap_percentage=0.1,
            importance_threshold=0.6,
            preserve_structure=True
        )
        
        # Adjust based on content type
        if content_type == ContentType.SOCIAL_MEDIA:
            strategy.segmentation_type = SegmentationType.RANDOM
            strategy.min_segment_length = 5
            strategy.max_segment_length = 30
            strategy.preserve_structure = False
            
        elif content_type == ContentType.NEWS_ARTICLE:
            strategy.segmentation_type = SegmentationType.STRUCTURAL
            strategy.min_segment_length = 20
            strategy.max_segment_length = 100
            strategy.preserve_structure = True
            
        elif content_type == ContentType.TECHNICAL:
            strategy.segmentation_type = SegmentationType.IMPORTANCE_BASED
            strategy.min_segment_length = 15
            strategy.max_segment_length = 80
            strategy.importance_threshold = 0.7
            
        elif content_type == ContentType.REVIEW:
            strategy.segmentation_type = SegmentationType.SEMANTIC
            strategy.min_segment_length = 10
            strategy.max_segment_length = 60
            
        # Adjust based on text length
        if text_length < 50:
            strategy.min_segment_length = min(5, text_length // 2)
            strategy.max_segment_length = text_length
            strategy.segmentation_type = SegmentationType.RANDOM
            
        elif text_length > 500:
            strategy.max_segment_length = min(100, text_length // 5)
            strategy.importance_threshold = 0.7  # Be more selective for long texts
        
        return strategy
    
    def process_content(self, text: str, target_percentage: Optional[float] = None) -> ProcessingResult:
        """
        Process content using intelligent segmentation and selection.
        
        Args:
            text: Text to process
            target_percentage: Target percentage of content to select (optional)
            
        Returns:
            Processing result with selected segments
        """
        if not text or not text.strip():
            return ProcessingResult(
                selected_segments=[],
                total_segments=0,
                selection_ratio=0.0,
                processing_strategy=ProcessingStrategy(
                    SegmentationType.RANDOM, 0, 0, 0.0, 0.0, False
                ),
                content_type=ContentType.GENERAL,
                confidence=0.0
            )
        
        # Detect content type
        content_type, type_confidence = self.detect_content_type(text)
        
        # Get processing strategy
        word_count = len(text.split())
        strategy = self.get_processing_strategy(content_type, word_count)
        
        # Segment content based on strategy
        if strategy.segmentation_type == SegmentationType.SEMANTIC:
            segments = self.segment_content_semantic(text, strategy)
        elif strategy.segmentation_type == SegmentationType.STRUCTURAL:
            segments = self.segment_content_structural(text, strategy)
        elif strategy.segmentation_type == SegmentationType.IMPORTANCE_BASED:
            segments = self.segment_content_importance(text, strategy)
        else:  # RANDOM
            segments = self.segment_content_random(text, strategy)
        
        # Select segments based on target percentage or importance
        if target_percentage is not None:
            # Select top segments by importance up to target percentage
            total_words = sum(len(seg.text.split()) for seg in segments)
            target_words = int(total_words * target_percentage)
            
            # Sort by importance and select
            segments.sort(key=lambda x: x.importance_score, reverse=True)
            selected_segments = []
            selected_words = 0
            
            for segment in segments:
                segment_words = len(segment.text.split())
                if selected_words + segment_words <= target_words:
                    selected_segments.append(segment)
                    selected_words += segment_words
                elif selected_words == 0:  # Always select at least one segment
                    selected_segments.append(segment)
                    selected_words += segment_words
                    break
        else:
            # Use importance threshold
            selected_segments = [
                seg for seg in segments 
                if seg.importance_score >= strategy.importance_threshold
            ]
            
            # Ensure we have at least one segment
            if not selected_segments and segments:
                selected_segments = [max(segments, key=lambda x: x.importance_score)]
        
        # Calculate selection ratio
        if segments:
            selection_ratio = len(selected_segments) / len(segments)
        else:
            selection_ratio = 0.0
        
        return ProcessingResult(
            selected_segments=selected_segments,
            total_segments=len(segments),
            selection_ratio=selection_ratio,
            processing_strategy=strategy,
            content_type=content_type,
            confidence=type_confidence
        )
    
    def extract_text_for_moderation(self, text: str, target_percentage: Optional[float] = None) -> str:
        """
        Extract text for moderation using intelligent processing.
        
        Args:
            text: Original text
            target_percentage: Target percentage of content to extract
            
        Returns:
            Extracted text for moderation
        """
        result = self.process_content(text, target_percentage)
        
        if not result.selected_segments:
            return text[:100]  # Fallback to first 100 characters
        
        # Combine selected segments
        extracted_texts = [segment.text for segment in result.selected_segments]
        
        # Sort by original position if preserve_structure is True
        if result.processing_strategy.preserve_structure:
            result.selected_segments.sort(key=lambda x: x.start_position)
            extracted_texts = [segment.text for segment in result.selected_segments]
        
        return " [...] ".join(extracted_texts)


# Global content processor instance
_content_processor: Optional[IntelligentContentProcessor] = None


def get_content_processor() -> IntelligentContentProcessor:
    """Get global content processor instance."""
    global _content_processor
    if _content_processor is None:
        _content_processor = IntelligentContentProcessor()
    return _content_processor


def process_content_intelligently(text: str, target_percentage: Optional[float] = None) -> str:
    """
    Convenience function to process content intelligently.
    
    Args:
        text: Text to process
        target_percentage: Target percentage of content to extract
        
    Returns:
        Processed text for moderation
    """
    processor = get_content_processor()
    return processor.extract_text_for_moderation(text, target_percentage)
