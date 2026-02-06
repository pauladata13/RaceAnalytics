# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

class SanSilvestrePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # LIMPIEZA: Quitamos espacios en blanco extra de todos los campos
        for field in adapter.field_names():
            value = adapter.get(field)
            if value and isinstance(value, str):
                adapter[field] = value.strip()

        # VALIDACIÓN: Si no hay nombre o tiempo, descartamos la fila
        if not adapter.get('runner_name') or not adapter.get('finish_time'):
            raise DropItem(f"Fila incompleta detectada: {item}")

        return item
