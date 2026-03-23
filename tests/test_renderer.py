from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput


def test_render_example_creates_pptx(tmp_path: Path) -> None:
    spec = PresentationInput.from_path("examples/ai_sales.json")
    output = tmp_path / "example.pptx"

    renderer = PresentationRenderer(asset_root="examples")
    rendered = renderer.render(spec, output)

    assert rendered.exists()
    presentation = Presentation(str(rendered))
    assert len(presentation.slides) == 7
