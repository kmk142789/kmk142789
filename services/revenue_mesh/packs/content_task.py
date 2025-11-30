from services.revenue_mesh.service_packs import register


@register("content_task")
def run_content_task(**kwargs):
    text = kwargs.get("text", "")
    length_units = max(1, len(text) // 500)  # 1 unit per ~500 chars
    return length_units
