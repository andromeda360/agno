from agno_v2.agent import Agent
from agno_v2.media import Image
from agno_v2.models.xai import xAI
from agno_v2.tools.duckduckgo import DuckDuckGoTools


def test_image_input():
    agent = Agent(
        model=xAI(id="grok-2-vision-1212"),
        tools=[DuckDuckGoTools(cache_results=True)],
        markdown=True,
        telemetry=False,
    )

    response = agent.run(
        "Tell me about this image and give me the latest news about it.",
        images=[Image(url="https://upload.wikimedia.org/wikipedia/commons/0/0c/GoldenGateBridge-001.jpg")],
    )

    assert response.content is not None
    assert "golden" in response.content.lower()
