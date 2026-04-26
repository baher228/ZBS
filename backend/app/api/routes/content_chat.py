from __future__ import annotations

from fastapi import APIRouter

from app.agents.llm import get_llm_provider
from app.agents.models import ContentChatRequest, ContentChatResponse
from app.agents.image_gen import generate_content_images
from app.company.storage import get_company_context

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/chat", response_model=ContentChatResponse)
def content_chat(request: ContentChatRequest) -> ContentChatResponse:
    llm = get_llm_provider()
    company_context = get_company_context() or ""
    response = llm.chat_content(
        messages=request.messages,
        company_context=company_context,
        workflow=request.workflow,
    )
    return _add_content_visuals(response, company_context, request.workflow)


def _add_content_visuals(
    response: ContentChatResponse,
    company_context: str,
    workflow: str | None,
) -> ContentChatResponse:
    if not response.content_ready or not response.generated_content:
        return response

    output = dict(response.generated_content)
    visual_sections = _visual_sections_for_content(output, workflow)
    if not visual_sections:
        response.generated_content = output
        return response

    section_texts = {section: output[section] for section in visual_sections if section in output}
    images = generate_content_images(
        startup_idea=_first_content_text(output),
        sections=visual_sections,
        section_texts=section_texts,
        company_context=company_context,
    )

    for section, image in images.items():
        output[f"{section}_image"] = image.url

    missing_sections = [section for section in visual_sections if f"{section}_image" not in output]
    if missing_sections:
        briefs = [
            f"**{_label_for_section(section)}:** {_image_brief_for_section(section, output.get(section, ''))}"
            for section in missing_sections
        ]
        output["image_directions"] = "\n".join(briefs)

    response.generated_content = output
    return response


def _visual_sections_for_content(output: dict[str, str], workflow: str | None) -> list[str]:
    content_keys = [key for key in output if not key.endswith("_image") and not key.startswith("image_")]
    if workflow == "social_post":
        preferred = [
            key
            for key in content_keys
            if any(platform in key for platform in ("linkedin", "instagram", "tiktok", "x_post", "twitter"))
        ]
        return preferred[:2] or content_keys[:1]
    if workflow == "landing_page":
        return [key for key in content_keys if "hero" in key or "landing" in key][:2] or content_keys[:1]
    if workflow == "blog_post":
        return content_keys[:1]
    if workflow == "launch_email":
        return content_keys[:1]
    return content_keys[:1]


def _first_content_text(output: dict[str, str]) -> str:
    for key, value in output.items():
        if not key.endswith("_image") and value.strip():
            return value
    return "startup launch content"


def _label_for_section(section: str) -> str:
    return section.replace("_", " ").title()


def _image_brief_for_section(section: str, content: str) -> str:
    first_line = next((line.strip() for line in content.splitlines() if line.strip()), section)
    if "linkedin" in section:
        return (
            "Use a clean founder/product launch visual, 1200x627, no text baked into the image. "
            f"Show the idea behind: {first_line[:140]}"
        )
    if "instagram" in section or "tiktok" in section:
        return (
            "Use a vertical 4:5 or 9:16 visual with a real product/community moment, no embedded text. "
            f"Anchor it on: {first_line[:140]}"
        )
    return (
        "Use a high-quality product or customer-context visual with no text, letters, numbers, or watermark. "
        f"Anchor it on: {first_line[:140]}"
    )
