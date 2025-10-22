"""LLM Evaluation - Multi-client analysis."""

import json
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage
from package.llm_postprocessor.llm.client import OpenAIClient, TogetherAIClient
from package.llm_postprocessor.llm.prompts import HUMAN_INST_1, AI_RESPONSE_1, HUMAN_INST_2, AI_RESPONSE_2, HUMAN_INST_3
from package.llm_postprocessor.schemas.aspects import PHQAspects
from package.llm_postprocessor.schemas.scale import PHQScales
from package.llm_postprocessor.utils import normalize_response_content
from package.models import GPT_MODELS, TOGETHER_MODELS
from dotenv import load_dotenv

load_dotenv()

clients = []
for model in GPT_MODELS:
    clients.append(OpenAIClient(model_name=model))
for model in TOGETHER_MODELS:
    clients.append(TogetherAIClient(model_name=model))
post_processed_path = Path("post_processed")
results_path = Path("results")
results_path.mkdir(exist_ok=True)
for result_idx, result_file in enumerate(sorted(post_processed_path.glob("*/analysis_result.json"))):
    if result_idx > 0:
        break  # process only the first conversation; remove to cover all users
    with open(result_file) as f:
        data = json.load(f)
    user_id = data["user_id"]
    session_id = data["session_id"]
    formatted_conv = data["metadata"]["formatted_conversation"]
    messages = [
        HumanMessage(content=HUMAN_INST_1.format()),
        AIMessage(content=AI_RESPONSE_1.format()),
        HumanMessage(content=HUMAN_INST_2.format(
            aspects=PHQAspects.get_aspect(),
            phq_scale=PHQScales.format_scale("phq_scale"),
            operational_scale=PHQScales.format_scale("operational_scale"),
        )),
        AIMessage(content=AI_RESPONSE_2.format()),
        HumanMessage(content=HUMAN_INST_3.format(chatHistory=formatted_conv)),
    ]
    folder_name = result_file.parent.name
    output_folder = results_path / folder_name
    output_folder.mkdir(exist_ok=True)
    for client in clients:
        try:
            llm = client.get_client()
            response = llm.invoke(messages)
            parsed_response = normalize_response_content(response.content)
            safe_model_name = client.model_name.replace("/", "_").replace(".", "_")
            model_folder = output_folder / safe_model_name
            model_folder.mkdir(exist_ok=True)
            result = {
                "user_id": user_id,
                "session_id": session_id,
                "model": client.model_name,
                "response": parsed_response,
            }
            output_file = model_folder / "evaluation.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            error_result = {
                "user_id": user_id,
                "session_id": session_id,
                "model": client.model_name,
                "error": str(e),
            }
            safe_model_name = client.model_name.replace("/", "_").replace(".", "_")
            model_folder = output_folder / safe_model_name
            model_folder.mkdir(exist_ok=True)
            output_file = model_folder / "evaluation.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(error_result, f, indent=2, ensure_ascii=False)
