from services.revenue_mesh.service_packs import register


@register("research_summary")
def research_summary(**kwargs):
    queries = kwargs.get("queries", [])
    return max(1, len(queries))
