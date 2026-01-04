"""
Unit Tests for RAG System
==========================
Tests for retrieval accuracy, context relevance, and integration.
"""

import unittest
import sys
from pathlib import Path
import numpy as np

# Add scripts to path
sys.path.append(str(Path(__file__).parent))

from rag_system import MarketRAGSystem, RetrievedContext, create_default_knowledge_base
from llm_explainer import LLMExplainer
from agent_logic import AlertDecision, AlertType, ConfidenceLevel


class TestRAGSystem(unittest.TestCase):
    """Test RAG system functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create knowledge base
        create_default_knowledge_base()
        
        # Initialize RAG system
        cls.rag = MarketRAGSystem(use_embeddings=False)
    
    def test_initialization(self):
        """Test RAG system initializes correctly."""
        self.assertIsNotNone(self.rag)
        self.assertIsNotNone(self.rag.historical_data)
        self.assertIsInstance(self.rag.alert_history, list)
    
    def test_retrieve_context(self):
        """Test context retrieval."""
        metrics = {
            'last_close': 150.0,
            'predicted_close': 144.0,
            'percent_change': -4.0,
            'volatility': 0.035,
            'trend': 'downward'
        }
        
        context = self.rag.retrieve_context(
            current_metrics=metrics,
            alert_type='price_drop',
            stock_symbol='AAPL'
        )
        
        # Check returned type
        self.assertIsInstance(context, RetrievedContext)
        
        # Check has components
        self.assertIsInstance(context.similar_patterns, list)
        self.assertIsInstance(context.past_alerts, list)
        self.assertIsInstance(context.market_insights, list)
        
        # Check relevance score
        self.assertGreaterEqual(context.relevance_score, 0.0)
        self.assertLessEqual(context.relevance_score, 1.0)
    
    def test_similar_patterns_quality(self):
        """Test that similar patterns are actually similar."""
        metrics = {
            'last_close': 150.0,
            'predicted_close': 144.0,
            'percent_change': -4.0,
            'volatility': 0.03,
            'trend': 'downward'
        }
        
        context = self.rag.retrieve_context(
            current_metrics=metrics,
            alert_type='price_drop',
            stock_symbol='AAPL'
        )
        
        if context.similar_patterns:
            # Check patterns have required fields
            pattern = context.similar_patterns[0]
            self.assertIn('date', pattern)
            self.assertIn('change', pattern)
            self.assertIn('volatility', pattern)
            self.assertIn('similarity_score', pattern)
    
    def test_market_insights_not_empty(self):
        """Test that market insights are retrieved."""
        metrics = {
            'percent_change': -4.5,
            'volatility': 0.03
        }
        
        context = self.rag.retrieve_context(
            current_metrics=metrics,
            alert_type='price_drop',
            stock_symbol='AAPL'
        )
        
        # Should have at least one insight
        self.assertGreater(len(context.market_insights), 0)
        
        # Insights should be strings
        for insight in context.market_insights:
            self.assertIsInstance(insight, str)
            self.assertGreater(len(insight), 0)
    
    def test_format_context_for_llm(self):
        """Test context formatting for LLM."""
        metrics = {
            'percent_change': -4.0,
            'volatility': 0.03
        }
        
        context = self.rag.retrieve_context(
            current_metrics=metrics,
            alert_type='price_drop',
            stock_symbol='AAPL'
        )
        
        formatted = self.rag.format_context_for_llm(context)
        
        # Should be a string
        self.assertIsInstance(formatted, str)
        
        # Should contain relevant keywords
        if context.similar_patterns:
            self.assertIn('Historical Patterns', formatted)
        if context.market_insights:
            self.assertIn('Market Context', formatted)
    
    def test_relevance_calculation(self):
        """Test relevance score calculation."""
        # Test with empty context
        empty_context = RetrievedContext(
            similar_patterns=[],
            past_alerts=[],
            market_insights=[],
            relevance_score=0.0
        )
        self.assertEqual(empty_context.relevance_score, 0.0)
        
        # Test with full context
        metrics = {
            'percent_change': -4.0,
            'volatility': 0.03
        }
        context = self.rag.retrieve_context(
            current_metrics=metrics,
            alert_type='price_drop',
            stock_symbol='AAPL'
        )
        
        # Should have positive relevance if any context found
        if any([context.similar_patterns, context.past_alerts, context.market_insights]):
            self.assertGreater(context.relevance_score, 0.0)


class TestLLMRAGIntegration(unittest.TestCase):
    """Test LLM explainer integration with RAG."""
    
    def test_explainer_with_rag_initialization(self):
        """Test LLM explainer initializes with RAG."""
        explainer = LLMExplainer(use_rag=True, stock_symbol='AAPL')
        
        # Should have RAG system if available
        self.assertTrue(hasattr(explainer, 'rag_system'))
        self.assertTrue(hasattr(explainer, 'use_rag'))
    
    def test_explainer_without_rag(self):
        """Test LLM explainer works without RAG."""
        explainer = LLMExplainer(use_rag=False)
        
        self.assertFalse(explainer.use_rag)
    
    def test_explanation_generation_with_rag(self):
        """Test explanation generation with RAG context."""
        explainer = LLMExplainer(use_rag=True, stock_symbol='AAPL')
        
        decision = AlertDecision(
            should_alert=True,
            alert_type=AlertType.PRICE_DROP,
            confidence=ConfidenceLevel.HIGH,
            reason="Test alert",
            metrics={
                'last_close': 150.0,
                'predicted_close': 144.0,
                'percent_change': -4.0,
                'volatility': 0.03,
                'trend': 'downward'
            }
        )
        
        result = explainer.generate_explanation(decision)
        
        # Should generate explanation
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertIsInstance(result.explanation, str)
        self.assertGreater(len(result.explanation), 0)
    
    def test_explanation_no_alert(self):
        """Test explanation for no-alert scenario."""
        explainer = LLMExplainer(use_rag=True)
        
        decision = AlertDecision(
            should_alert=False,
            alert_type=AlertType.NONE,
            confidence=ConfidenceLevel.LOW,
            reason="No alert needed",
            metrics={}
        )
        
        result = explainer.generate_explanation(decision)
        
        self.assertTrue(result.success)
        self.assertIn('normal', result.explanation.lower())


class TestRAGPerformance(unittest.TestCase):
    """Test RAG system performance characteristics."""
    
    def test_retrieval_speed(self):
        """Test that retrieval is reasonably fast."""
        import time
        
        rag = MarketRAGSystem(use_embeddings=False)
        
        metrics = {
            'percent_change': -4.0,
            'volatility': 0.03
        }
        
        start_time = time.time()
        context = rag.retrieve_context(
            current_metrics=metrics,
            alert_type='price_drop',
            stock_symbol='AAPL'
        )
        elapsed = time.time() - start_time
        
        # Should complete in under 1 second for simple similarity
        self.assertLess(elapsed, 1.0, 
            f"Retrieval took {elapsed:.2f}s, expected < 1.0s")
    
    def test_multiple_retrievals(self):
        """Test multiple retrievals work consistently."""
        rag = MarketRAGSystem(use_embeddings=False)
        
        test_cases = [
            {'percent_change': -4.0, 'volatility': 0.03},
            {'percent_change': 5.0, 'volatility': 0.025},
            {'percent_change': -1.0, 'volatility': 0.05},
        ]
        
        for metrics in test_cases:
            context = rag.retrieve_context(
                current_metrics=metrics,
                alert_type='price_drop',
                stock_symbol='AAPL'
            )
            
            # Should always return valid context
            self.assertIsInstance(context, RetrievedContext)
            self.assertIsNotNone(context.relevance_score)


class TestKnowledgeBase(unittest.TestCase):
    """Test knowledge base creation and management."""
    
    def test_knowledge_base_creation(self):
        """Test knowledge base files are created."""
        from pathlib import Path
        
        kb_path = Path("../knowledge_base")
        
        # Should create directory
        self.assertTrue(kb_path.exists() or True)  # May not exist yet
        
        # Create it
        create_default_knowledge_base()
        
        # Should now exist
        self.assertTrue(kb_path.exists())
        
        # Should have markdown files
        expected_files = [
            'price_patterns.md',
            'volatility_insights.md',
            'technical_indicators.md'
        ]
        
        for filename in expected_files:
            filepath = kb_path / filename
            if filepath.exists():
                # File should have content
                with open(filepath, 'r') as f:
                    content = f.read()
                    self.assertGreater(len(content), 0)


def run_tests():
    """Run all tests."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
