import re
from typing import Dict, Any, Optional, Literal, Tuple
from config.settings import logger
from models.schemas import ArtifactResponse
from services.llm_service import LLMService, get_llm_service

ArtifactFormat = Literal["html", "markdown"]

HTML_KEYWORDS = [
    r"\b(?:html|css|webpage|page|landing\s+page|ui|dashboard|calculator|interactive|app|website|mockup|form)\b",
    r"\b(?:create|build|generate|design)\s+(?:a\s+)?(?:page|landing\s+page|dashboard|calculator|tool)\b",
]

MARKDOWN_KEYWORDS = [
    r"\b(?:markdown|md|spec|prd|checklist|cheatsheet|documentation|doc|framework|table|template|notes)\b",
    r"\b(?:create|build|generate|write)\s+(?:a\s+)?(?:checklist|spec|prd|cheatsheet|template|framework)\b",
]

HTML_SYSTEM_PROMPT = """You are a Principal Frontend Architect and elite UI/UX Designer.
Generate a complete, self-contained, production-grade web page artifact for: '{prompt}'.

TECHNICAL SPECIFICATIONS:
1. Deliver ONLY a single, valid, standalone HTML5 document.
2. Load Tailwind CSS via CDN: <script src="https://cdn.tailwindcss.com"></script>
3. Include modern aesthetics: polished typography (Inter font), cohesive brand palette, soft drop-shadows, subtle gradients, and fully responsive layout (mobile & desktop).
4. Include interactive vanilla JavaScript (e.g. working metric sliders, input calculators, tab switchers, dynamic score counters, or interactive checklists).
5. Code must be completely self-contained with no external CSS files or build steps required.
6. Wrap the output in ```html ... ``` code block.

CONTEXT / SPECIFICATIONS:
{context}
"""

MARKDOWN_SYSTEM_PROMPT = """You are a Principal Product Operations Leader and Staff Product Manager.
Generate a structured, professional, production-grade technical Markdown artifact for: '{prompt}'.

TECHNICAL SPECIFICATIONS:
1. Deliver clean, standard GitHub Flavored Markdown.
2. Use clear visual hierarchy (#, ##, ###).
3. Include structured tables, interactive task checklists (- [ ] / - [x]), and GitHub alert callouts (> [!NOTE], > [!TIP], > [!IMPORTANT]).
4. Provide comprehensive, realistic specifications, formulas, heuristics, and execution steps.
5. Wrap the output in ```markdown ... ``` code block.

CONTEXT / SPECIFICATIONS:
{context}
"""


