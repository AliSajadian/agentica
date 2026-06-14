'''Prompt builder'''
from app.models.schemas import ContextChunk, Message, MessageRole
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Default system prompt ─────────────────────────────────────────────────────
DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant with access to a knowledge base.
Answer the user's question based ONLY on the provided context.
If the context doesn't contain enough information, say so honestly.
Be concise, accurate and helpful."""


class PromptBuilder:
    '''Prompt Builder'''

    def build_rag_prompt(
        self,
        question: str,
        context_chunks: list[ContextChunk],
        system_prompt: str = None
    ) -> str:
        """
        Builds a single prompt string for Ollama generate endpoint.
        Combines system prompt + context + question.
        """
        system = system_prompt or DEFAULT_SYSTEM_PROMPT
        context = self._format_context(context_chunks)

        prompt = f"""{system}

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

        logger.info("rag_prompt_built", chunks=len(context_chunks), question=question)
        return prompt

    def build_rag_messages(
        self,
        question: str,
        context_chunks: list[ContextChunk],
        system_prompt: str = None,
        history: list[Message] = None
    ) -> list[dict]:
        """
        Builds message list for Ollama chat endpoint.
        Supports conversation history.
        """
        system = system_prompt or DEFAULT_SYSTEM_PROMPT
        context = self._format_context(context_chunks)

        messages = [
            {
                "role": MessageRole.SYSTEM,
                "content": f"{system}\n\nCONTEXT:\n{context}"
            }
        ]

        # add conversation history if exists
        if history:
            for msg in history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # add current question
        messages.append({
            "role": MessageRole.USER,
            "content": question
        })

        return messages

    def _format_context(self, chunks: list[ContextChunk]) -> str:
        if not chunks:
            return "No context available."
        return "\n\n---\n\n".join(
            f"[Source: {c.metadata.get('source', 'unknown')} "
            f"| Score: {c.score:.2f}]\n{c.text}"
            for c in chunks
        )


prompt_builder = PromptBuilder()
