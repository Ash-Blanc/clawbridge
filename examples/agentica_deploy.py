"""Example: Deploy via Agentica with type-safe scope objects."""

from clawbridge import ClawAgent, ModelConfig, ToolDefinition, build_agentica_agent


class DataAnalyzer:
    """A typed scope object for Agentica — the agent can call its methods."""

    def analyze_csv(self, path: str) -> dict:
        """Analyze a CSV file and return summary statistics."""
        return {"rows": 100, "columns": 5, "path": path}

    def plot(self, data: dict, chart_type: str = "bar") -> str:
        """Generate a chart from data."""
        return f"Chart ({chart_type}) generated for {len(data)} data points"


analyzer = DataAnalyzer()

agent = ClawAgent(
    name="DataClaw",
    description="A data analysis assistant",
    model=ModelConfig(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
    ),
    tools=[
        ToolDefinition(
            name="analyzer",
            description="Data analysis toolkit",
            callable=analyzer,
        ),
    ],
)

# Build the Agentica config — returns scope-based config rather than a long-lived runtime
agentica_config = build_agentica_agent(agent)

# Agentica uses scope objects — show the compiled config
print(f"Agent: {agent.name}")
print(f"Scope objects: {list(agentica_config.scope.keys())}")
print(f"Model: {agentica_config.model}")
