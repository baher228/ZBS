from __future__ import annotations

import argparse
import base64
import json
import os
import re
import time
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urljoin, urlparse, urlunparse

from openai import OpenAI
from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = Path(__file__).resolve().parent / "extraction_reports"
ARTIFACT_DIR = Path(__file__).resolve().parent / "extraction_artifacts"

DEFAULT_FOUNDER_INPUT = {
    "product_name": "Demeo",
    "product_description": (
        "Demeo helps technical B2B founders turn their product into a guided "
        "buyer demo. A prospect receives a link to an AI-led experience that "
        "explains the product, answers questions, qualifies the opportunity, "
        "and prepares follow-up for the founder."
    ),
    "target_customer": "technical B2B startup founders selling software",
    "prospect_description": "a founder evaluating whether Demeo can demo their own startup",
    "demo_goals": [
        "show what a founder provides during setup",
        "show how content or agent output is generated",
        "show the prospect demo room",
        "show the founder what they receive after a prospect finishes the demo",
    ],
    "founder_walkthrough": (
        "Start by showing how the founder enters company and product context. "
        "Then show the agent/content console where AI output can be generated "
        "from that context. Then show the prospect demo room where a buyer can "
        "ask questions. Finally show the CRM summary and follow-up output that "
        "qualifies the lead. Emphasize that the final product sends a prospect "
        "a personalized link and the AI demo agent guides them."
    ),
    "approved_qa": [
        {
            "question": "What does the founder need to provide?",
            "answer": (
                "A product or staging URL, sandbox credentials when needed, "
                "target persona, demo goals, a short walkthrough, approved Q&A, "
                "CTA, and qualification questions."
            ),
        },
        {
            "question": "Should the runtime click the real app directly?",
            "answer": (
                "The MVP should use an approved manifest and visual event playback. "
                "Playwright is better for setup-time extraction and validation. "
                "Live app control can come later for approved low-risk paths."
            ),
        },
        {
            "question": "Can this support voice?",
            "answer": (
                "Yes. Gemini Live or a LiveKit voice agent can call the same safe "
                "demo tools used by text: show page, move cursor, highlight, "
                "propose click, answer from knowledge, and update lead memory."
            ),
        },
    ],
    "cta": "book a founder onboarding call",
    "qualification_questions": [
        "What product do you want Demeo to demo?",
        "Do you have a safe sandbox or staging account?",
        "Who is the target buyer?",
    ],
}

EXPECTED_PAGES = {
    "setup": {"onboarding"},
    "content": {"content", "agents"},
    "demo": {"demo"},
    "crm": {"crm"},
}

EXPECTED_QUESTIONS = [
    {
        "question": "What does the founder need to provide?",
        "expected_pages": {"onboarding"},
        "expected_terms": {"product", "persona", "walkthrough", "q", "cta", "setup"},
    },
    {
        "question": "Show me the agent/content console.",
        "expected_pages": {"content", "agents"},
        "expected_terms": {"agent", "content", "generate", "prompt"},
    },
    {
        "question": "Show the prospect demo room.",
        "expected_pages": {"demo"},
        "expected_terms": {"demo", "prospect", "chat", "agent"},
    },
    {
        "question": "Show me what the founder receives after the demo.",
        "expected_pages": {"crm"},
        "expected_terms": {"lead", "score", "crm", "follow", "qualify"},
    },
]


@dataclass
class CrawlLink:
    href: str
    text: str
    source_route: str


@dataclass
class CrawlPage:
    route: str
    depth: int
    title: str
    text: str
    controls: list[dict[str, Any]]
    links: list[CrawlLink]
    screenshot_path: str | None = None

    @property
    def page_id(self) -> str:
        return self.route.strip("/").replace("/", "-") or "home"


def load_dotenv() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        if not line or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_founder_input(path: str | None) -> dict[str, Any]:
    if path is None:
        return DEFAULT_FOUNDER_INPUT
    return json.loads(Path(path).read_text())


def normalize_internal_href(base_url: str, href: str) -> str | None:
    if not href or href.startswith(("mailto:", "tel:", "javascript:")):
        return None
    base = urlparse(base_url)
    parsed = urlparse(urljoin(base_url.rstrip("/") + "/", href))
    if parsed.netloc != base.netloc:
        return None
    clean_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key not in {"utm_source", "utm_medium", "utm_campaign"}
    ]
    return urlunparse(("", "", parsed.path or "/", "", "&".join(f"{k}={v}" for k, v in clean_query), ""))


