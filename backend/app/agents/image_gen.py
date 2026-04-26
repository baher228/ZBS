from __future__ import annotations

import logging

from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeneratedImage(BaseModel):
    url: str
    content_type: str
    prompt: str
    section: str


def generate_image(
    prompt: str,
    section: str,
    reference_image_urls: list[str] | None = None,
) -> GeneratedImage | None:
    api_key = settings.fal_api_key
    if not api_key:
        logger.warning("FAL_API_KEY not configured — skipping image generation")
        return None

    try:
        import fal_client
        import os

        os.environ["FAL_KEY"] = api_key

        references = [url.strip() for url in reference_image_urls or [] if url.strip()]
        model_id = settings.fal_image_edit_model if references else settings.fal_image_model
        arguments: dict[str, object] = {
            "prompt": prompt,
            "image_size": "auto" if references else "landscape_16_9",
            "quality": "high",
            "num_images": 1,
            "output_format": "png",
        }
        if references:
            arguments["image_urls"] = references

        result = fal_client.subscribe(model_id, arguments=arguments)

        images = result.get("images", [])
        if not images:
            logger.warning("fal.ai returned no images for prompt: %s", prompt[:80])
            return None

        return GeneratedImage(
            url=images[0]["url"],
            content_type=images[0].get("content_type", "image/jpeg"),
            prompt=prompt,
            section=section,
        )
    except Exception:
        logger.exception("Image generation failed for section '%s'", section)
        return None


def _build_contextual_prompt(section: str, section_text: str, company_context: str) -> str:
    """Use LLM to generate a context-specific image prompt from the actual content."""
    try:
        from langchain_openai import ChatOpenAI

        api_key = settings.resolved_gateway_api_key or settings.resolved_llm_api_key
        base_url = settings.resolved_gateway_base_url
        if not api_key:
            return _fallback_prompt(section, section_text)

        model = ChatOpenAI(
            model="gpt-5.2",
            api_key=api_key,
            base_url=base_url,
            max_tokens=200,
            temperature=0.7,
        )

        result = model.invoke(
            [
                (
                    "system",
                    "You create image generation prompts for a B2B startup content platform. "
                    "Given a content section and its text, produce a single vivid image prompt "
                    "that visually represents the specific ideas in the text.\n\n"
                    "Rules:\n"
                    "- The image should feel like a high-quality product screenshot, "
                    "team photo, data visualization, or professional scene\n"
                    "- Reference specific concepts from the text (not generic business imagery)\n"
                    "- NEVER include any text, letters, words, or watermarks in the image\n"
                    "- Keep the prompt under 150 words\n"
                    "- End with: 'Absolutely no text, no letters, no words, no numbers, no watermarks.'\n"
                    "- Make it photorealistic and professional\n"
                    "- If the text mentions a specific product or tool, depict a sleek UI mockup or "
                    "dashboard relevant to that product category",
                ),
                (
                    "human",
                    f"Section: {section}\n"
                    f"Content:\n{section_text[:600]}\n"
                    f"Company context:\n{company_context[:400]}",
                ),
            ]
        )
        content = result.content if hasattr(result, "content") else str(result)
        return content.strip()
    except Exception:
        logger.exception("Failed to generate contextual prompt for '%s'", section)
        return _fallback_prompt(section, section_text)


def _fallback_prompt(section: str, section_text: str) -> str:
    """Create a basic prompt from the section text without LLM."""
    first_sentence = section_text.split(".")[0][:120] if section_text else section
    base = {
        "positioning": (
            f"Professional product visualization representing: {first_sentence}. "
            "Clean modern workspace, soft lighting, premium feel."
        ),
        "landing_copy": (
            f"Sleek product dashboard mockup showing: {first_sentence}. "
            "Modern UI with data visualizations, ambient lighting."
        ),
        "icp_notes": (
            f"Professional team collaborating in modern office, discussing: {first_sentence}. "
            "Natural light, shallow depth of field."
        ),
        "launch_email": (
            f"Minimalist laptop on clean desk showing notification about: {first_sentence}. "
            "Soft lighting, inviting atmosphere."
        ),
        "social_post": (
            f"Bold dynamic composition representing: {first_sentence}. "
            "Modern, energetic, high-contrast professional visuals."
        ),
    }
    prompt = base.get(section, f"Professional scene representing: {first_sentence}.")
    return prompt + " Absolutely no text, no letters, no words, no numbers, no watermarks."


def generate_content_images(
    startup_idea: str,
    sections: list[str] | None = None,
    section_texts: dict[str, str] | None = None,
    company_context: str = "",
    reference_image_urls: list[str] | None = None,
) -> dict[str, GeneratedImage]:
    if not settings.fal_api_key:
        return {}

    default_sections = ["positioning", "landing_copy", "icp_notes", "launch_email", "social_post"]
    target_sections = sections or default_sections
    results: dict[str, GeneratedImage] = {}

    for section in target_sections:
        section_text = (section_texts or {}).get(section, startup_idea)

        if section_text and company_context:
            prompt = _build_contextual_prompt(section, section_text, company_context)
        else:
            prompt = _fallback_prompt(section, section_text or startup_idea)

        image = generate_image(prompt, section, reference_image_urls=reference_image_urls)
        if image:
            results[section] = image

    return results
