"""Example: Deploy an OpenClaw-style agent via Agno."""

from pathlib import Path

from clawbridge import (
    ClawAgent,
    ClawMemory,
    ClawSkill,
    ModelConfig,
    ToolDefinition,
    build_agno_agent,
)


# 1. Define a custom tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # In practice, wire to DuckDuckGo, Tavily, etc.
    return f"Search results for: {query}"


def read_file(path: str) -> str:
    """Read a file from disk."""
    return Path(path).read_text()


def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    import urllib.request
    with urllib.request.urlopen(url) as resp:  # noqa: S310
        return resp.read().decode(errors="replace")


# 2. Load OpenClaw-format skills
skills = []
skill_dir = Path("./skills/web_search")
if skill_dir.exists():
    skills.append(ClawSkill.from_skill_md(skill_dir))

# 3. Define the agent (OpenClaw-style spec)
agent = ClawAgent(
    name="Molty",
    description="A personal AI assistant inspired by OpenClaw",
    personality=(
        "You are Molty 🦞, a helpful and slightly witty personal AI assistant. "
        "You get things done efficiently. You remember context across conversations. "
        "When you don't know something, you search for it."
    ),
    role="Personal assistant with web search and file management capabilities",
    model=ModelConfig(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        api_key_env="ANTHROPIC_API_KEY",
    ),
    skills=skills,
    tools=[
        ToolDefinition(
            name="search_web",
            description="Search the web for information",
            callable=search_web,
        ),
        ToolDefinition(
            name="read_file",
            description="Read a local file",
            callable=read_file,
        ),
        ToolDefinition(
            name="fetch_url",
            description="Fetch content from a URL",
            callable=fetch_url,
        ),
    ],
    autonomous=True,
    markdown_output=True,
)

# 4. Build the native Agno agent
native_agent = build_agno_agent(agent)

# 5. Run a query (requires ANTHROPIC_API_KEY at runtime)
response = native_agent.run("What's the latest on AI agents?")
print(getattr(response, "content", response))

# 6. Memory helpers are separate from the runtime
memory = ClawMemory()
memory.remember("user_name", "Alice", category="preference")
memory.remember("timezone", "US/Pacific", category="preference")
print(memory.recall("user_name"))
