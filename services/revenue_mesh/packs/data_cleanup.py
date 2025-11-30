from services.revenue_mesh.service_packs import register
import random


@register("data_cleanup")
def run_data_cleanup(**kwargs):
    batch_size = kwargs.get("batch_size", 100)
    return max(1, batch_size // 100)
