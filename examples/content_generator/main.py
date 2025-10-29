#!/usr/bin/env python3
"""
Content Generator Demo - LightCrew Framework
Multi-agent system: Researcher → Writer → Editor
"""

# Ensure repository root is on sys.path so `import lightcrew` works when
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
from typing import Dict, Any, List
# Optional dependency: PyYAML. Fallback to defaults if unavailable.
try:
    import yaml  # type: ignore
except Exception:
    yaml = None
from dataclasses import dataclass

from lightcrew import Agent, Task, Crew, Settings, ExecutionMode
from lightcrew.tools import tool
from lightcrew.utils import get_logger

logger = get_logger(__name__)


@dataclass
class ContentBrief:
    """Content generation brief."""
    topic: str
    content_type: str = "blog_post"
    target_audience: str = "general"
    tone: str = "professional"
    length: int = 1000
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class ContentResult:
    """Generated content result."""
    title: str
    body: str
    meta_description: str
    seo_score: int
    readability_score: int
    word_count: int
    research_sources: List[str]
    generation_time: float


@tool(name="research_content", description="Research information for content creation")
def research_content(topic: str, content_type: str, depth: str = "standard") -> dict:
    """
    Research information and gather data for content creation.
    
    Args:
        topic: Content topic to research
        content_type: Type of content (blog_post, article, social_media)
        depth: Research depth (basic, standard, comprehensive)
        
    Returns:
        Research data dictionary
    """
    # openai research data - in real scenario, integrate with search APIs
    research_data = {
        "topic": topic,
        "key_points": [
            f"Current trends in {topic}",
            f"Market statistics for {topic}",
            f"Expert opinions on {topic}",
            f"Future predictions for {topic}",
            f"Case studies related to {topic}"
        ],
        "statistics": [
            f"85% growth in {topic} sector",
            f"$2.3B market size for {topic}",
            f"67% of companies adopting {topic}",
            f"40% efficiency improvement with {topic}"
        ],
        "expert_quotes": [
            f"'{topic} is transforming the industry' - Industry Expert",
            f"'The future of {topic} looks promising' - Research Director",
            f"'Companies must adapt to {topic} trends' - Consultant"
        ],
        "sources": [
            f"Industry Report on {topic} 2024",
            f"Market Analysis: {topic} Trends",
            f"Expert Survey: {topic} Impact",
            f"Case Study: {topic} Implementation"
        ],
        "related_topics": [
            f"{topic} applications",
            f"{topic} challenges",
            f"{topic} benefits",
            f"{topic} best practices"
        ],
        "content_angles": [
            f"How {topic} is changing business",
            f"Top 5 {topic} trends to watch",
            f"Getting started with {topic}",
            f"Common {topic} mistakes to avoid"
        ]
    }
    
    logger.info(f"Research completed for topic: {topic}")
    return research_data


