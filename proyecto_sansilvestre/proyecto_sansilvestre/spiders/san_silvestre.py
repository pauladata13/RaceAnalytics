from urllib import response
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
        
        for fila in filas:
            item = self.extraer_datos_tabla(fila, response.meta)
            perfil_url = fila.css('td.nombre a::attr(href)').get()
            
            if fecha in self.distancias_cache:
                item['race_distance'] = self.distancias_cache[fecha]
                yield item
            

            elif perfil_url:
               
                yield response.follow(perfil_url, callback=self.parse_perfil, meta={'item': item})
            
            else:
                item['race_distance'] = "distancia no disponible"
                yield item
    
        siguiente = response.css('li.next a::attr(href)').get()
        if siguiente:
            yield response.follow(siguiente, callback=self.parse_resultados, meta=response.meta)


    def extraer_datos_tabla(self, fila, meta):
        item = RunnerItem()
        item['runner_name'] = f"{fila.css('td.nombre a::text').get('')} {fila.css('td.apellidos a::text').get('')}".strip()
        item['finish_time'] = fila.css('td.tiempo_display::text').get()

        # Get age group w/o place in race
        age_group=None
        raw_agegroup=fila.css('td.get_puesto_categoria_display::text').get()
        if raw_agegroup and "-" in raw_agegroup:
            splitted_agegroup=raw_agegroup.split("-")
            age_group=splitted_agegroup[0]

        item['age_group'] = age_group

        # Get gender w/o place in race
        gender=None
        raw_gender=fila.css('td.get_puesto_sexo_display::text').get()
        if raw_gender and "-" in raw_gender:
            splitted_gender=raw_gender.split("-")
            gender=splitted_gender[0]

        item['gender'] = gender
        item['race_date'] = meta.get('fecha')
        item['location'] = meta.get('location')
        return item

    def parse_perfil(self, response):
        item = response.meta['item']
        fecha = item['race_date']
        
        distancia = response.xpath('//tr[td[contains(text(), "META")]]/td[last()]/text()').get()
        if not distancia:
            distancias = response.xpath('//td[contains(text(), " m")]/text()').getall()
            distancia = distancias[-1] if distancias else None
        
      
        self.distancias_cache[fecha] = distancia
        
        item['race_distance'] = distancia
        yield item