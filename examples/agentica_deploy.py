"""Example: Deploy via Agentica with type-safe scope objects."""

import asyncio

from clawbridge import ClawAgent, ClawBridge, ModelConfig, ToolDefinition


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
        model_id="claude-sonnet-4-20250514",
    ),
    tools=[
        ToolDefinition(
            name="analyzer",
            description="Data analysis toolkit",
            callable=analyzer,  # Pass the live object!
        ),
    ],
)

bridge = ClawBridge(agent, backend="agentica")


async def main():
    # Agentica excels at letting agents interact with live objects
    response = await bridge.achat("Analyze the sales data in data/sales.csv")
    print(response)


asyncio.run(main())