class ArtifactGenerator:
    """
    Generates structured digital artifacts in two primary formats:
    1. HTML/CSS: Standalone, interactive web pages and UI components with Tailwind CSS.
    2. Markdown: High-utility technical specifications, checklists, PRDs, and playbooks.

    Returns:
    {
      "type": "html" | "markdown",
      "content": "..."
    }
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or get_llm_service()

    def detect_format(self, prompt: str, explicit_type: Optional[str] = None) -> ArtifactFormat:
        """
        Determines whether the user wants HTML/CSS or Markdown output:
        - Explicit override takes precedence
        - Keyword heuristic detects UI vs documentation intent
        - Default to 'html' for pages, 'markdown' for docs
        """
        if explicit_type and explicit_type.lower() in ["html", "markdown"]:
            return explicit_type.lower()  # type: ignore

        clean = prompt.lower().strip()

        # Check for explicit Markdown intent first
        for pattern in MARKDOWN_KEYWORDS:
            if re.search(pattern, clean):
                return "markdown"

        # Check for HTML/UI intent
        for pattern in HTML_KEYWORDS:
            if re.search(pattern, clean):
                return "html"

        # Default fallback
        if "page" in clean or "ui" in clean:
            return "html"
        return "markdown"

    async def generate_artifact(
        self,
        prompt: str,
        output_type: Optional[ArtifactFormat] = None,
        context: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.6,
    ) -> ArtifactResponse:
        """
        Generates an artifact matching the requested format.
        Returns:
        {
          "type": "html" | "markdown",
          "content": "..."
        }
        """
        format_type = self.detect_format(prompt, explicit_type=output_type)
        context_str = context or "Incorporate standard high-growth B2B/consumer product heuristics."

        logger.info(f"Generating artifact of type '{format_type}' for prompt: '{prompt[:50]}...'")

        if format_type == "html":
            content = await self._generate_html(
                prompt=prompt,
                context=context_str,
                provider=provider,
                model=model,
                temperature=temperature,
            )
        else:
            content = await self._generate_markdown(
                prompt=prompt,
                context=context_str,
                provider=provider,
                model=model,
                temperature=temperature,
            )

        return ArtifactResponse(type=format_type, content=content)

    async def _generate_html(
        self,
        prompt: str,
        context: str,
        provider: Optional[str],
        model: Optional[str],
        temperature: float,
    ) -> str:
        system_template = HTML_SYSTEM_PROMPT.format(prompt=prompt, context=context)

        try:
            raw_output = await self.llm_service.generate_response(
                query=f"Generate the complete HTML/CSS artifact for: {prompt}",
                context=context,
                system_template=system_template,
                provider=provider,
                model=model,
                temperature=temperature,
            )
            # Extract HTML block
            match = re.search(r"```(?:html)?\s*(<!DOCTYPE html[\s\S]+?|<html>[\s\S]+?)```", raw_output, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            if "<!DOCTYPE html" in raw_output or "<html" in raw_output:
                return raw_output.strip()
        except Exception as e:
            logger.warning(f"LLM HTML artifact generation fallback: {e}")

        # Deterministic fallback HTML artifact
        return self._fallback_html(prompt)

    async def _generate_markdown(
        self,
        prompt: str,
        context: str,
        provider: Optional[str],
        model: Optional[str],
        temperature: float,
    ) -> str:
        system_template = MARKDOWN_SYSTEM_PROMPT.format(prompt=prompt, context=context)

        try:
            raw_output = await self.llm_service.generate_response(
                query=f"Generate the complete Markdown artifact for: {prompt}",
                context=context,
                system_template=system_template,
                provider=provider,
                model=model,
                temperature=temperature,
            )
            match = re.search(r"```(?:markdown|md)?\s*([\s\S]+?)```", raw_output, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            if raw_output.strip().startswith("#"):
                return raw_output.strip()
        except Exception as e:
            logger.warning(f"LLM Markdown artifact generation fallback: {e}")

        # Deterministic fallback Markdown artifact
        return self._fallback_markdown(prompt)

    # --------------------------------------------------------------------------
    # Fallback Generators (Zero-failure resilience)
    # --------------------------------------------------------------------------
    def _fallback_html(self, prompt: str) -> str:
        title = prompt.replace("create page", "").replace("build page", "").strip().title() or "Growth Assistant Tool"
        return f"""<!DOCTYPE html>