def crawl_discoverable_pages(
    base_url: str,
    start_path: str,
    max_pages: int,
    max_depth: int,
    with_screenshots: bool,
) -> list[CrawlPage]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    queued: set[str] = {start_path}
    queue: deque[tuple[str, int]] = deque([(start_path, 0)])
    pages: list[CrawlPage] = []

    with sync_playwright() as p:
        executable_path = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
        launch_kwargs: dict[str, Any] = {"headless": True}
        if executable_path:
            launch_kwargs["executable_path"] = executable_path
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})

        while queue and len(pages) < max_pages:
            route, depth = queue.popleft()
            queued.discard(route)
            if route in seen or depth > max_depth:
                continue
            seen.add(route)

            page.goto(f"{base_url.rstrip('/')}{route}", wait_until="networkidle")
            time.sleep(0.35)

            controls = page.locator(
                "button, a, input, textarea, select, [role=button], [data-demo-id]"
            ).evaluate_all(
                """els => els.slice(0, 100).map((el, index) => {
                    const tag = el.tagName.toLowerCase();
                    const text = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().replace(/\\s+/g, ' ').slice(0, 180);
                    const dataDemoId = el.getAttribute('data-demo-id');
                    const id = el.getAttribute('id');
                    const href = el.getAttribute('href');
                    let selectorHint = tag;
                    if (dataDemoId) selectorHint = `[data-demo-id="${dataDemoId}"]`;
                    else if (id) selectorHint = `#${id}`;
                    else if (href) selectorHint = `a[href="${href}"]`;
                    else if (el.getAttribute('placeholder')) selectorHint = `${tag}[placeholder="${el.getAttribute('placeholder')}"]`;
                    else if (text) selectorHint = `${tag}:has-text("${text.slice(0, 60)}")`;
                    return {
                        index,
                        tag,
                        role: el.getAttribute('role'),
                        text,
                        href,
                        selectorHint,
                        dataDemoId,
                        placeholder: el.getAttribute('placeholder'),
                        disabled: el.disabled || el.getAttribute('aria-disabled') === 'true'
                    };
                })"""
            )
            raw_links = page.locator("a[href]").evaluate_all(
                """els => els.slice(0, 100).map(el => ({
                    href: el.getAttribute('href') || '',
                    text: (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ').slice(0, 120)
                }))"""
            )
            links = []
            for raw in raw_links:
                href = normalize_internal_href(base_url, raw.get("href", ""))
                if href is None:
                    continue
                links.append(CrawlLink(href=href, text=raw.get("text", ""), source_route=route))
                if depth < max_depth and href not in seen and href not in queued and len(seen) + len(queued) < max_pages:
                    queue.append((href, depth + 1))
                    queued.add(href)

            screenshot_path = None
            if with_screenshots:
                safe_name = route.strip("/").replace("/", "-") or "home"
                screenshot_path = str(ARTIFACT_DIR / f"{safe_name}.png")
                page.screenshot(path=screenshot_path, full_page=False)

            pages.append(
                CrawlPage(
                    route=route,
                    depth=depth,
                    title=page.title(),
                    text=page.locator("body").inner_text(timeout=5000)[:7000],
                    controls=controls,
                    links=links,
                    screenshot_path=screenshot_path,
                )
            )

        browser.close()

    return pages


def page_summaries(pages: list[CrawlPage], include_controls: bool = True) -> list[dict[str, Any]]:
    summaries = []
    for page in pages:
        item: dict[str, Any] = {
            "page_id": page.page_id,
            "route": page.route,
            "depth": page.depth,
            "title": page.title,
            "visible_text": page.text[:2800],
            "links_found": [asdict(link) for link in page.links[:30]],
        }
        if include_controls:
            item["controls"] = page.controls[:40]
        summaries.append(item)
    return summaries


