# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class RunnerItem(scrapy.Item):
    runner_name = scrapy.Field()
    finish_time = scrapy.Field()
    age_group = scrapy.Field()
    gender = scrapy.Field()
    race_distance = scrapy.Field()
    race_date = scrapy.Field()
    location = scrapy.Field()