import scrapy

class SanSilvestreSpider(scrapy.Spider):
    name = "san_silvestre"
    allowed_domains = ["sansilvestrecoruna.com"]
    start_urls = ["https://sansilvestrecoruna.com/es/web/resultado/"]

    def parse(self, response):
        enlaces = response.css('div.col-md-3 a[href*="evento-"]::attr(href)').getall()
        enlaces_unicos = list(set(enlaces))
        
        self.logger.info(f"Se han localizado {len(enlaces_unicos)} ediciones.")

        for enlace in enlaces_unicos:
            yield response.follow(enlace, callback=self.parse_edicion)

    def parse_edicion(self, response):
        self.logger.info(f"Explorando edición: {response.url}")
        
        enlace_absoluta = response.xpath(
            '//a[contains(translate(text(), "ABSOLUTA", "absoluta"), "absoluta")]/@href'
        ).get()

        if enlace_absoluta:
            self.logger.info(f"Encontrado por texto 'absoluta': {enlace_absoluta}")
            yield response.follow(enlace_absoluta, callback=self.parse_resultados)
        
        else:
            enlaces_competicion = response.css('a[href*="competicion"]::attr(href)').getall()
            if enlaces_competicion:
                for link in set(enlaces_competicion):
                    self.logger.info(f"Encontrado por URL 'competicion': {link}")
                    yield response.follow(link, callback=self.parse_resultados)
            else:
                self.logger.warning(f"Sin resultados en: {response.url}")

    def parse_resultados(self, response):
        self.logger.info(f"📊 Página de resultados alcanzada: {response.url}")
                
        yield {
            'url_final': response.url,
            'tipo': 'Absoluta/Competición'
        }