def build_condition_payload(
    condition: str,
    pages: list[CrawlPage],
    founder_input: dict[str, Any],
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": (
                f"Condition: {condition}\n"
                "Return strict JSON only with this shape:\n"
                "{\n"
                '  "pages": [{"page_id":"string","route":"string|null","purpose":"string",'
                '"important_elements":[{"element_id":"string","label":"string","selector_hint":"string","why":"string"}],'
                '"allowed_actions":[{"action_id":"string","type":"navigate|highlight|click|answer","label":"string",'
                '"source_page_id":"string","target_page_id":"string|null","element_id":"string|null","intent":"string","safe":true}]}],\n'
                '  "flows": [{"flow_id":"string","goal":"string","steps":[{"page_id":"string","action_id":"string|null","say":"string"}]}],\n'
                '  "approved_answers": [{"topic":"string","answer":"string","source":"string"}],\n'
                '  "notes": ["string"]\n'
                "}\n"
                "For navigate actions, source_page_id is where the link/control exists and target_page_id is the destination. "
                "For highlight/answer actions, target_page_id can equal source_page_id or null. "
                "Use only routes and selector hints from crawled pages unless the condition lacks crawled pages. "
                "Do not include destructive actions. Prefer highlight/navigate actions; only include clicks for clearly safe controls."
            ),
        }
    ]
    if condition in {"url_only", "url_walkthrough", "screenshot_assisted"}:
        content.append(
            {
                "type": "input_text",
                "text": "Crawled pages discovered by internal links:\n"
                + json.dumps(page_summaries(pages), indent=2),
            }
        )
    if condition in {"url_walkthrough", "docs_only", "screenshot_assisted"}:
        context = {
            "product_name": founder_input["product_name"],
            "product_description": founder_input["product_description"],
            "target_customer": founder_input["target_customer"],
            "prospect_description": founder_input["prospect_description"],
            "demo_goals": founder_input["demo_goals"],
            "founder_walkthrough": founder_input["founder_walkthrough"],
            "approved_qa": founder_input["approved_qa"],
            "cta": founder_input["cta"],
            "qualification_questions": founder_input["qualification_questions"],
        }
        content.append({"type": "input_text", "text": "Founder-provided input:\n" + json.dumps(context, indent=2)})
    if condition == "screenshot_assisted":
        content.append({"type": "input_text", "text": "Screenshots from crawled pages follow."})
        for crawl_page in pages[:6]:
            if not crawl_page.screenshot_path:
                continue
            image_bytes = Path(crawl_page.screenshot_path).read_bytes()
            content.extend(
                [
                    {
                        "type": "input_text",
                        "text": f"Screenshot for page_id={crawl_page.page_id}, route={crawl_page.route}",
                    },
                    {
                        "type": "input_image",
                        "image_url": "data:image/png;base64,"
                        + base64.b64encode(image_bytes).decode("ascii"),
                    },
                ]
            )
    return content


def response_kwargs(model: str) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"model": model}
    if model.startswith("gpt-5"):
        kwargs["reasoning"] = {"effort": os.getenv("OPENAI_REASONING_EFFORT", "low")}
        kwargs["text"] = {"verbosity": os.getenv("OPENAI_TEXT_VERBOSITY", "low")}
    else:
        kwargs["temperature"] = 0.1
    return kwargs


def safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def call_openai_manifest(condition: str, pages: list[CrawlPage], founder_input: dict[str, Any]) -> dict[str, Any]:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not available in environment or .env")

    client = OpenAI(timeout=float(os.getenv("OPENAI_EXTRACTION_TIMEOUT", "90")))
    model = os.getenv("OPENAI_EXTRACTION_MODEL", "gpt-4.1-mini")
    response = client.responses.create(
        **response_kwargs(model),
        input=[
            {
                "role": "system",
                "content": (
                    "You extract safe, reviewable AI demo-room manifests from startup pages and founder context. "
                    "The manifest will power a visible demo agent. Be conservative: do not invent selectors, "
                    "do not invent hidden pages, and mark only obviously safe actions as allowed."
                ),
            },
            {"role": "user", "content": build_condition_payload(condition, pages, founder_input)},
        ],
    )
    return parse_json(response.output_text)


def call_openai_planner(manifest: dict[str, Any], founder_input: dict[str, Any], planner_model: str) -> dict[str, Any]:
    load_dotenv()
    client = OpenAI(timeout=float(os.getenv("OPENAI_EXTRACTION_TIMEOUT", "90")))
    planner_prompt = {
        "founder_input": founder_input,
        "manifest": manifest,
        "prospect_questions": [item["question"] for item in EXPECTED_QUESTIONS],
    }
    response = client.responses.create(
        **response_kwargs(planner_model),
        input=[
            {
                "role": "system",
                "content": (
                    "You are the runtime planner for an AI demo-room. Choose only from the provided manifest. "
                    "This is a visual product demo, so if a question can be answered while showing a relevant "
                    "page or element, return both narration and visual events. "
                    "Return strict JSON only: {\"decisions\":[{\"question\":\"string\",\"reply\":\"string\","
                    "\"events\":[{\"type\":\"answer|show_page|highlight|click\",\"page_id\":\"string|null\","
                    "\"action_id\":\"string|null\",\"element_id\":\"string|null\",\"say\":\"string|null\"}],"
                    "\"reason\":\"string\"}]}. "
                    "Use show_page for approved pages even when no click path is required. Use click only for safe allowed_actions. "
                    "If no safe UI action fits, use a single answer event."
                ),
            },
            {"role": "user", "content": json.dumps(planner_prompt, indent=2)},
        ],
    )
    return parse_json(response.output_text)


def parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def page_matches(target: str, expected_pages: set[str]) -> bool:
    target = target.lower().strip("/")
    if target in expected_pages:
        return True
    return any(expected in target for expected in expected_pages)


def score_extraction(manifest: dict[str, Any], pages: list[CrawlPage]) -> dict[str, Any]:
    crawled_ids = {page.page_id for page in pages}
    crawled_routes = {page.route.strip("/").replace("/", "-") or "home" for page in pages}
    manifest_pages = manifest.get("pages", [])
    actions = [action for page in manifest_pages for action in page.get("allowed_actions", [])]
    action_ids = {action.get("action_id") for action in actions}
    element_ids = {
        element.get("element_id")
        for page in manifest_pages
        for element in page.get("important_elements", [])
    }
    valid_selector_refs = set(element_ids)
    for page in manifest_pages:
        for element in page.get("important_elements", []):
            selector_hint = element.get("selector_hint")
            if selector_hint:
                valid_selector_refs.add(selector_hint)
    for page in pages:
        for control in page.controls:
            for key in ("selectorHint", "dataDemoId", "text", "href"):
                value = control.get(key)
                if value:
                    valid_selector_refs.add(value)
    invented_pages = [
        page.get("page_id")
        for page in manifest_pages
        if page.get("page_id") not in crawled_ids and page.get("page_id") not in crawled_routes
    ]
    invented_action_refs = []
    invalid_action_pages = []
    for action in actions:
        element_id = action.get("element_id")
        if element_id not in {None, "", "null"} and element_id not in valid_selector_refs:
            invented_action_refs.append(action)
        for key in ("source_page_id", "target_page_id", "page_id"):
            value = action.get(key)
            if value not in {None, "", "null"} and value not in crawled_ids and value not in crawled_routes:
                invalid_action_pages.append(action)

    expected_page_hits = {
        label: any(page_matches(page.page_id, options) for page in pages)
        for label, options in EXPECTED_PAGES.items()
    }
    linked_live_route_reached = any(page.route == "/demo-room/live" for page in pages)

    return {
        "crawled_page_count": len(pages),
        "manifest_page_count": len(manifest_pages),
        "action_count": len(actions),
        "safe_action_count": sum(1 for action in actions if action.get("safe") is True),
        "known_action_count": len(action_ids),
        "expected_page_hits": expected_page_hits,
        "expected_page_hit_count": sum(1 for hit in expected_page_hits.values() if hit),
        "invented_page_count": len(invented_pages),
        "invented_pages": invented_pages,
        "invented_action_ref_count": len(invented_action_refs),
        "invalid_action_page_count": len(invalid_action_pages),
        "linked_live_route_reached": linked_live_route_reached,
    }


def score_planner(manifest: dict[str, Any], planner_result: dict[str, Any]) -> dict[str, Any]:
    actions = [action for page in manifest.get("pages", []) for action in page.get("allowed_actions", [])]
    action_ids = {action.get("action_id") for action in actions}
    page_ids = {page.get("page_id") for page in manifest.get("pages", [])}
    decisions = planner_result.get("decisions", [])
    results = []

    for expected in EXPECTED_QUESTIONS:
        decision = next(
            (
                item
                for item in decisions
                if expected["question"].lower()[:18] in str(item.get("question", "")).lower()
            ),
            None,
        )
        if decision is None:
            results.append({"question": expected["question"], "passed": False, "reason": "missing decision"})
            continue
        events = decision.get("events") or []
        reason = str(decision.get("reason", "")).lower()
        reply = str(decision.get("reply", "")).lower()
        event_pages = [str(event.get("page_id") or "") for event in events]
        event_action_ids = [event.get("action_id") for event in events]
        page_hit = any(page_matches(page_id, expected["expected_pages"]) for page_id in event_pages)
        action_known = all(action_id in action_ids or action_id in {None, "", "null"} for action_id in event_action_ids)
        page_known = all(
            page_id in page_ids or page_id in {None, "", "null"} or event.get("type") == "answer"
            for page_id, event in zip(event_pages, events)
        )
        term_hit = bool(expected["expected_terms"] & set(re.findall(r"[a-z]+", reason + " " + reply)))
        answer_only_ok = (
            expected["question"].startswith("What does the founder need")
            and any(event.get("type") == "answer" for event in events)
            and term_hit
        )
        results.append(
            {
                "question": expected["question"],
                "passed": (answer_only_ok or page_hit) and action_known and page_known and (term_hit or page_hit),
                "events": events,
                "reason": decision.get("reason"),
            }
        )

    return {
        "question_pass_count": sum(1 for result in results if result["passed"]),
        "question_total": len(results),
        "question_results": results,
    }


