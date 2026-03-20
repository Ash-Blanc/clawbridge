"""Example: Deploy an OpenClaw-style agent via Agno."""

from pathlib import Path

from clawbridge import (
    ClawAgent,
    ClawBridge,
    ClawSkill,
    ModelConfig,
    ToolDefinition,
)


# 1. Define a custom tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # In practice, wire to DuckDuckGo, Tavily, etc.
    return f"Search results for: {query}"


def read_file(path: str) -> str:
    """Read a file from disk."""
    return Path(path).read_text()


# 2. Load OpenClaw-format skills
skills = []
skill_dir = Path("./skills/web_search")
if skill_dir.exists():
    skills.append(ClawSkill.from_skill_md(skill_dir))

# 3. Define the agent (universal, framework-agnostic)
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
        model_id="claude-sonnet-4-20250514",
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
    ],
    autonomous=True,
    markdown_output=True,
)

# 4. Deploy via Agno
bridge = ClawBridge(agent, backend="agno")
print(bridge)
# → ClawBridge(agent='Molty', backend='agno', skills=1, tools=2)

# 5. Chat!
response = bridge.chat("What's the latest on AI agents?")
print(response)

# 6. Memory persists
bridge.memory.remember("user_name", "Alice", category="preference")
bridge.memory.remember("timezone", "US/Pacific", category="preference")

# 7. Hot-swap to Agentica backend (same agent, same memory!)
bridge.switch_backend("agentica")
response = bridge.chat("What's my name?")  # Memory carries over
print(response)