@tool(name="write_content", description="Write engaging content based on research")
def write_content(research_data: dict, brief: dict, structure: str = "standard") -> dict:
    """
    Write content based on research data and content brief.
    
    Args:
        research_data: Research information
        brief: Content brief with requirements
        structure: Content structure type
        
    Returns:
        Written content dictionary
    """
    topic = research_data.get("topic", "Topic")
    content_type = brief.get("content_type", "blog_post")
    tone = brief.get("tone", "professional")
    target_length = brief.get("length", 1000)
    
    # Generate title
    title = f"The Complete Guide to {topic}: Trends, Insights, and Future Outlook"
    
    # Generate meta description
    meta_description = f"Discover the latest trends and insights about {topic}. " \
                      f"Expert analysis, statistics, and actionable recommendations for professionals."
    
    # Generate content body based on structure
    if content_type == "blog_post":
        body = f"""# {title}

## Introduction

In today's rapidly evolving landscape, {topic} has emerged as a critical factor for success. This comprehensive guide explores the current state, emerging trends, and future implications of {topic}.

## Current Market Landscape

Recent research indicates significant growth in the {topic} sector:

- **Market Growth**: 85% year-over-year expansion
- **Adoption Rate**: 67% of companies now implementing {topic} solutions
- **Investment**: $2.3B in funding allocated to {topic} initiatives
- **Efficiency Gains**: 40% improvement in operational efficiency

## Key Trends Shaping the Future

### 1. Technology Integration
{topic} is increasingly integrated with advanced technologies, creating new opportunities for innovation and efficiency.

### 2. Market Expansion
The {topic} market continues to expand globally, with emerging markets showing particular promise.

### 3. Regulatory Evolution
Regulatory frameworks are adapting to accommodate {topic} developments, providing clearer guidelines for implementation.

## Expert Insights

Industry leaders share their perspectives on {topic}:

> "{topic} is transforming the industry in ways we never imagined. Organizations that embrace these changes will have a significant competitive advantage." - Industry Expert

> "The future of {topic} looks incredibly promising. We're seeing unprecedented innovation and adoption rates." - Research Director

## Implementation Strategies

### Getting Started
1. **Assessment**: Evaluate current capabilities and needs
2. **Planning**: Develop a comprehensive {topic} strategy
3. **Pilot Program**: Start with small-scale implementation
4. **Scaling**: Expand successful initiatives organization-wide

### Best Practices
- Focus on user experience and adoption
- Invest in training and change management
- Monitor metrics and adjust strategies
- Stay updated with latest developments

## Common Challenges and Solutions

### Challenge 1: Resource Allocation
**Solution**: Prioritize high-impact initiatives and secure executive buy-in

### Challenge 2: Technical Integration
**Solution**: Work with experienced partners and invest in proper infrastructure

### Challenge 3: Change Management
**Solution**: Implement comprehensive training programs and communication strategies

## Future Outlook

The {topic} landscape will continue evolving with:
- Increased automation and AI integration
- Enhanced user experiences
- Greater regulatory clarity
- Expanded market opportunities

## Conclusion

{topic} represents a significant opportunity for organizations willing to invest in the future. By understanding current trends, implementing best practices, and staying ahead of developments, businesses can leverage {topic} for sustainable competitive advantage.

The key to success lies in strategic planning, proper execution, and continuous adaptation to changing market conditions. Organizations that take action now will be best positioned for future success.

## Key Takeaways

1. **Market Growth**: {topic} sector showing strong expansion
2. **Strategic Importance**: Critical for competitive advantage
3. **Implementation**: Start with pilot programs and scale gradually
4. **Future Focus**: Continuous innovation and adaptation required

---

*This analysis is based on current market research and expert insights. Stay updated with the latest {topic} developments for continued success.*
"""
    
    elif content_type == "technical_article":
        body = f"""# Technical Deep Dive: {topic} Implementation and Best Practices

## Abstract

This technical article provides an in-depth analysis of {topic} implementation, covering architecture considerations, best practices, and performance optimization strategies.

## Introduction

{topic} has become a cornerstone technology in modern systems architecture. This article examines the technical aspects of implementation and provides practical guidance for developers and architects.

## Technical Architecture

### Core Components
- **Data Layer**: Handles information processing and storage
- **Logic Layer**: Implements business rules and processing
- **Presentation Layer**: Manages user interfaces and interactions
- **Integration Layer**: Facilitates external system connections

### Implementation Patterns
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Layer  │────│  Service Layer  │────│   Data Layer    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────┐           ┌─────────────┐        ┌─────────────┐
    │   UI    │           │  Business   │        │  Database   │
    │ Components│         │    Logic    │        │   Storage   │
    └─────────┘           └─────────────┘        └─────────────┘
```

## Implementation Guidelines

### Phase 1: Planning and Design
1. Requirements analysis and specification
2. Architecture design and documentation
3. Technology stack selection
4. Resource planning and allocation

### Phase 2: Development
1. Core component implementation
2. Integration layer development
3. User interface creation
4. Testing and quality assurance

### Phase 3: Deployment
1. Environment preparation
2. Application deployment
3. Performance monitoring
4. User training and support

## Performance Optimization

### Database Optimization
- Index optimization for query performance
- Connection pooling for resource efficiency
- Caching strategies for frequently accessed data
- Query optimization and analysis

### Application Performance
- Code optimization and refactoring
- Memory management and garbage collection
- Asynchronous processing implementation
- Load balancing and scaling strategies

## Security Considerations

### Data Protection
- Encryption at rest and in transit
- Access control and authentication
- Audit logging and monitoring
- Compliance with security standards

### Network Security
- Secure communication protocols
- API security and rate limiting
- Firewall configuration
- Intrusion detection systems

## Monitoring and Maintenance

### Performance Metrics
- Response time and throughput
- Error rates and availability
- Resource utilization
- User experience metrics

### Maintenance Procedures
- Regular updates and patches
- Performance tuning
- Backup and recovery
- Capacity planning

## Conclusion

Successful {topic} implementation requires careful planning, proper architecture design, and ongoing optimization. By following these technical guidelines and best practices, organizations can achieve robust, scalable, and maintainable solutions.

## References

1. Technical Documentation: {topic} Architecture Guide
2. Performance Study: {topic} Optimization Strategies
3. Security Analysis: {topic} Best Practices
4. Case Study: Enterprise {topic} Implementation
"""
    
    else:  # social_media or other formats
        body = f"""🚀 {topic}: The Game-Changer You Need to Know About

The {topic} revolution is here, and it's transforming how we work, think, and innovate! 

📊 Key Stats:
• 85% growth in adoption
• $2.3B market opportunity
• 67% of companies investing
• 40% efficiency improvement

💡 Why {topic} Matters:
✅ Drives innovation and growth
✅ Improves operational efficiency  
✅ Creates competitive advantages
✅ Enables future-ready solutions

🎯 Getting Started:
1. Assess your current needs
2. Develop a strategic plan
3. Start with pilot programs
4. Scale successful initiatives

The future belongs to organizations that embrace {topic} today. Are you ready to lead the change?

#Innovation #{topic.replace(' ', '')} #Technology #BusinessGrowth #FutureOfWork

What's your experience with {topic}? Share your thoughts below! 👇
"""
    
    content_result = {
        "title": title,
        "meta_description": meta_description,
        "body": body,
        "word_count": len(body.split()),
        "content_type": content_type,
        "tone": tone,
        "structure": structure
    }
    
    logger.info(f"Content written: {content_type}, {len(body.split())} words")
    return content_result


