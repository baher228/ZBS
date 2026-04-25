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


def generate_image(prompt: str, section: str) -> GeneratedImage | None:
    api_key = settings.fal_api_key
    if not api_key:
        logger.warning("FAL_API_KEY not configured — skipping image generation")
        return None

    try:
        import fal_client
        import os

        os.environ["FAL_KEY"] = api_key

        result = fal_client.run(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": prompt,
                "image_size": "landscape_16_9",
                "num_inference_steps": 4,
                "num_images": 1,
                "enable_safety_checker": True,
            },
        )

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


SECTION_PROMPT_TEMPLATES = {
    "positioning": (
        "Clean, modern hero image for a startup landing page. "
        "Abstract visualization of {idea}. "
        "Professional, minimal, tech-forward aesthetic. No text."
    ),
    "landing_copy": (
        "Product hero banner for a B2B SaaS landing page. "
        "Visual metaphor for {idea}. "
        "Gradient background, modern UI elements, clean and professional. No text."
    ),
    "social_post": (
        "Eye-catching social media post graphic for LinkedIn/Twitter. "
        "Visual concept representing {idea}. "
        "Bold colors, modern design, engagement-focused. No text."
    ),
}


def generate_content_images(
    startup_idea: str,
    sections: list[str] | None = None,
) -> dict[str, GeneratedImage]:
    if not settings.fal_api_key:
        return {}

    target_sections = sections or list(SECTION_PROMPT_TEMPLATES.keys())
    results: dict[str, GeneratedImage] = {}

    for section in target_sections:
        template = SECTION_PROMPT_TEMPLATES.get(section)
        if not template:
            continue

        prompt = template.format(idea=startup_idea)
        image = generate_image(prompt, section)
        if image:
            results[section] = image

    return results
