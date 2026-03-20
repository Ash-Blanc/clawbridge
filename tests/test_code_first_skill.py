import pytest
from pathlib import Path
from clawbridge.core.skill import ClawSkill

def test_code_first_skill(tmp_path: Path):
    # Create a skill directory with NO SKILL.md, only tools.py
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    
    tools_py_content = """
def fetch_weather(location: str, days: int = 1) -> str:
    \"\"\"Fetches the weather for a given location.\"\"\"
    return f"Weather in {location} for {days} days."
"""
    (skill_dir / "tools.py").write_text(tools_py_content)
    
    # Load the skill
    skill = ClawSkill.from_dir(skill_dir)
    
    # Assertions
    assert skill.name == "test_skill"
    assert skill.description == "Auto-generated from Python callables."
    assert len(skill.tools) == 1
    
    tool = skill.tools[0]
    assert tool.name == "fetch_weather"
    assert tool.description == "Fetches the weather for a given location."
    
    # Validate parameters
    params = {p.name: p for p in tool.parameters}
    assert "location" in params
    assert params["location"].type == "str"
    assert params["location"].required is True
    
    assert "days" in params
    assert params["days"].type == "int"
    assert params["days"].required is False
