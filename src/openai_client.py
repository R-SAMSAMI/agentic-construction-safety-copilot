from __future__ import annotations

import base64
import os

from openai import OpenAI, RateLimitError

from src.agent_workflow import ObservationContext
from src.schemas import SafetyAgentRun


SYSTEM_PROMPT = """You are a construction safety multi-agent coordinator.

Simulate four cooperating agents and return the final structured result:
1. Observation agent: extract concrete jobsite signals from notes and optional images.
2. Reasoning agent: infer compounding risk and likely severity.
3. Compliance agent: compare the scenario against OSHA-style controls without inventing certainty.
4. Planning agent: create operationally useful actions for field leadership.

Rules:
- Focus on construction safety and practical field operations.
- Stay grounded in the provided note, job context, and optional images.
- If a control is unclear, say review needed instead of overstating a violation.
- Keep outputs concise, specific, and supervisor-friendly.
- Prefer likely compliant, review needed, or likely non-compliant as compliance statuses.
- Prioritize actions that are realistic for a superintendent, foreman, safety manager, or crew.
"""


class SafetyQuotaError(RuntimeError):
    """Raised when API quota or billing is unavailable."""


def _image_to_data_url(file_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def analyze_site_safety_case(
    *,
    context: ObservationContext,
    image_payloads: list[dict[str, str | bytes]],
) -> SafetyAgentRun:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)

    content: list[dict[str, str]] = [
        {
            "type": "input_text",
            "text": (
                f"Project name: {context.project_name or 'Not provided'}\n"
                f"Contractor: {context.contractor_name or 'Not provided'}\n"
                f"Work area: {context.work_area or 'Not provided'}\n"
                f"Work type: {context.work_type or 'Not provided'}\n"
                f"Shift: {context.shift or 'Not provided'}\n"
                f"Weather: {context.weather or 'Not provided'}\n"
                f"Crew size: {context.crew_size}\n"
                f"Observation notes: {context.notes or 'Not provided'}\n"
                f"Attached filenames: {', '.join(context.filenames) if context.filenames else 'None'}\n"
            ),
        }
    ]

    for image in image_payloads:
        content.append({"type": "input_text", "text": f"Evidence image: {image['name']}"})
        content.append(
            {
                "type": "input_image",
                "image_url": _image_to_data_url(image["bytes"], image["mime_type"]),
            }
        )

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
                {"role": "user", "content": content},
            ],
            max_output_tokens=1800,
            text_format=SafetyAgentRun,
        )
    except RateLimitError as exc:
        raise SafetyQuotaError(
            "OpenAI API quota is unavailable for this key. Check billing or switch to Demo Mode."
        ) from exc

    if response.output_parsed is None:
        raise ValueError("The model did not return a structured safety agent result.")

    return response.output_parsed
