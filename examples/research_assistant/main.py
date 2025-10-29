#!/usr/bin/env python3
"""
Research Assistant Demo - LightCrew Framework
Tự động research topics và tạo comprehensive reports.
"""

# Ensure the repository root is on sys.path so `import lightcrew` works when
# running this script from the showcases subfolder (prevents ModuleNotFoundError).
import sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import asyncio
import argparse
import json
from pathlib import Path
from typing import Dict, Any
# Optional dependency: PyYAML. Fallback to defaults if unavailable.
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

# Import LightCrew framework
from lightcrew import Agent, Task, Crew, Settings
from lightcrew.tools import tool
from lightcrew.utils import get_logger

logger = get_logger(__name__)


@tool(name="web_search", description="Search the web for information")
def web_search(query: str, max_results: int = 10) -> dict:
    """
    Search the web for information about a query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary with search results
    """
    # Mock implementation - in real scenario, use SERP API or similar
    mock_results = {
        "query": query,
        "results": [
            {
                "title": f"Research on {query} - Industry Report",
                "url": "https://example.com/report1",
                "snippet": f"Comprehensive analysis of {query} showing significant growth trends and market opportunities.",
                "source": "Industry Research Institute"
            },
            {
                "title": f"{query}: Market Analysis 2024",
                "url": "https://example.com/analysis",
                "snippet": f"Latest market data and forecasts for {query} sector with detailed statistics.",
                "source": "Market Research Firm"
            },
            {
                "title": f"Expert Insights on {query}",
                "url": "https://example.com/insights",
                "snippet": f"Leading experts share their perspectives on {query} and future implications.",
                "source": "Expert Panel"
            }
        ],
        "total_found": max_results
    }
    
    logger.info(f"Web search completed for: {query}")
    return mock_results


@tool(name="document_analyzer", description="Analyze documents and extract key insights")
def document_analyzer(content: str, analysis_type: str = "comprehensive") -> dict:
    """
    Analyze document content and extract key insights.
    
    Args:
        content: Document content to analyze
        analysis_type: Type of analysis (summary, comprehensive, technical)
        
    Returns:
        Dictionary with analysis results
    """
    # Mock analysis - in real scenario, use NLP libraries
    analysis = {
        "key_points": [
            "Market showing strong growth trajectory",
            "Technology adoption accelerating",
            "Regulatory environment evolving",
            "Investment opportunities emerging"
        ],
        "sentiment": "positive",
        "confidence": 0.85,
        "topics": ["market trends", "technology", "regulation", "investment"],
        "summary": f"Analysis of the provided content reveals significant insights about the topic with {analysis_type} depth.",
        "word_count": len(content.split()),
        "reading_time": len(content.split()) // 200  # words per minute
    }
    
    logger.info(f"Document analysis completed: {analysis_type}")
    return analysis


@tool(name="report_generator", description="Generate structured research reports")
def report_generator(research_data: dict, format_type: str = "markdown") -> str:
    """
    Generate a structured research report from collected data.
    
    Args:
        research_data: Collected research data
        format_type: Output format (markdown, html, pdf)
        
    Returns:
        Formatted report string
    """
    topic = research_data.get("topic", "Research Topic")
    findings = research_data.get("findings", [])
    sources = research_data.get("sources", [])
    
    report = f"""# Research Report: {topic}

## Executive Summary

This comprehensive research report provides an in-depth analysis of {topic} based on extensive data collection and analysis from multiple authoritative sources.

## Key Findings

"""
    
    for i, finding in enumerate(findings, 1):
        report += f"{i}. {finding}\n"
    
    report += f"""

## Detailed Analysis

Based on our research methodology, we have identified several critical trends and patterns:

- **Market Dynamics**: The sector shows strong growth indicators
- **Technology Trends**: Innovation driving transformation
- **Competitive Landscape**: Key players establishing market positions
- **Future Outlook**: Positive trajectory with emerging opportunities

## Recommendations

1. **Strategic Focus**: Prioritize high-impact areas identified in the analysis
2. **Investment Considerations**: Evaluate opportunities based on market trends
3. **Risk Management**: Monitor regulatory and competitive developments
4. **Innovation Strategy**: Leverage technology trends for competitive advantage

## Methodology

This research employed a multi-source approach including:
- Web-based information gathering
- Document analysis and synthesis
- Expert insight compilation
- Trend analysis and forecasting

## Sources

"""
    
    for i, source in enumerate(sources, 1):
        report += f"[{i}] {source.get('title', 'Unknown')} - {source.get('source', 'Unknown Source')}\n"
    
    report += f"""

---
*Report generated by LightCrew Research Assistant*
*Generated on: {asyncio.get_event_loop().time()}*
"""
    
    logger.info(f"Report generated in {format_type} format")
    return report


