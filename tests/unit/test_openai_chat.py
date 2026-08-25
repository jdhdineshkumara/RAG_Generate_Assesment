from app.domain.entities import RetrievedChunk
from app.infrastructure.providers.openai_chat import OpenAIChatProvider


class Response:
    def __init__(self, content):
        self.content = content


class FakeChat:
    def __init__(self, response):
        self.response = response
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return Response(self.response)


def test_prompt_instructs_date_comparison_and_uses_source_context():
    provider = OpenAIChatProvider(
        "test-key", "test-model", "I cannot find the information you have requested"
    )
    fake_chat = FakeChat("No, the last working day was 07 August 2026.")
    provider._chat = fake_chat

    answer = provider.answer(
        "may i need to work on 12th August 2026",
        [
            RetrievedChunk(
                "chunk",
                "My last working day will be 07 August 2026.",
                "doc",
                "resignation.pdf",
                1,
                0.9,
            )
        ],
    )

    assert answer.startswith("No")
    assert "last working day" in fake_chat.messages.messages[0].content
    assert "07 August 2026" in fake_chat.messages.messages[1].content


def test_prompt_normalizes_model_fallback_to_exact_configured_message():
    fallback = "I cannot find the information you have requested"
    provider = OpenAIChatProvider("test-key", "test-model", fallback)
    provider._chat = FakeChat("I cannot find the information you have requested.")

    answer = provider.answer(
        "What is missing?",
        [RetrievedChunk("chunk", "No relevant text.", "doc", "file.pdf", 1, 0.9)],
    )

    assert answer == fallback
