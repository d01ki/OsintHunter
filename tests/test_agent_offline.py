import pytest

from osinthunter.agent import OSINTAgent
from osinthunter.models import ProblemInput


def test_run_offline_basic():
    agent = OSINTAgent()
    problem = ProblemInput(text="Investigate http://example.com and ip 8.8.8.8 @user")
    result = agent.run(problem)
    assert result.plan  # planner returns steps
    assert result.evidence  # should gather some evidence offline
    # Flag detection should be empty for non-flag text
    assert all("flag{" not in ev.fact.lower() for ev in result.evidence)


def test_run_offline_no_input():
    agent = OSINTAgent()
    problem = ProblemInput(text="")
    result = agent.run(problem)
    assert result.plan
    # Evidence may be sparse but should still be a list
    assert isinstance(result.evidence, list)
