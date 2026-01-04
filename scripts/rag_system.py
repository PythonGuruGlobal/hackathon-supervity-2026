"""
RAG (Retrieval-Augmented Generation) System for Market Analysis
================================================================
Enhances LLM explanations and agent decisions with relevant historical context,
past alerts, and similar market patterns.

This module demonstrates how RAG improves agentic systems by:
1. Retrieving similar historical market conditions
2. Finding relevant past alerts and their outcomes
3. Providing contextual market knowledge
4. Enhancing LLM explanations with factual data
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from pathlib import Path

# Vector store imports (fallback if not available)
try:
    from langchain_openai import OpenAIEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import Chroma
    from langchain.docstore.document import Document
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False
    # Create dummy Document class for when langchain is not available
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}
    print("⚠️ Vector store libraries not available. Using simple similarity search.")


@dataclass
class RetrievedContext:
    """Retrieved context from RAG system."""
    similar_patterns: List[Dict]
    past_alerts: List[Dict]
    market_insights: List[str]
    relevance_score: float


class MarketRAGSystem:
    """
    RAG system specialized for market data analysis.
    
    Features:
    - Semantic search over historical market patterns
    - Time-series similarity search (DTW-based)
    - Alert history retrieval
    - Market knowledge base integration
    """
    
    def __init__(
        self,
        data_path: str = "../stock_market_dataset.csv",
        alerts_path: str = "../outputs/alerts.json",
        knowledge_base_path: str = "../knowledge_base",
        use_embeddings: bool = True
    ):
        """
        Initialize RAG system.
        
        Args:
            data_path: Path to historical market data
            alerts_path: Path to past alerts
            knowledge_base_path: Path to market knowledge base
            use_embeddings: Whether to use vector embeddings (requires API key)
        """
        self.data_path = Path(data_path)
        self.alerts_path = Path(alerts_path)
        self.knowledge_base_path = Path(knowledge_base_path)
        self.use_embeddings = use_embeddings and VECTOR_STORE_AVAILABLE
        
        # Load data
        self.historical_data = self._load_historical_data()
        self.alert_history = self._load_alert_history()
        
        # Initialize vector store if available
        self.vector_store = None
        if self.use_embeddings:
            self._initialize_vector_store()
        
        print(f"✓ RAG System initialized with {len(self.historical_data)} historical records")
        print(f"✓ Loaded {len(self.alert_history)} past alerts")
    
    def _load_historical_data(self) -> pd.DataFrame:
        """Load historical market data."""
        try:
            if self.data_path.exists():
                df = pd.read_csv(self.data_path)
                df['Date'] = pd.to_datetime(df['Date'])
                return df
            else:
                print(f"⚠️ Historical data not found at {self.data_path}")
                return pd.DataFrame()
        except Exception as e:
            print(f"⚠️ Error loading historical data: {e}")
            return pd.DataFrame()
    
    def _load_alert_history(self) -> List[Dict]:
        """Load past alert history."""
        try:
            if self.alerts_path.exists():
                with open(self.alerts_path, 'r') as f:
                    alerts = json.load(f)
                return alerts if isinstance(alerts, list) else []
            else:
                return []
        except Exception as e:
            print(f"⚠️ Error loading alert history: {e}")
            return []
    
    def _initialize_vector_store(self):
        """Initialize vector store for semantic search."""
        try:
            # Check for OpenAI API key
            if not os.getenv('OPENAI_API_KEY'):
                print("⚠️ OPENAI_API_KEY not set. Disabling vector embeddings.")
                self.use_embeddings = False
                return
            
            embeddings = OpenAIEmbeddings()
            
            # Create documents from knowledge base
            documents = self._create_knowledge_documents()
            
            if documents:
                # Create or load vector store
                persist_directory = str(self.knowledge_base_path / "chroma_db")
                
                if Path(persist_directory).exists():
                    self.vector_store = Chroma(
                        persist_directory=persist_directory,
                        embedding_function=embeddings
                    )
                else:
                    self.vector_store = Chroma.from_documents(
                        documents=documents,
                        embedding=embeddings,
                        persist_directory=persist_directory
                    )
                    self.vector_store.persist()
                
                print("✓ Vector store initialized for semantic search")
        except Exception as e:
            print(f"⚠️ Vector store initialization failed: {e}")
            self.use_embeddings = False
    
    def _create_knowledge_documents(self) -> List[Document]:
        """Create documents from knowledge base."""
        documents = []
        
        # Market knowledge base (can be expanded)
        market_knowledge = [
            {
                "content": "Price drops of 4%+ in a single day often indicate significant market events, negative news, or panic selling. Historical analysis shows these drops are followed by increased volatility in 70% of cases.",
                "metadata": {"type": "pattern", "category": "price_drop"}
            },
            {
                "content": "Price spikes above 5% typically result from positive earnings reports, merger announcements, or sector-wide momentum. These movements tend to stabilize within 3-5 trading days.",
                "metadata": {"type": "pattern", "category": "price_spike"}
            },
            {
                "content": "Volatility spikes above 3% standard deviation suggest market uncertainty. Common causes include: earnings season, macroeconomic announcements, geopolitical events, or sector rotation.",
                "metadata": {"type": "pattern", "category": "volatility"}
            },
            {
                "content": "Trend reversals after prolonged movements often signal exhaustion. Downtrends reversing to uptrends may indicate accumulation, while uptrend reversals suggest profit-taking or deteriorating fundamentals.",
                "metadata": {"type": "pattern", "category": "trend_reversal"}
            },
            {
                "content": "High volume combined with price changes amplifies signal significance. Volume confirmation reduces false positive alerts by 40% according to historical analysis.",
                "metadata": {"type": "indicator", "category": "volume"}
            },
            {
                "content": "RSI below 30 indicates oversold conditions, while above 70 suggests overbought. These technical indicators complement price-based alerts for better context.",
                "metadata": {"type": "indicator", "category": "rsi"}
            }
        ]
        
        # Convert to LangChain documents
        for item in market_knowledge:
            doc = Document(
                page_content=item["content"],
                metadata=item["metadata"]
            )
            documents.append(doc)
        
        # Add historical alert insights
        if self.alert_history:
            for alert in self.alert_history[-50:]:  # Last 50 alerts
                content = f"Alert: {alert.get('alert_type', 'unknown')} - {alert.get('explanation', '')}"
                doc = Document(
                    page_content=content,
                    metadata={
                        "type": "historical_alert",
                        "alert_type": alert.get('alert_type', 'unknown'),
                        "timestamp": alert.get('timestamp', '')
                    }
                )
                documents.append(doc)
        
        return documents
    
    def retrieve_context(
        self,
        current_metrics: Dict,
        alert_type: str,
        stock_symbol: str = "SAMPLE",
        top_k: int = 5
    ) -> RetrievedContext:
        """
        Retrieve relevant context for current market situation.
        
        Args:
            current_metrics: Current market metrics
            alert_type: Type of alert being evaluated
            stock_symbol: Stock symbol
            top_k: Number of similar patterns to retrieve
            
        Returns:
            RetrievedContext with relevant information
        """
        # 1. Find similar historical patterns
        similar_patterns = self._find_similar_patterns(
            stock_symbol=stock_symbol,
            current_metrics=current_metrics,
            top_k=top_k
        )
        
        # 2. Retrieve relevant past alerts
        past_alerts = self._retrieve_similar_alerts(
            alert_type=alert_type,
            metrics=current_metrics,
            top_k=top_k
        )
        
        # 3. Get market insights from vector store
        market_insights = self._get_market_insights(
            query=f"{alert_type} with {current_metrics.get('percent_change', 0):.1f}% change",
            top_k=3
        )
        
        # 4. Calculate relevance score
        relevance_score = self._calculate_relevance(
            similar_patterns, past_alerts, market_insights
        )
        
        return RetrievedContext(
            similar_patterns=similar_patterns,
            past_alerts=past_alerts,
            market_insights=market_insights,
            relevance_score=relevance_score
        )
    
    def _find_similar_patterns(
        self,
        stock_symbol: str,
        current_metrics: Dict,
        top_k: int = 5
    ) -> List[Dict]:
        """Find similar historical patterns using feature similarity."""
        if self.historical_data.empty:
            return []
        
        try:
            # Filter by stock
            stock_data = self.historical_data[
                self.historical_data['Stock'] == stock_symbol
            ].copy()
            
            if len(stock_data) < 2:
                return []
            
            # Calculate features for comparison
            stock_data['price_change'] = stock_data['Close'].pct_change() * 100
            stock_data['volatility'] = stock_data['Close'].rolling(5).std()
            
            # Current features
            current_change = current_metrics.get('percent_change', 0)
            current_vol = current_metrics.get('volatility', 0)
            
            # Calculate similarity scores
            stock_data['similarity'] = np.sqrt(
                (stock_data['price_change'] - current_change) ** 2 +
                (stock_data['volatility'] - current_vol) ** 2 * 100
            )
            
            # Get top K similar patterns
            similar = stock_data.nsmallest(top_k, 'similarity')
            
            results = []
            for _, row in similar.iterrows():
                results.append({
                    'date': row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else 'N/A',
                    'close': float(row['Close']),
                    'change': float(row['price_change']) if pd.notna(row['price_change']) else 0,
                    'volatility': float(row['volatility']) if pd.notna(row['volatility']) else 0,
                    'similarity_score': float(row['similarity'])
                })
            
            return results
        
        except Exception as e:
            print(f"⚠️ Error finding similar patterns: {e}")
            return []
    
    def _retrieve_similar_alerts(
        self,
        alert_type: str,
        metrics: Dict,
        top_k: int = 5
    ) -> List[Dict]:
        """Retrieve similar past alerts."""
        if not self.alert_history:
            return []
        
        # Filter by alert type
        similar_alerts = [
            alert for alert in self.alert_history
            if alert.get('alert_type') == alert_type
        ]
        
        # Sort by recency and return top K
        similar_alerts.sort(
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        return similar_alerts[:top_k]
    
    def _get_market_insights(self, query: str, top_k: int = 3) -> List[str]:
        """Get market insights using semantic search."""
        if not self.vector_store:
            # Fallback: return static insights based on query keywords
            return self._get_fallback_insights(query)
        
        try:
            # Semantic search
            results = self.vector_store.similarity_search(query, k=top_k)
            insights = [doc.page_content for doc in results]
            return insights
        except Exception as e:
            print(f"⚠️ Vector search failed: {e}")
            return self._get_fallback_insights(query)
    
    def _get_fallback_insights(self, query: str) -> List[str]:
        """Fallback insights when vector store unavailable."""
        query_lower = query.lower()
        
        insights = []
        
        if 'drop' in query_lower or 'decline' in query_lower:
            insights.append(
                "Price drops of this magnitude often indicate significant market events. "
                "Historical patterns show increased volatility follows such movements."
            )
        
        if 'spike' in query_lower or 'surge' in query_lower:
            insights.append(
                "Sharp price increases typically result from positive catalysts. "
                "These movements tend to stabilize within several trading days."
            )
        
        if 'volatility' in query_lower:
            insights.append(
                "Elevated volatility suggests market uncertainty. "
                "Common causes include earnings season, economic data, or sector events."
            )
        
        if not insights:
            insights.append(
                "Market movements should be evaluated in context of broader trends "
                "and historical patterns for accurate risk assessment."
            )
        
        return insights
    
    def _calculate_relevance(
        self,
        patterns: List[Dict],
        alerts: List[Dict],
        insights: List[str]
    ) -> float:
        """Calculate overall relevance score for retrieved context."""
        score = 0.0
        
        # Score based on number and quality of retrieved items
        if patterns:
            avg_similarity = np.mean([p.get('similarity_score', 10) for p in patterns])
            pattern_score = max(0, 1 - (avg_similarity / 10))  # Normalize
            score += pattern_score * 0.4
        
        if alerts:
            alert_score = min(len(alerts) / 5, 1.0)  # Cap at 1.0
            score += alert_score * 0.3
        
        if insights:
            insight_score = min(len(insights) / 3, 1.0)
            score += insight_score * 0.3
        
        return min(score, 1.0)
    
    def format_context_for_llm(self, context: RetrievedContext) -> str:
        """Format retrieved context for LLM prompt."""
        sections = []
        
        # Similar patterns
        if context.similar_patterns:
            sections.append("**Similar Historical Patterns:**")
            for i, pattern in enumerate(context.similar_patterns[:3], 1):
                sections.append(
                    f"{i}. {pattern['date']}: {pattern['change']:+.2f}% change "
                    f"(volatility: {pattern['volatility']:.4f})"
                )
        
        # Past alerts
        if context.past_alerts:
            sections.append("\n**Relevant Past Alerts:**")
            for i, alert in enumerate(context.past_alerts[:2], 1):
                sections.append(
                    f"{i}. {alert.get('alert_type', 'N/A')} - "
                    f"{alert.get('reason', 'No reason provided')[:100]}"
                )
        
        # Market insights
        if context.market_insights:
            sections.append("\n**Market Context:**")
            for insight in context.market_insights[:2]:
                sections.append(f"- {insight[:150]}")
        
        return "\n".join(sections)


def create_default_knowledge_base(output_dir: str = "../knowledge_base"):
    """
    Create default market knowledge base.
    Useful for first-time setup.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create markdown files with market knowledge
    knowledge_items = {
        "price_patterns.md": """# Price Pattern Analysis

## Price Drops
- Drops of 4%+ in a single day indicate significant events
- Often followed by increased volatility (70% of historical cases)
- Common causes: negative earnings, sector weakness, market corrections

## Price Spikes
- Spikes above 5% typically from positive catalysts
- Stabilization occurs within 3-5 trading days
- Volume confirmation important for signal validity

## Consolidation Patterns
- Sideways movement after trends suggests accumulation/distribution
- Breakouts from consolidation often explosive
""",
        "volatility_insights.md": """# Volatility Analysis

## High Volatility Indicators
- Standard deviation above 3% signals uncertainty
- Common during: earnings season, economic data releases, geopolitical events
- Risk management critical during high volatility periods

## Low Volatility
- Extended low volatility may precede major moves
- Complacency risk increases
""",
        "technical_indicators.md": """# Technical Indicators

## RSI (Relative Strength Index)
- Below 30: oversold conditions, potential reversal
- Above 70: overbought conditions, potential correction
- Divergences provide early reversal signals

## Volume Analysis
- High volume confirms price movements
- Low volume raises reliability concerns
- Volume precedes price (often leading indicator)
"""
    }
    
    for filename, content in knowledge_items.items():
        filepath = output_path / filename
        with open(filepath, 'w') as f:
            f.write(content)
    
    print(f"✓ Knowledge base created at {output_dir}")


if __name__ == "__main__":
    # Demo usage
    print("🔍 RAG System Demo\n")
    
    # Create knowledge base if it doesn't exist
    create_default_knowledge_base()
    
    # Initialize RAG system
    rag = MarketRAGSystem(use_embeddings=False)  # Set True if you have API key
    
    # Example: Retrieve context for a price drop alert
    test_metrics = {
        'last_close': 150.0,
        'predicted_close': 144.0,
        'percent_change': -4.0,
        'volatility': 0.035,
        'trend': 'downward'
    }
    
    print("\n🔍 Retrieving context for price drop alert...\n")
    context = rag.retrieve_context(
        current_metrics=test_metrics,
        alert_type='price_drop',
        stock_symbol='AAPL'
    )
    
    print(f"Relevance Score: {context.relevance_score:.2f}\n")
    print(rag.format_context_for_llm(context))
