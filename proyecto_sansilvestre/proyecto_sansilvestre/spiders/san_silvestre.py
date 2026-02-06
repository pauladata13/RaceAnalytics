import scrapy
from proyecto_sansilvestre.items import RunnerItem

class SanSilvestreSpider(scrapy.Spider):
    name = "san_silvestre"
    start_urls = ["https://sansilvestrecoruna.com/es/web/resultado/"]
    
    distancias_cache = {}

    def parse(self, response):
        eventos = response.css('a.portfolio-link')
        for evento in eventos:
            fecha = evento.css('p.year::text').get()
            localizacion = evento.css('div.caption-content h3::text').get() or "A Coruña"
            enlace_edicion = evento.css('::attr(href)').get()
            
            yield response.follow(enlace_edicion, callback=self.parse_edicion, 
                                  meta={'fecha': fecha, 'location': localizacion})

    def parse_edicion(self, response):
        enlaces_carrera = response.css('a[href*="competicion"]')
        for enlace in enlaces_carrera:
            texto = enlace.css('::text').get('').lower()
            if "competición" in texto or "absoluta" in texto:
                yield response.follow(enlace, callback=self.parse_resultados, meta=response.meta)

    def parse_resultados(self, response):
        fecha = response.meta.get('fecha')
        filas = response.css('table tbody tr')
        
        if fecha in self.distancias_cache:
            distancia_fija = self.distancias_cache[fecha]
            for fila in filas:
                item = self.crear_item_base(fila, response.meta)
                item['race_distance'] = distancia_fija
                yield item
        else:
           
            for i, fila in enumerate(filas):
                item = self.crear_item_base(fila, response.meta)
                perfil_url = fila.css('td.nombre a::attr(href)').get()
                
                if i == 0 and perfil_url:  
                    yield response.follow(perfil_url, callback=self.parse_perfil, meta={'item': item})
                else:
                    
                    item['race_distance'] = "Pendiente..." 
                    yield item
        siguiente = response.css('li.next a::attr(href)').get()
        if siguiente:
            yield response.follow(siguiente, callback=self.parse_resultados, meta=response.meta)

    def extraer_datos_tabla(self, fila, meta):
        item = RunnerItem()
        item['runner_name'] = f"{fila.css('td.nombre a::text').get('')} {fila.css('td.apellidos a::text').get('')}".strip()
        item['finish_time'] = fila.css('td.tiempo_display::text').get()
        item['age_group'] = fila.css('td.get_puesto_categoria_display::text').get()
        item['gender'] = fila.css('td.get_puesto_sexo_display::text').get()
        item['race_date'] = meta.get('fecha')
        item['location'] = meta.get('location')
        return item

    def parse_perfil(self, response):
        item = response.meta['item']
        fecha = item['race_date']
        
        distancia = response.xpath('//tr[td[contains(text(), "META")]]/td[last()]/text()').get()
        if not distancia:
            distancias = response.xpath('//td[contains(text(), " m")]/text()').getall()
            distancia = distancias[-1] if distancias else "N/A"
        
      
        self.distancias_cache[fecha] = distancia
        
        item['race_distance'] = distancia
        yield item