@tool(name="edit_content", description="Edit and optimize content for quality and SEO")
def edit_content(content_data: dict, optimization_focus: str = "balanced") -> dict:
    """
    Edit and optimize content for grammar, style, and SEO.
    
    Args:
        content_data: Content to edit
        optimization_focus: Focus area (seo, readability, engagement, balanced)
        
    Returns:
        Edited content with quality scores
    """
    title = content_data.get("title", "")
    body = content_data.get("body", "")
    meta_description = content_data.get("meta_description", "")
    
    # openai editing improvements
    improvements = {
        "grammar_fixes": 5,
        "style_improvements": 8,
        "seo_optimizations": 12,
        "readability_enhancements": 6
    }
    
    # Calculate quality scores (openai calculations)
    word_count = len(body.split())
    
    # SEO Score calculation (simplified)
    seo_score = 85
    if len(title) >= 50 and len(title) <= 60:
        seo_score += 5
    if len(meta_description) >= 150 and len(meta_description) <= 160:
        seo_score += 5
    if word_count >= 800:
        seo_score += 5
    
    # Readability score (Flesch Reading Ease approximation)
    readability_score = 65  # Grade 8-9 level
    
    # Quality improvements (openai)
    edited_title = title
    edited_body = body
    edited_meta = meta_description
    
    if optimization_focus == "seo":
        # SEO-focused improvements
        seo_score = min(95, seo_score + 10)
        edited_title = f"{title} | Complete Guide 2024"
        
    elif optimization_focus == "readability":
        # Readability-focused improvements
        readability_score = min(80, readability_score + 15)
        
    elif optimization_focus == "engagement":
        # Engagement-focused improvements
        edited_title = f"🚀 {title}"
        
    edited_content = {
        "title": edited_title,
        "body": edited_body,
        "meta_description": edited_meta,
        "word_count": word_count,
        "seo_score": seo_score,
        "readability_score": readability_score,
        "improvements": improvements,
        "optimization_focus": optimization_focus,
        "quality_grade": "A" if seo_score >= 90 else "B" if seo_score >= 80 else "C"
    }
    
    logger.info(f"Content edited: SEO {seo_score}/100, Readability {readability_score}/100")
    return edited_content


