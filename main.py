"""LLM Evaluation - Multi-client analysis."""

import asyncio
import json
import os
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage
from package.llm_postprocessor.llm.client import OpenAIClient, TogetherAIClient
from package.llm_postprocessor.llm.prompts import HUMAN_INST_1, AI_RESPONSE_1, HUMAN_INST_2, AI_RESPONSE_2, HUMAN_INST_3
from package.llm_postprocessor.schemas.aspects import PHQAspects
from package.llm_postprocessor.schemas.scale import PHQScales
from package.llm_postprocessor.utils import normalize_response_content, ensure_totals
from package.models import GPT_MODELS, TOGETHER_MODELS
from dotenv import load_dotenv

load_dotenv()
def _resolve_timeout() -> float:
    """Read request timeout from env, defaulting to 60 seconds."""
    try:
        return float(os.getenv("LLM_REQUEST_TIMEOUT", "60"))
    except (TypeError, ValueError):
        return 60.0

def _resolve_concurrency_limit(total_clients: int) -> int:
    """Determine how many requests to fire in parallel."""
    try:
        configured = int(os.getenv("LLM_MAX_CONCURRENCY", "4"))
    except (TypeError, ValueError):
        configured = 2
    if configured <= 0:
        configured = 1
    if total_clients <= 0:
        return 0
    return min(total_clients, configured)

def _build_clients():
    """Instantiate client wrappers for configured models."""
    clients = []
    for model in GPT_MODELS:
        clients.append(OpenAIClient(model_name=model))
    for model in TOGETHER_MODELS:
        clients.append(TogetherAIClient(model_name=model))
    return clients


def _build_messages(formatted_conv: str):
    """Prepare the evaluation conversation."""
    return [
        HumanMessage(content=HUMAN_INST_1.format()),
        AIMessage(content=AI_RESPONSE_1.format()),
        HumanMessage(content=HUMAN_INST_2.format(
            aspects=PHQAspects.get_aspect(),
            phq_scale=PHQScales.format_scale("phq_scale"),
        )),
        AIMessage(content=AI_RESPONSE_2.format()),
        HumanMessage(content=HUMAN_INST_3.format(chatHistory=formatted_conv)),
    ]


def _write_json(path: Path, payload: dict) -> None:
    """Persist JSON payload with UTF-8 encoding."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


async def _invoke_with_timeout(llm, messages, timeout: float):
    """Invoke the LLM, preferring native async when available."""
    if hasattr(llm, "ainvoke"):
        return await asyncio.wait_for(llm.ainvoke(messages), timeout=timeout)
    loop = asyncio.get_running_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(None, llm.invoke, messages),
        timeout=timeout,
    )


async def _process_client(
    client,
    messages,
    eval_base: Path,
    user_id: str,
    session_id: str,
    semaphore: asyncio.Semaphore,
    timeout: float,
) -> None:
    """Invoke a single client and write its result into post_processed."""
    safe_model_name = client.model_name.replace("/", "_").replace(".", "_")
    model_folder = eval_base / safe_model_name
    try:
        llm = client.get_client()
        async with semaphore:
            response = await _invoke_with_timeout(llm, messages, timeout)
        parsed_response = normalize_response_content(response.content)
        parsed_response = ensure_totals(parsed_response)
        result = {
            "user_id": user_id,
            "session_id": session_id,
            "model": client.model_name,
            "response": parsed_response,
        }
        _write_json(model_folder / "evaluation.json", result)
    except asyncio.TimeoutError:
        error_result = {
            "user_id": user_id,
            "session_id": session_id,
            "model": client.model_name,
            "error": f"Timed out after {timeout} seconds.",
        }
        _write_json(model_folder / "evaluation.json", error_result)
    except Exception as exc:  # pylint: disable=broad-except
        error_result = {
            "user_id": user_id,
            "session_id": session_id,
            "model": client.model_name,
            "error": str(exc),
        }
        _write_json(model_folder / "evaluation.json", error_result)


async def main() -> None:
    """Entry point."""
    clients = _build_clients()
    if not clients:
        print("No models configured; nothing to evaluate.")
        return

    timeout = _resolve_timeout()
    post_processed_path = Path("post_processed")

    data_sessions = sorted(
        [
            session_dir
            for session_dir in Path("data").iterdir()
            if session_dir.is_dir() and (post_processed_path / session_dir.name / "analysis_result.json").exists()
        ]
    )

    for session_idx, session_dir in enumerate(data_sessions):
        if session_idx > 0:
            break  # process only the first conversation; remove this guard for full batch

        result_file = post_processed_path / session_dir.name / "analysis_result.json"

        with open(result_file, encoding="utf-8") as f:
            data = json.load(f)

        user_id = data["user_id"]
        session_id = data["session_id"]
        formatted_conv = data["metadata"]["formatted_conversation"]
        messages = _build_messages(formatted_conv)
        folder_name = result_file.parent.name
        eval_base = result_file.parent / "evaluations"
        eval_base.mkdir(parents=True, exist_ok=True)

        concurrency_limit = _resolve_concurrency_limit(len(clients))
        if concurrency_limit == 0:
            continue
        semaphore = asyncio.Semaphore(concurrency_limit)
        tasks = [
            asyncio.create_task(
                _process_client(
                    client,
                    messages,
                    eval_base,
                    user_id,
                    session_id,
                    semaphore,
                    timeout,
                )
            )
            for client in clients
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
