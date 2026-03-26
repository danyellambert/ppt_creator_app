from __future__ import annotations

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.util import Inches, Pt

from ppt_creator.theme import rgb

CHART_TYPES = {
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS,
}


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors
    variant = renderer.resolve_layout_variant(slide_spec, "column")

    renderer.add_heading(
        slide,
        title=slide_spec.title or "",
        subtitle=slide_spec.subtitle,
        eyebrow=slide_spec.eyebrow or "Data view",
        left=g.content_left,
        top=g.title_top,
        width=8.2,
        subtitle_width=7.0,
    )

    top = 2.2
    if slide_spec.body:
        body_box = renderer.textbox(slide, g.content_left, top, g.content_width, 0.6)
        renderer.write_paragraph(
            body_box.text_frame,
            slide_spec.body,
            size=t.body_size - 1,
            color=colors.text,
        )
        top += 0.75

    chart_data = CategoryChartData()
    chart_data.categories = slide_spec.chart_categories
    for series in slide_spec.chart_series:
        chart_data.add_series(series.name, series.values)

    chart_frame = slide.shapes.add_chart(
        CHART_TYPES[variant],
        Inches(g.content_left),
        Inches(top),
        Inches(g.content_width),
        Inches(3.35),
        chart_data,
    )
    chart = chart_frame.chart
    chart.has_legend = len(slide_spec.chart_series) > 1
    if chart.has_legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(t.small_size)
        chart.legend.font.color.rgb = rgb(colors.muted)

    category_axis = chart.category_axis
    category_axis.tick_labels.font.size = Pt(t.small_size)
    category_axis.tick_labels.font.color.rgb = rgb(colors.muted)
    category_axis.format.line.color.rgb = rgb(colors.line)

    value_axis = chart.value_axis
    value_axis.tick_labels.font.size = Pt(t.small_size)
    value_axis.tick_labels.font.color.rgb = rgb(colors.muted)
    value_axis.format.line.color.rgb = rgb(colors.line)
    value_axis.major_gridlines.format.line.color.rgb = rgb(colors.line)

    plot = chart.plots[0]
    if hasattr(plot, "gap_width"):
        plot.gap_width = 55

    palette = [colors.navy, colors.accent, colors.text, colors.muted]
    for idx, series in enumerate(chart.series):
        color = palette[idx % len(palette)]
        series.format.fill.solid()
        series.format.fill.fore_color.rgb = rgb(color)
        series.format.line.color.rgb = rgb(color)