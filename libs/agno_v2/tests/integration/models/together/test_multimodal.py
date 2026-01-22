from agno_v2.agent import Agent
from agno_v2.media import Image
from agno_v2.models.together import Together


def test_image_input():
    agent = Agent(model=Together(id="meta-llama/Llama-Vision-Free"), markdown=True, telemetry=False)

    response = agent.run(
        "Tell me about this image and give me the latest news about it.",
        images=[Image(url="https://upload.wikimedia.org/wikipedia/commons/0/0c/GoldenGateBridge-001.jpg")],
    )

    assert response.content is not None
    assert "golden" in response.content.lower()
