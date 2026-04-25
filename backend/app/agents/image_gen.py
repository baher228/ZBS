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

        result = fal_client.subscribe(
            "fal-ai/flux-pro/v1.1",
            arguments={
                "prompt": prompt,
                "image_size": "landscape_16_9",
                "num_images": 1,
                "safety_tolerance": "2",
                "output_format": "jpeg",
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
        "Abstract geometric visualization representing innovation and technology. "
        "Flowing gradients of deep blue, teal, and warm gold. "
        "Interconnected nodes and clean lines suggesting a network or system. "
        "Professional corporate aesthetic, soft lighting, shallow depth of field. "
        "Absolutely no text, no letters, no words, no numbers, no watermarks."
    ),
    "landing_copy": (
        "Sleek product mockup scene on a clean desk workspace. "
        "Modern laptop or tablet showing an abstract UI dashboard with colorful data visualizations. "
        "Soft ambient lighting, minimal props, premium feel. "
        "Blurred background with warm bokeh. Photo-realistic render. "
        "Absolutely no text, no letters, no words, no numbers, no watermarks."
    ),
    "icp_notes": (
        "Professional portrait-style scene of diverse business professionals in a modern office setting. "
        "Warm natural light, shallow depth of field, people collaborating over a tablet or whiteboard. "
        "Clean corporate aesthetic, muted color palette with pops of blue. "
        "Absolutely no text, no letters, no words, no numbers, no watermarks."
    ),
    "launch_email": (
        "Minimalist flat-lay composition of a laptop with a glowing inbox notification icon. "
        "Clean white desk surface, coffee cup, and a small plant. "
        "Soft top-down lighting, pastel accents, modern and inviting feel. "
        "Absolutely no text, no letters, no words, no numbers, no watermarks."
    ),
    "social_post": (
        "Bold, attention-grabbing abstract composition for social media. "
        "Dynamic diagonal lines and geometric shapes in contrasting colors — "
        "electric purple, coral, and white on a dark background. "
        "Modern, energetic, high-contrast. Perfect square or 16:9 crop. "
        "Absolutely no text, no letters, no words, no numbers, no watermarks."
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

        image = generate_image(template, section)
        if image:
            results[section] = image

    return results
