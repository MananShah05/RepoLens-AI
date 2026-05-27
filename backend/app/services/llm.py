import httpx
import json
import re
from typing import List, Dict, Any
from app.config import get_settings

SYSTEM_PROMPTS = {
    "summary": """You are RepoLens AI, a codebase intelligence assistant. Summarize the following repository contents concisely. Include:
- What the repo does
- Major folders/modules and their purposes
- Tech stack
- Architecture notes
Use markdown. Be factual and grounded only in the provided context.""",
    "chat": """You are RepoLens AI, an expert codebase assistant. Answer the user's question using ONLY the provided code context.
Rules:
- Cite file paths when referencing code.
- Say "I don't have enough context" if unsure.
- Be concise but thorough.
- Format code snippets in markdown.""",
    "onboarding": """You are RepoLens AI. Create a beginner-friendly onboarding guide for the repository using the provided context. Include:
1. Project overview
2. Setup steps (infer from package.json, requirements.txt, README, etc.)
3. Suggested reading order (entry points)
4. Important environment variables or configuration
5. Common gotchas
Use markdown.""",
    "architecture": """You are RepoLens AI. Describe the architecture of the repository based on the provided files and imports. Include:
- High-level component/module breakdown
- How major parts interact
- Data/request flow if discernible
Use markdown and bullet points.""",
    "file_explain": """You are RepoLens AI. Explain the following code file to a developer. Include:
- Purpose of the file
- Key functions/classes
- How it fits into the broader codebase
Use markdown.""",
}

# Ordered list of smart free models to try on OpenRouter when the user
# has configured "openrouter/free" as the chat model.  We iterate through
# these on 429/502/503/504 errors until one succeeds.
FREE_MODEL_FALLBACK_CHAIN = [
    "moonshotai/kimi-k2.6:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "qwen/qwen3-coder:free",
    "google/gemma-4-31b-it:free",
    "deepseek/deepseek-v4-flash:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-120b:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
]


def clean_llm_response(text: str) -> str:
    """Strip leaked <think>…</think> blocks, </assistant> tags, and other
    reasoning artifacts that some free models leak into their output."""
    # Remove <think>…</think> blocks (including nested/multiline)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove stray opening/closing tags
    text = re.sub(r"</?(?:think|assistant|output|response)>", "", text)
    # Collapse excessive leading/trailing whitespace left behind
    text = text.strip()
    return text


async def llm_chat(messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return "*LLM not configured. Set OPENAI_API_KEY to enable AI responses.*"

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    # Determine the list of models to try
    use_fallback_chain = settings.CHAT_MODEL.lower() in ("openrouter/free", "")
    if use_fallback_chain:
        models_to_try = list(FREE_MODEL_FALLBACK_CHAIN)
    else:
        models_to_try = [settings.CHAT_MODEL]

    last_error = ""

    for model in models_to_try:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.OPENAI_BASE_URL}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "stream": False,
                    },
                    timeout=120.0,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return clean_llm_response(content)

                # Retryable errors – try next model
                if resp.status_code in (429, 502, 503, 504):
                    last_error = f"Model {model} returned HTTP {resp.status_code}"
                    continue

                # Non-retryable error – parse and return immediately
                resp.raise_for_status()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_msg = f"API returned HTTP {status_code}"
            try:
                body = e.response.json()
                if isinstance(body, dict):
                    error_detail = body.get("error", {})
                    if isinstance(error_detail, dict) and "message" in error_detail:
                        error_msg = error_detail["message"]
                    elif "detail" in body:
                        error_msg = str(body["detail"])
            except Exception:
                pass

            if use_fallback_chain and status_code in (429, 502, 503, 504):
                last_error = error_msg
                continue

            if status_code == 402:
                return "*AI Generation Error*: The API provider failed with status `402 Payment Required`. Please verify your OpenRouter/OpenAI API key and billing balance."
            return f"*AI Generation Error*: The API provider failed with status `{status_code}`: {error_msg}. Please check your configuration and network connection."
        except Exception as e:
            if use_fallback_chain:
                last_error = str(e)
                continue
            return f"*AI Generation Error*: An unexpected error occurred while communicating with the LLM: `{str(e)}`"

    # All models in the fallback chain failed
    return f"*AI Generation Error*: All free models are currently rate-limited or unavailable. Last error: {last_error}. Please try again in a few moments."


async def generate_summary(context_chunks: List[Dict[str, Any]]) -> str:
    context_text = "\n\n---\n\n".join(
        f"File: {c.get('file_path', 'unknown')}\n{c['content']}" for c in context_chunks
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS["summary"]},
        {"role": "user", "content": f"Repository files:\n\n{context_text}\n\nGenerate a summary."},
    ]
    return await llm_chat(messages)

async def generate_chat_response(query: str, context_chunks: List[Dict[str, Any]], history: List[Dict[str, str]] = None) -> str:
    context_text = "\n\n---\n\n".join(
        f"File: {c.get('file_path', 'unknown')}\n{c['content']}" for c in context_chunks
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPTS["chat"]}]
    if history:
        messages.extend(history[:6])
    messages.append({
        "role": "user",
        "content": f"Context:\n{context_text}\n\nQuestion: {query}",
    })
    return await llm_chat(messages)

async def generate_onboarding(context_chunks: List[Dict[str, Any]]) -> str:
    context_text = "\n\n---\n\n".join(
        f"File: {c.get('file_path', 'unknown')}\n{c['content']}" for c in context_chunks
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS["onboarding"]},
        {"role": "user", "content": f"Repository files:\n\n{context_text}\n\nGenerate onboarding guide."},
    ]
    return await llm_chat(messages)

async def generate_architecture(context_chunks: List[Dict[str, Any]]) -> str:
    context_text = "\n\n---\n\n".join(
        f"File: {c.get('file_path', 'unknown')}\n{c['content']}" for c in context_chunks
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS["architecture"]},
        {"role": "user", "content": f"Repository files:\n\n{context_text}\n\nDescribe architecture."},
    ]
    return await llm_chat(messages)

async def explain_file(file_path: str, content: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS["file_explain"]},
        {"role": "user", "content": f"File: {file_path}\n\n```\n{content[:4000]}\n```\n\nExplain this file."},
    ]
    return await llm_chat(messages)
