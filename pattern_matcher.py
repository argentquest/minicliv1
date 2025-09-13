"""
Advanced pattern matching for detecting tool commands and code analysis requests.
"""
import re
from typing import List, Dict, Set, Optional
from dataclasses import dataclass


@dataclass
class PatternMatch:
    """Represents a pattern match with confidence and context."""
    pattern: str
    confidence: float
    context: str
    match_type: str


class ToolCommandPatternMatcher:
    """Advanced pattern matcher for detecting tool commands and code analysis requests."""
    
    def __init__(self):
        # Compile patterns once for better performance
        self._code_analysis_patterns = self._compile_code_analysis_patterns()
        self._intent_patterns = self._compile_intent_patterns()
        self._file_reference_patterns = self._compile_file_reference_patterns()
        self._programming_keywords = self._compile_programming_keywords()
        
    def _compile_code_analysis_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for code analysis detection."""
        patterns = [
            # Direct code references
            r'\bthis\s+code\b',
            r'\bthe\s+code\b',
            r'\bmy\s+code\b',
            r'\bour\s+code\b',
            r'\bcodebase\b',
            r'\brepository\b',
            r'\bproject\b',
            
            # Analysis verbs with code context
            r'\b(analyze|review|examine|inspect|check|audit)\s+(this|the|my|our)?\s*(code|codebase|files?|project)\b',
            r'\b(explain|describe|summarize|document)\s+(this|the|my|our)?\s*(code|implementation|logic)\b',
            r'\b(fix|debug|solve|resolve)\s+(this|the|my|our)?\s*(code|bug|issue|problem)\b',
            r'\b(refactor|improve|optimize|enhance)\s+(this|the|my|our)?\s*(code|implementation)\b',
            r'\b(test|validate|verify)\s+(this|the|my|our)?\s*(code|implementation|logic)\b',
            
            # Code quality and maintenance
            r'\bcode\s+(quality|review|analysis|coverage)\b',
            r'\b(security|vulnerability|exploit)\s+(scan|check|analysis|review)\b',
            r'\b(performance|optimization|bottleneck)\s+(analysis|review|check)\b',
            r'\b(lint|format|style)\s+(check|analysis)\b',
            
            # File and structure references
            r'\bfollowing\s+(code|files?|implementation)\b',
            r'\bthese\s+(files?|modules?|components?)\b',
            r'\bin\s+(this|the)\s+(file|module|component|class|function)\b',
            
            # Programming concepts that suggest code analysis
            r'\b(function|method|class|variable|algorithm|data\s+structure)\b.*\b(explain|analyze|review|fix)\b',
            r'\b(explain|analyze|review|fix)\b.*\b(function|method|class|variable|algorithm|data\s+structure)\b',
        ]
        
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _compile_intent_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile patterns for different analysis intents."""
        intents = {
            'security': [
                r'\b(security|vulnerability|exploit|attack|breach|unsafe|insecure)\b',
                r'\b(SQL\s+injection|XSS|CSRF|buffer\s+overflow|privilege\s+escalation)\b',
                r'\b(authentication|authorization|access\s+control|encryption|sanitization)\b',
            ],
            'performance': [
                r'\b(performance|speed|slow|fast|optimization|bottleneck|latency)\b',
                r'\b(memory\s+leak|memory\s+usage|CPU\s+usage|cache|caching)\b',
                r'\b(algorithm\s+complexity|time\s+complexity|space\s+complexity)\b',
            ],
            'quality': [
                r'\b(code\s+quality|maintainability|readability|complexity|technical\s+debt)\b',
                r'\b(best\s+practices|clean\s+code|design\s+patterns|refactoring)\b',
                r'\b(SOLID|DRY|KISS|separation\s+of\s+concerns)\b',
            ],
            'testing': [
                r'\b(test|testing|unit\s+test|integration\s+test|coverage)\b',
                r'\b(mock|stub|fixture|assertion|test\s+case)\b',
                r'\b(TDD|BDD|test\s+driven|behavior\s+driven)\b',
            ],
            'documentation': [
                r'\b(document|documentation|comment|docstring|README)\b',
                r'\b(API\s+doc|inline\s+comment|code\s+comment|JSDoc|sphinx)\b',
            ]
        }
        
        compiled_intents = {}
        for intent, patterns in intents.items():
            compiled_intents[intent] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        
        return compiled_intents
    
    def _compile_file_reference_patterns(self) -> List[re.Pattern]:
        """Compile patterns for file and code structure references."""
        patterns = [
            # File extensions and types
            r'\b\w+\.(py|js|ts|java|cpp|c|h|php|rb|go|rs|swift|kt|scala|cs|vb|sql|html|css|json|xml|yaml|yml)\b',
            
            # File path patterns
            r'\b(src/|lib/|app/|components?/|utils?/|helpers?/|models?/|views?/|controllers?/)\w+',
            r'\b\w+/(main|index|app|server|client)\.\w+\b',
            
            # Code structure references
            r'\b(main|index|app|config|setup|init|utils|helpers|models|views|controllers|routes|api|auth|database|db)\b',
            r'\bpackage\.json\b|\brequirements\.txt\b|\bpom\.xml\b|\bCargo\.toml\b',
        ]
        
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _compile_programming_keywords(self) -> Set[str]:
        """Compile set of programming-related keywords."""
        keywords = {
            # General programming concepts
            'algorithm', 'function', 'method', 'class', 'object', 'variable', 'constant',
            'array', 'list', 'dictionary', 'hash', 'map', 'set', 'queue', 'stack',
            'loop', 'iteration', 'recursion', 'condition', 'branch', 'exception',
            'import', 'export', 'module', 'package', 'library', 'framework',
            'database', 'query', 'schema', 'table', 'index', 'transaction',
            'api', 'endpoint', 'route', 'middleware', 'controller', 'model', 'view',
            'authentication', 'authorization', 'session', 'cookie', 'token',
            'async', 'await', 'promise', 'callback', 'thread', 'process',
            'git', 'commit', 'merge', 'branch', 'repository', 'version',
            
            # Language-specific keywords
            'def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while',
            'try', 'except', 'finally', 'with', 'as', 'return', 'yield', 'lambda',
            'function', 'var', 'let', 'const', 'public', 'private', 'protected',
            'static', 'final', 'abstract', 'interface', 'extends', 'implements',
            'new', 'this', 'super', 'null', 'undefined', 'true', 'false',
        }
        
        return keywords
    
    def analyze_question(self, question: str, tool_vars: Dict[str, str] = None) -> PatternMatch:
        """
        Analyze question for tool command patterns with confidence scoring.
        
        Args:
            question: The user's question to analyze
            tool_vars: Optional dictionary of TOOL environment variables
            
        Returns:
            PatternMatch object with confidence score and context
        """
        if not question or not isinstance(question, str):
            return PatternMatch("", 0.0, "", "none")
        
        confidence = 0.0
        contexts = []
        match_types = []
        
        # Check exact tool command matches (highest confidence)
        if tool_vars:
            for tool_key, tool_text in tool_vars.items():
                if tool_text and tool_text.strip() in question:
                    confidence = max(confidence, 0.95)
                    contexts.append(f"Exact tool match: {tool_key}")
                    match_types.append("exact_tool")
        
        # Check code analysis patterns
        question_lower = question.lower()
        code_matches = 0
        
        for pattern in self._code_analysis_patterns:
            if pattern.search(question_lower):
                code_matches += 1
                confidence = max(confidence, 0.8)
                contexts.append(f"Code analysis pattern: {pattern.pattern}")
                match_types.append("code_analysis")
        
        # Check for programming keywords
        words = set(re.findall(r'\b\w+\b', question_lower))
        keyword_matches = len(words.intersection(self._programming_keywords))
        
        if keyword_matches >= 3:
            confidence = max(confidence, 0.7)
            contexts.append(f"Programming keywords: {keyword_matches}")
            match_types.append("programming_keywords")
        elif keyword_matches >= 1:
            confidence = max(confidence, 0.4)
            contexts.append(f"Some programming keywords: {keyword_matches}")
            match_types.append("programming_keywords")
        
        # Check file reference patterns
        for pattern in self._file_reference_patterns:
            if pattern.search(question):
                confidence = max(confidence, 0.6)
                contexts.append(f"File reference pattern: {pattern.pattern}")
                match_types.append("file_reference")
        
        # Check intent-specific patterns
        for intent, patterns in self._intent_patterns.items():
            intent_matches = sum(1 for pattern in patterns if pattern.search(question_lower))
            if intent_matches > 0:
                intent_confidence = min(0.8, 0.3 + (intent_matches * 0.1))
                confidence = max(confidence, intent_confidence)
                contexts.append(f"{intent.title()} intent: {intent_matches} matches")
                match_types.append(f"intent_{intent}")
        
        # Boost confidence for multiple pattern types
        if len(set(match_types)) >= 2:
            confidence = min(0.95, confidence + 0.1)
            contexts.append("Multiple pattern types detected")
        
        # Create combined context string
        context = "; ".join(contexts[:3])  # Limit to top 3 contexts
        match_type = match_types[0] if match_types else "none"
        
        return PatternMatch(
            pattern=context,
            confidence=confidence,
            context=context,
            match_type=match_type
        )
    
    def is_tool_command(self, question: str, tool_vars: Dict[str, str] = None, threshold: float = 0.5) -> bool:
        """
        Determine if question requires codebase context based on pattern analysis.
        
        Args:
            question: The user's question
            tool_vars: Optional TOOL environment variables
            threshold: Confidence threshold for classification (default: 0.5)
            
        Returns:
            True if question likely needs codebase context
        """
        match = self.analyze_question(question, tool_vars)
        return match.confidence >= threshold
    
    def get_analysis_details(self, question: str, tool_vars: Dict[str, str] = None) -> Dict:
        """
        Get detailed analysis of question patterns for debugging/logging.
        
        Args:
            question: The user's question
            tool_vars: Optional TOOL environment variables
            
        Returns:
            Dictionary with detailed analysis results
        """
        match = self.analyze_question(question, tool_vars)
        
        return {
            "question_length": len(question),
            "confidence": match.confidence,
            "match_type": match.match_type,
            "context": match.context,
            "requires_codebase": match.confidence >= 0.5,
            "programming_keywords": len(set(re.findall(r'\b\w+\b', question.lower())).intersection(self._programming_keywords)),
            "has_file_references": any(pattern.search(question) for pattern in self._file_reference_patterns),
            "analysis_patterns_matched": sum(1 for pattern in self._code_analysis_patterns if pattern.search(question.lower()))
        }


# Global instance for efficient reuse
pattern_matcher = ToolCommandPatternMatcher()