class ResearchAssistant:
    """Main Research Assistant class using LightCrew framework."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Research Assistant."""
        self.config = self._load_config(config_path)
        self.settings = Settings()
        
        # Create research agent
        self.research_agent = Agent(
            role="Senior Research Analyst",
            goal="Conduct comprehensive research and generate insightful reports",
            backstory="I am an expert researcher with extensive experience in data analysis, "
                     "information synthesis, and report generation across various industries.",
            llm="mock",  # Using mock LLM for demo
            tools=[web_search, document_analyzer, report_generator]
        )
        
        logger.info("Research Assistant initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if yaml is None:
                logger.warning("PyYAML not installed; using default configuration")
                return self._get_default_config()
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "research_agent": {
                "max_sources": 10,
                "search_depth": "comprehensive",
                "output_format": "markdown"
            },
            "search_config": {
                "timeout": 30,
                "retry_count": 3
            }
        }
    
    async def research_topic(self, topic: str, depth: str = "standard") -> str:
        """
        Research a topic and generate a comprehensive report.
        
        Args:
            topic: Research topic
            depth: Research depth (basic, standard, comprehensive)
            
        Returns:
            Generated research report
        """
        logger.info(f"Starting research on topic: {topic}")
        
        # Create research task
        research_task = Task(
            description=f"""
            Conduct comprehensive research on the topic: "{topic}"
            
            Your research should include:
            1. Web search for current information and trends
            2. Analysis of found documents and sources
            3. Synthesis of key findings and insights
            4. Generation of a structured report with recommendations
            
            Research depth: {depth}
            
            Use the available tools to:
            - Search for relevant information using web_search
            - Analyze documents using document_analyzer  
            - Generate the final report using report_generator
            
            Ensure the report is comprehensive, well-structured, and includes proper source citations.
            """,
            agent=self.research_agent,
            expected_output="A comprehensive research report in markdown format with executive summary, key findings, analysis, and recommendations."
        )
        
        # Create crew with single agent and task
        research_crew = Crew(
            agents=[self.research_agent],
            tasks=[research_task]
        )
        
        # Execute research
        try:
            result = await research_crew.execute({
                "topic": topic,
                "depth": depth,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            if result.success:
                logger.info("Research completed successfully")
                return result.results[0].output
            else:
                logger.error("Research failed")
                return f"Research failed: {result.results[0].error if result.results else 'Unknown error'}"
                
        except Exception as e:
            logger.error(f"Research execution error: {e}")
            return f"Research execution failed: {str(e)}"
    
    def save_report(self, report: str, filename: str = None) -> str:
        """Save report to file."""
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_report_{timestamp}.md"
        
        output_path = Path("reports") / filename
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Report saved to: {output_path}")
        return str(output_path)


async def main():
    """Main function for CLI interface."""
    parser = argparse.ArgumentParser(description="LightCrew Research Assistant Demo")
    parser.add_argument("--topic", "-t", type=str, help="Research topic")
    parser.add_argument("--depth", "-d", choices=["basic", "standard", "comprehensive"], 
                       default="standard", help="Research depth")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    parser.add_argument("--config", "-c", type=str, default="config.yaml",
                       help="Configuration file path")
    
    args = parser.parse_args()
    
    # Initialize Research Assistant
    assistant = ResearchAssistant(args.config)
    
    if args.interactive:
        print("🔍 LightCrew Research Assistant - Interactive Mode")
        print("=" * 50)
        
        while True:
            try:
                topic = input("\nEnter research topic (or 'quit' to exit): ").strip()
                if topic.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not topic:
                    print("Please enter a valid topic.")
                    continue
                
                depth = input("Research depth [basic/standard/comprehensive] (default: standard): ").strip()
                if not depth:
                    depth = "standard"
                
                print(f"\n🔄 Researching '{topic}' with {depth} depth...")
                
                # Perform research
                report = await assistant.research_topic(topic, depth)
                
                print("\n📊 Research Report Generated:")
                print("=" * 50)
                print(report)
                
                # Ask if user wants to save
                save_choice = input("\nSave report to file? (y/n): ").strip().lower()
                if save_choice in ['y', 'yes']:
                    filename = input("Enter filename (press Enter for auto-generated): ").strip()
                    saved_path = assistant.save_report(report, filename if filename else None)
                    print(f"✅ Report saved to: {saved_path}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    elif args.topic:
        print(f"🔍 Researching: {args.topic}")
        print(f"📊 Depth: {args.depth}")
        print("=" * 50)
        
        # Perform research
        report = await assistant.research_topic(args.topic, args.depth)
        
        print("\n📊 Research Report:")
        print("=" * 50)
        print(report)
        
        # Save if output specified
        if args.output:
            assistant.save_report(report, args.output)
            print(f"\n✅ Report saved to: {args.output}")
    
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python main.py --topic 'AI Agent Market Trends' --depth comprehensive")
        print("  python main.py --interactive")


if __name__ == "__main__":
    asyncio.run(main())
