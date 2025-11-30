from services.revenue_mesh.service_packs import register


@register("business_upgrade")
def business_upgrade(**kwargs):
    pages = kwargs.get("pages", 1)
    return max(1, pages // 2)