class ContentGenerator:
    """Main Content Generator using LightCrew multi-agent system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Content Generator."""
        self.config = self._load_config(config_path)
        self.settings = Settings()
        
        # Create specialized agents
        self.researcher = Agent(
            role="Content Research Specialist",
            goal="Gather comprehensive information and insights for content creation",
            backstory="I am an expert researcher with deep knowledge of market trends, "
                     "data analysis, and information synthesis. I excel at finding "
                     "relevant, accurate, and engaging information for content creation.",
            llm="openai",
            tools=[research_content]
        )
        
        self.writer = Agent(
            role="Content Creator",
            goal="Create engaging, well-structured content that resonates with the target audience",
            backstory="I am a skilled content writer with expertise in various formats "
                     "and styles. I create compelling narratives that inform, engage, "
                     "and inspire readers while maintaining brand voice and objectives.",
            llm="openai",
            tools=[write_content]
        )
        
        self.editor = Agent(
            role="Quality Assurance Editor",
            goal="Optimize content for quality, readability, and SEO performance",
            backstory="I am a meticulous editor with expertise in grammar, style, "
                     "SEO optimization, and content quality assurance. I ensure "
                     "all content meets the highest standards before publication.",
            llm="openai",
            tools=[edit_content]
        )
        
        logger.info("Content Generator initialized with 3 specialized agents")
    
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
            "content_types": {
                "blog_post": {"min_length": 800, "max_length": 1500},
                "technical_article": {"min_length": 1500, "max_length": 3000},
                "social_media": {"min_length": 100, "max_length": 300}
            },
            "quality_thresholds": {
                "seo_score": 80,
                "readability_score": 60
            }
        }
    
    async def generate_content(self, brief: ContentBrief) -> ContentResult:
        """
        Generate content using the multi-agent workflow.
        
        Args:
            brief: Content generation brief
            
        Returns:
            Generated content result
        """
        logger.info(f"Starting content generation for: {brief.topic}")
        
        # Task 1: Research
        research_task = Task(
            description=f"""
            Research comprehensive information about "{brief.topic}" for {brief.content_type} creation.
            
            Focus areas:
            - Current trends and developments
            - Market statistics and data
            - Expert opinions and insights
            - Case studies and examples
            - Related topics and angles
            
            Target audience: {brief.target_audience}
            Content type: {brief.content_type}
            
            Provide detailed research data that will inform high-quality content creation.
            """,
            agent=self.researcher,
            expected_output="Comprehensive research data with key points, statistics, expert quotes, and sources."
        )
        
        # Task 2: Writing
        writing_task = Task(
            description=f"""
            Create engaging {brief.content_type} content based on the research data.
            
            Requirements:
            - Topic: {brief.topic}
            - Target length: {brief.length} words
            - Tone: {brief.tone}
            - Target audience: {brief.target_audience}
            - Keywords to include: {', '.join(brief.keywords) if brief.keywords else 'None specified'}
            
            Structure the content appropriately for {brief.content_type} format.
            Include compelling headlines, clear sections, and engaging copy.
            Ensure the content is informative, valuable, and well-organized.
            """,
            agent=self.writer,
            expected_output="Well-structured content with title, body, and meta description."
        )
        
        # Task 3: Editing
        editing_task = Task(
            description=f"""
            Edit and optimize the content for maximum quality and performance.
            
            Focus on:
            - Grammar and spelling accuracy
            - Style and tone consistency
            - SEO optimization (keywords, meta tags, structure)
            - Readability and flow
            - Content quality and engagement
            
            Optimization focus: balanced approach for {brief.content_type}
            Target audience: {brief.target_audience}
            
            Provide quality scores and improvement recommendations.
            """,
            agent=self.editor,
            expected_output="Optimized content with quality scores and improvement metrics."
        )

        # Set task dependencies properly instead of passing Task objects as context
        writing_task.add_dependency(research_task)
        editing_task.add_dependency(writing_task)
        
        # Create crew with sequential execution
        content_crew = Crew(
            agents=[self.researcher, self.writer, self.editor],
            tasks=[research_task, writing_task, editing_task],
            execution_mode=ExecutionMode.SEQUENTIAL
        )
        
        # Execute content generation workflow
        try:
            start_time = asyncio.get_event_loop().time()
            
            result = await content_crew.execute({
                "brief": brief.__dict__,
                "timestamp": start_time
            })
            
            end_time = asyncio.get_event_loop().time()
            generation_time = end_time - start_time
            
            if result.success and len(result.results) >= 3:
                # Extract results from each agent
                research_result = result.results[0].output
                writing_result = result.results[1].output
                editing_result = result.results[2].output
                
                # Parse the final edited content
                if isinstance(editing_result, dict):
                    final_content = editing_result
                else:
                    # Fallback if editing result is not structured
                    final_content = {
                        "title": f"Content about {brief.topic}",
                        "body": str(editing_result),
                        "meta_description": f"Learn about {brief.topic}",
                        "seo_score": 75,
                        "readability_score": 65,
                        "word_count": len(str(editing_result).split())
                    }
                
                # Create content result
                content_result = ContentResult(
                    title=final_content.get("title", f"Content about {brief.topic}"),
                    body=final_content.get("body", str(editing_result)),
                    meta_description=final_content.get("meta_description", f"Learn about {brief.topic}"),
                    seo_score=final_content.get("seo_score", 75),
                    readability_score=final_content.get("readability_score", 65),
                    word_count=final_content.get("word_count", 0),
                    research_sources=research_result.get("sources", []) if isinstance(research_result, dict) else [],
                    generation_time=generation_time
                )
                
                logger.info(f"Content generation completed successfully in {generation_time:.2f}s")
                return content_result
            
            else:
                logger.error("Content generation failed")
                raise Exception("Content generation workflow failed")
                
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            raise
    
    def save_content(self, content: ContentResult, filename: str = None) -> str:
        """Save generated content to file."""
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in content.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"content_{safe_title[:30]}_{timestamp}.md"
        
        output_path = Path("generated_content") / filename
        output_path.parent.mkdir(exist_ok=True)
        
        # Format content with metadata
        formatted_content = f"""---
title: "{content.title}"
meta_description: "{content.meta_description}"
word_count: {content.word_count}
seo_score: {content.seo_score}
readability_score: {content.readability_score}
generation_time: {content.generation_time:.2f}s
sources: {len(content.research_sources)}
---

{content.body}

---

## Content Metrics
- **Word Count**: {content.word_count}
- **SEO Score**: {content.seo_score}/100
- **Readability Score**: {content.readability_score}/100
- **Generation Time**: {content.generation_time:.2f} seconds
- **Research Sources**: {len(content.research_sources)}

## Research Sources
{chr(10).join(f"- {source}" for source in content.research_sources)}

---
*Generated by LightCrew Content Generator*
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        logger.info(f"Content saved to: {output_path}")
        return str(output_path)


async def main():
    """Main function for CLI interface."""
    parser = argparse.ArgumentParser(description="LightCrew Content Generator Demo")
    parser.add_argument("--brief", "-b", type=str, help="Content brief/topic")
    parser.add_argument("--type", "-t", choices=["blog_post", "technical_article", "social_media"], 
                       default="blog_post", help="Content type")
    parser.add_argument("--audience", "-a", type=str, default="general", 
                       help="Target audience")
    parser.add_argument("--tone", choices=["professional", "casual", "technical", "conversational"], 
                       default="professional", help="Content tone")
    parser.add_argument("--length", "-l", type=int, default=1000, 
                       help="Target word count")
    parser.add_argument("--keywords", "-k", type=str, nargs="+", 
                       help="SEO keywords")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    parser.add_argument("--config", "-c", type=str, default="config.yaml",
                       help="Configuration file path")
    
    args = parser.parse_args()
    
    # Initialize Content Generator
    generator = ContentGenerator(args.config)
    
    if args.interactive:
        print("✍️  LightCrew Content Generator - Interactive Mode")
        print("=" * 60)
        
        while True:
            try:
                brief_text = input("\nEnter content brief/topic (or 'quit' to exit): ").strip()
                if brief_text.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not brief_text:
                    print("Please enter a valid content brief.")
                    continue
                
                # Get content type
                content_type = input("Content type [blog_post/technical_article/social_media] (default: blog_post): ").strip()
                if not content_type:
                    content_type = "blog_post"
                
                # Get other parameters
                audience = input("Target audience (default: general): ").strip() or "general"
                tone = input("Tone [professional/casual/technical/conversational] (default: professional): ").strip() or "professional"
                
                length_input = input("Target word count (default: 1000): ").strip()
                length = int(length_input) if length_input.isdigit() else 1000
                
                keywords_input = input("SEO keywords (comma-separated, optional): ").strip()
                keywords = [k.strip() for k in keywords_input.split(",")] if keywords_input else []
                
                # Create content brief
                brief = ContentBrief(
                    topic=brief_text,
                    content_type=content_type,
                    target_audience=audience,
                    tone=tone,
                    length=length,
                    keywords=keywords
                )
                
                print(f"\n🔄 Generating {content_type} about '{brief_text}'...")
                print("   Research → Writing → Editing...")
                
                # Generate content
                content = await generator.generate_content(brief)
                
                print(f"\n✅ Content Generated Successfully!")
                print("=" * 60)
                print(f"Title: {content.title}")
                print(f"Word Count: {content.word_count}")
                print(f"SEO Score: {content.seo_score}/100")
                print(f"Readability: {content.readability_score}/100")
                print(f"Generation Time: {content.generation_time:.2f}s")
                print("=" * 60)
                print("\nContent Preview:")
                print(content.body[:500] + "..." if len(content.body) > 500 else content.body)
                
                # Ask if user wants to save
                save_choice = input("\nSave content to file? (y/n): ").strip().lower()
                if save_choice in ['y', 'yes']:
                    filename = input("Enter filename (press Enter for auto-generated): ").strip()
                    saved_path = generator.save_content(content, filename if filename else None)
                    print(f"✅ Content saved to: {saved_path}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    elif args.brief:
        # Create content brief
        brief = ContentBrief(
            topic=args.brief,
            content_type=args.type,
            target_audience=args.audience,
            tone=args.tone,
            length=args.length,
            keywords=args.keywords or []
        )
        
        print(f"✍️  Generating {args.type} content...")
        print(f"📝 Topic: {args.brief}")
        print(f"🎯 Audience: {args.audience}")
        print(f"📊 Length: {args.length} words")
        print("=" * 60)
        
        # Generate content
        content = await generator.generate_content(brief)
        
        print(f"\n✅ Content Generated Successfully!")
        print("=" * 60)
        print(f"Title: {content.title}")
        print(f"Word Count: {content.word_count}")
        print(f"SEO Score: {content.seo_score}/100")
        print(f"Readability: {content.readability_score}/100")
        print(f"Generation Time: {content.generation_time:.2f}s")
        print("=" * 60)
        print("\nGenerated Content:")
        print(content.body)
        
        # Save if output specified
        if args.output:
            generator.save_content(content, args.output)
            print(f"\n✅ Content saved to: {args.output}")
    
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python main.py --brief 'AI trends in healthcare' --type blog_post --length 1200")
        print("  python main.py --interactive")


if __name__ == "__main__":
    asyncio.run(main())
