#!/usr/bin/env python3
"""
LightCrew + OpenAI minimal demo.

Single-agent, single-task crew that calls OpenAI to answer a user query.
"""

# Ensure repository root is on sys.path for `import lightcrew` when running from showcases/
import sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import os
import asyncio
import argparse
from typing import Dict, Any

from lightcrew import Agent, Task, Crew
from lightcrew.utils import get_logger
from lightcrew.utils.llm_providers import OpenAIProvider

logger = get_logger(__name__)


async def run_once(query: str, model: str, temperature: float, timeout: float, api_key: str | None) -> str:
    """Execute a single OpenAI-backed task via LightCrew."""
    # Prefer explicit api_key if provided; else rely on env OPENAI_API_KEY
    provider = OpenAIProvider(model=model, api_key=api_key)

    agent = Agent(
        role="Helpful Assistant",
        goal="Answer user questions clearly and concisely",
        backstory="You are a helpful AI assistant.",
        llm=provider,  # pass provider instance so api_key is honored
        llm_model=model,
        config={"timeout": timeout, "temperature": temperature}
    )

    task = Task(
        description=query,
        agent=agent,
        expected_output="A short, direct answer to the user's question."
    )

    crew = Crew(agents=[agent], tasks=[task])

    result = await crew.execute()
    if result.success and result.results:
        return result.results[0].output or ""
    raise RuntimeError(result.results[0].error if result.results else "Unknown error")


async def main():
    parser = argparse.ArgumentParser(description="LightCrew OpenAI Minimal Demo")
    parser.add_argument("--query", "-q", type=str, help="User query to answer")
    parser.add_argument("--model", "-m", type=str, default="gpt-4o-mini", help="OpenAI model")
    parser.add_argument("--temperature", type=float, default=0.7, help="Generation temperature")
    parser.add_argument("--timeout", type=float, default=60.0, help="Agent timeout (seconds)")
    parser.add_argument("--api-key", type=str, help="OpenAI API key (optional; else use env OPENAI_API_KEY)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set. You can also pass --api-key.")

    if args.interactive:
        print("LightCrew OpenAI Minimal Demo (type 'quit' to exit)")
        while True:
            try:
                q = input("\nEnter your question: ").strip()
                if q.lower() in {"quit", "exit", "q"}:
                    break
                if not q:
                    print("Please enter a non-empty question.")
                    continue

                try:
                    answer = await run_once(q, args.model, args.temperature, args.timeout, api_key)
                    print("\nAnswer:\n" + answer)
                except Exception as e:
                    print(f"\nError: {e}")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
    else:
        if not args.query:
            parser.print_help()
            print("\nExample:")
            print("  python showcases/openai_minimal/main.py --query 'What is the capital of France?' --model gpt-4o-mini")
            return

        try:
            answer = await run_once(args.query, args.model, args.temperature, args.timeout, api_key)
            print(answer)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