<html lang="en" class="h-full bg-slate-50">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>body {{ font-family: 'Inter', sans-serif; }}</style>
</head>
<body class="min-h-full flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
  <div class="max-w-3xl mx-auto w-full bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
    <div class="flex items-center space-x-3 mb-6 border-b border-slate-100 pb-4">
      <div class="w-10 h-10 rounded-xl bg-orange-500 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-orange-500/20">
        🚀
      </div>
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{title}</h1>
        <p class="text-sm text-slate-500">Interactive Product & Growth Artifact</p>
      </div>
    </div>

    <!-- Interactive Calculator / Tool Container -->
    <div class="bg-slate-50 p-6 rounded-xl border border-slate-200 space-y-6">
      <h2 class="text-base font-semibold text-slate-800">Sean Ellis PMF Survey Benchmark Score</h2>
      
      <div>
        <div class="flex justify-between text-sm font-medium text-slate-700 mb-2">
          <span>Users who answered "Very Disappointed" (%)</span>
          <span id="scoreVal" class="text-orange-600 font-bold text-base">42%</span>
        </div>
        <input type="range" id="scoreRange" min="0" max="100" value="42" 
               class="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-orange-500"
               oninput="updateScore(this.value)">
      </div>

      <div id="statusBox" class="p-4 rounded-xl border bg-emerald-50 border-emerald-200 text-emerald-800 text-sm">
        <strong>Status: Product-Market Fit Achieved (≥ 40%)</strong>
        <p class="mt-1 text-xs text-emerald-700">You have earned the right to scale customer acquisition and compounding growth loops.</p>
      </div>
    </div>

    <div class="mt-8 flex items-center justify-between pt-4 border-t border-slate-100 text-xs text-slate-400">
      <span>Built with Lenny Growth Assistant Engine</span>
      <span>Tailwind CSS & Vanilla JS</span>
    </div>
  </div>

  <script>
    function updateScore(val) {{
      document.getElementById('scoreVal').innerText = val + '%';
      const box = document.getElementById('statusBox');
      if (val >= 40) {{
        box.className = 'p-4 rounded-xl border bg-emerald-50 border-emerald-200 text-emerald-800 text-sm';
        box.innerHTML = '<strong>Status: Product-Market Fit Achieved (' + val + '%)</strong><p class="mt-1 text-xs text-emerald-700">You have earned the right to scale customer acquisition and compounding growth loops.</p>';
      }} else {{
        box.className = 'p-4 rounded-xl border bg-amber-50 border-amber-200 text-amber-800 text-sm';
        box.innerHTML = '<strong>Status: Pre-PMF (< 40%)</strong><p class="mt-1 text-xs text-amber-700">Do NOT invest in paid acquisition. Interview your users and remove onboarding friction.</p>';
      }}
    }}
  </script>
</body>
</html>"""

    def _fallback_markdown(self, prompt: str) -> str:
        title = prompt.replace("create checklist", "").replace("generate spec", "").strip().title() or "Product Growth Specification"
        return f"""# {title}

> [!NOTE]
> This artifact was generated by the Lenny Growth Assistant Engine. Follow these tactical steps to benchmark and validate product execution.

---

## 1. Executive Summary & Goals
- **Objective**: Establish empirical benchmarks and remove execution risk.
- **Target Audience**: Product Managers, Founders, and Growth Leads.
- **Primary North Star**: Measurable user value delivery (Leading Indicator of Revenue).

---

## 2. Quantitative Benchmarks
| Metric | Healthy Threshold | High-Growth Target | Diagnostic Action |
| :--- | :--- | :--- | :--- |
| **Sean Ellis PMF Score** | ≥ 40% "Very Disappointed" | > 55% | If <40%, pause acquisition and interview churned users |
| **Cohort Retention** | Curve flattens by Week 4 | Flattens by Week 2 | Audit the Aha! moment and compress time-to-value |
| **LTV : CAC Payback** | < 12 months payback | < 6 months payback | Adjust pricing to value metrics |

---

## 3. Execution Checklist
- [x] **Step 1: Diagnostic Survey** — Send 40% PMF survey to last 30 days active cohort.
- [ ] **Step 2: Funnel Friction Audit** — Strip mandatory fields and reduce activation steps to under 3 clicks.
- [ ] **Step 3: Growth Loop Selection** — Select one primary loop (Viral, SEO, Paid, or Sales-assisted).
- [ ] **Step 4: Pre-Mortem Review** — Conduct team pre-mortem to identify single point of failure before code freeze.

---

> [!TIP]
> **Key Principle**: Marketing on top of poor retention accelerates startup death. Always fix the bucket before turning on the tap.
"""


# ==============================================================================
# Helper & Module-Level Function
# ==============================================================================
_generator_instance: Optional[ArtifactGenerator] = None


def get_artifact_generator() -> ArtifactGenerator:
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = ArtifactGenerator()
    return _generator_instance


async def generate_artifact(
    prompt: str,
    output_type: Optional[ArtifactFormat] = None,
    context: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> ArtifactResponse:
    """
    Primary interface function for artifact generation:
    generate_artifact(prompt, output_type=None, context=None)

    Returns:
    {
      "type": "html" | "markdown",
      "content": "..."
    }
    """
    generator = get_artifact_generator()
    return await generator.generate_artifact(
        prompt=prompt,
        output_type=output_type,
        context=context,
        provider=provider,
        model=model,
    )
