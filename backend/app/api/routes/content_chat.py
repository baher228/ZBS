from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from app.agents.llm import get_llm_provider
from app.agents.models import ContentChatRequest, ContentChatResponse
from app.agents.image_gen import generate_content_images
from app.agents.result_cache import cache_key, get_cached_model, set_cached_model
from app.company.chat_extractor import extract_insights_from_messages
from app.company.storage import get_company_context

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/chat", response_model=ContentChatResponse)
def content_chat(request: ContentChatRequest, background_tasks: BackgroundTasks) -> ContentChatResponse:
    llm = get_llm_provider()
    company_context = get_company_context() or ""
    msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
    background_tasks.add_task(
        extract_insights_from_messages,
        msg_dicts,
        "content",
        company_context,
    )

    if request.existing_generated_content:
        response = ContentChatResponse(
            reply="I added visuals for the drafted content below.",
            follow_up_questions=[],
            content_ready=True,
            generated_content=dict(request.existing_generated_content),
        )
        key = cache_key(
            "content.chat.visuals",
            {"request": request, "company_context": company_context},
        )
        cached = get_cached_model(key, ContentChatResponse)
        if cached is not None:
            return cached
        response = _handle_content_visuals(
            response=response,
            company_context=company_context,
            workflow=request.workflow,
            image_mode=request.image_mode,
            reference_image_urls=request.reference_image_urls,
            existing_image_note=request.existing_image_note,
        )
        set_cached_model(key, response)
        return response

    key = cache_key(
        "content.chat",
        {"request": request, "company_context": company_context},
    )
    cached = get_cached_model(key, ContentChatResponse)
    if cached is not None:
        return cached
    response = llm.chat_content(
        messages=request.messages,
        company_context=company_context,
        workflow=request.workflow,
    )
    response = _handle_content_visuals(
        response=response,
        company_context=company_context,
        workflow=request.workflow,
        image_mode=request.image_mode,
        reference_image_urls=request.reference_image_urls,
        existing_image_note=request.existing_image_note,
    )
    set_cached_model(key, response)
    return response


def _handle_content_visuals(
    response: ContentChatResponse,
    company_context: str,
    workflow: str | None,
    image_mode: str,
    reference_image_urls: list[str] | None = None,
    existing_image_note: str = "",
) -> ContentChatResponse:
    if not response.content_ready or not response.generated_content:
        return response

    if image_mode == "generate":
        return _add_content_visuals(
            response,
            company_context,
            workflow,
            reference_image_urls=reference_image_urls,
        )

    if image_mode == "reference":
        response.reply = _append_visual_prompt(
            response.reply,
            "I drafted the content below. Use your existing screenshots or platform visuals with the image directions included.",
        )
        response.generated_content = _add_reference_image_directions(
            dict(response.generated_content),
            workflow,
            existing_image_note,
            reference_image_urls or [],
        )
        return response

    if image_mode == "none":
        return response

    response.reply = _append_visual_prompt(
        response.reply,
        "I drafted the content below. For visuals, do you want me to generate AI images, use screenshots/assets you already have, or keep it text-only?",
    )
    return response


def _add_content_visuals(
    response: ContentChatResponse,
    company_context: str,
    workflow: str | None,
    reference_image_urls: list[str] | None = None,
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
        reference_image_urls=reference_image_urls,
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


def _append_visual_prompt(reply: str, prompt: str) -> str:
    cleaned = reply.strip()
    if not cleaned:
        return prompt
    if prompt in cleaned:
        return cleaned
    return f"{cleaned}\n\n{prompt}"


def _add_reference_image_directions(
    output: dict[str, str],
    workflow: str | None,
    existing_image_note: str,
    reference_image_urls: list[str],
) -> dict[str, str]:
    visual_sections = _visual_sections_for_content(output, workflow)
    if not visual_sections:
        return output

    source_line = ""
    if reference_image_urls:
        source_line = "\nReference URLs:\n" + "\n".join(f"- {url}" for url in reference_image_urls)
    note_line = f"\nAsset notes: {existing_image_note.strip()}" if existing_image_note.strip() else ""
    briefs = [
        f"**{_label_for_section(section)}:** {_image_brief_for_section(section, output.get(section, ''))}"
        for section in visual_sections
    ]
    output["image_directions"] = "\n".join(briefs) + source_line + note_line
    return output


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