def success_summary(extraction_score: dict[str, Any], planner_score: dict[str, Any]) -> dict[str, Any]:
    extraction_ready = (
        extraction_score["expected_page_hit_count"] >= 3
        and extraction_score["action_count"] >= 6
        and extraction_score["invented_page_count"] == 0
        and extraction_score["invented_action_ref_count"] == 0
        and extraction_score["invalid_action_page_count"] == 0
    )
    planner_ready = planner_score["question_pass_count"] >= 3
    return {
        "extraction_ready": extraction_ready,
        "planner_ready": planner_ready,
        "usable_for_mvp_review": extraction_ready and planner_ready,
            "success_rule": (
                "MVP-usable means at least 3/4 expected app areas discovered, at least 6 safe/reviewable "
                "actions, no invented manifest pages/action refs, and at least 3/4 prospect questions "
            "planned to the right page/action."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5175")
    parser.add_argument("--start-path", default="/")
    parser.add_argument("--max-pages", type=int, default=12)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--founder-input-json")
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=["url_only", "url_walkthrough", "docs_only", "screenshot_assisted"],
    )
    parser.add_argument(
        "--planner-models",
        nargs="+",
        default=[os.getenv("OPENAI_PLANNER_MODEL", "gpt-5.4-mini")],
    )
    args = parser.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    needs_screenshots = "screenshot_assisted" in args.conditions
    founder_input = load_founder_input(args.founder_input_json)
    pages = crawl_discoverable_pages(
        base_url=args.base_url,
        start_path=args.start_path,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        with_screenshots=needs_screenshots,
    )
    report: dict[str, Any] = {
        "base_url": args.base_url,
        "start_path": args.start_path,
        "extraction_model": os.getenv("OPENAI_EXTRACTION_MODEL", "gpt-4.1-mini"),
        "planner_models": args.planner_models,
        "founder_input": founder_input,
        "crawl_pages": page_summaries(pages),
        "conditions": {},
    }
    for condition in args.conditions:
        print(f"extracting condition={condition}", flush=True)
        manifest = call_openai_manifest(condition, pages, founder_input)
        extraction_score = score_extraction(manifest, pages)
        report["conditions"][condition] = {
            "manifest": manifest,
            "extraction_score": extraction_score,
            "planner_runs": {},
        }
        for planner_model in args.planner_models:
            print(f"planning condition={condition} model={planner_model}", flush=True)
            planner = call_openai_planner(manifest, founder_input, planner_model)
            planner_score = score_planner(manifest, planner)
            success = success_summary(extraction_score, planner_score)
            report["conditions"][condition]["planner_runs"][planner_model] = {
                "planner": planner,
                "planner_score": planner_score,
                "success": success,
            }
            # Preserve a top-level result for older ad-hoc readers.
            if "planner" not in report["conditions"][condition]:
                report["conditions"][condition].update(
                    {
                        "planner": planner,
                        "planner_score": planner_score,
                        "success": success,
                    }
                )
            print(
                f"completed condition={condition} model={planner_model} "
                f"planner={planner_score['question_pass_count']}/{planner_score['question_total']} "
                f"actions={extraction_score['action_count']} usable={success['usable_for_mvp_review']}",
                flush=True,
            )
        (REPORT_DIR / f"{safe_filename(condition)}.json").write_text(json.dumps(report["conditions"][condition], indent=2))
    report_path = REPORT_DIR / "summary.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(report_path)
    for condition, data in report["conditions"].items():
        extraction = data["extraction_score"]
        for planner_model, run in data["planner_runs"].items():
            planner = run["planner_score"]
            success = run["success"]
            print(
                condition,
                planner_model,
                f"pages={extraction['crawled_page_count']}",
                f"expected_pages={extraction['expected_page_hit_count']}/4",
                f"actions={extraction['action_count']}",
                f"planner={planner['question_pass_count']}/{planner['question_total']}",
                f"usable={success['usable_for_mvp_review']}",
            )


if __name__ == "__main__":
    main()
