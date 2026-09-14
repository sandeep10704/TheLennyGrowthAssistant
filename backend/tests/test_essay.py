import pytest
from services.essay_generator import (
    Ship30EssayGenerator,
    Ship30Article,
    generate_ship30_article,
)


@pytest.mark.asyncio
async def test_generate_ship30_article_complete_flow():
    context = (
        "Sean Ellis 40% PMF benchmark states that startups should not scale acquisition "
        "until at least 40% of surveyed users would be 'very disappointed' without the product. "
        "Retention curves must flatten parallel to the x-axis. Growth loops compound through "
        "viral loops, SEO loops, paid loops, and sales loops."
    )

    article: Ship30Article = await generate_ship30_article(
        context=context,
        topic="Product-Market Fit and Retention Loops",
    )

    assert isinstance(article, Ship30Article)

    # 1. Word count verification (~1200 words)
    assert article.word_count >= 600
    assert len(article.content.split()) >= 600

    # 2. Hook requirement
    assert article.hook is not None
    assert len(article.hook) > 20

    # 3. Headings requirement (###)
    assert "### " in article.content
    assert len(article.sections) >= 3

    # 4. Bullets requirement (- )
    assert "- " in article.content

    # 5. Strong takeaway requirement
    assert len(article.takeaways) >= 2
    assert any("retention" in t.lower() or "pmf" in t.lower() or "loop" in t.lower() or "survey" in t.lower() for t in article.takeaways)

    # String representation
    assert str(article) == article.content


@pytest.mark.asyncio
async def test_ship30_outline_creation():
    generator = Ship30EssayGenerator()
    outline = await generator.create_outline(
        context="Finding Product Market Fit and measuring retention.",
        topic="PMF Benchmarks",
    )
    assert len(outline) >= 4
    assert any("Hook" in item or "Trap" in item or "1" in item for item in outline)


def test_ship30_formatting():
    generator = Ship30EssayGenerator()
    raw = (
        "# Why Founders Fail at Retention\n"
        "## The honest truth about leaky buckets.\n\n"
        "Most founders believe marketing solves growth. They are completely wrong.\n\n"
        "### 1. The Real Problem\n"
        "Funnels leak without end.\n"
        "- **First mistake**: spending on ads before PMF.\n"
        "- **Second mistake**: ignoring cohort curves.\n\n"
        "### 2. Strong Takeaways\n"
        "- Always check the 40% benchmark first.\n"
        "- Never hire a growth team before flattening retention."
    )
    formatted = generator.add_formatting(raw_article=raw, outline=["1. Intro", "2. End"])
    assert formatted.title == "Why Founders Fail at Retention"
    assert formatted.subtitle == "The honest truth about leaky buckets."
    assert "marketing solves growth" in formatted.hook
    assert len(formatted.takeaways) >= 2
    assert len(formatted.sections) >= 2
