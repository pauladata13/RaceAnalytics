# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ProyectoSansilvestreItem(scrapy.Item):
    nombre = scrapy.Field()
    tiempo = scrapy.Field()
    categoria = scrapy.Field()
    genero = scrapy.Field()
    distancia = scrapy.Field()
    fecha = scrapy.Field()
    ubicacion = scrapy.Field()
   
