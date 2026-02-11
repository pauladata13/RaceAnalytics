import scrapy
from proyecto_sansilvestre.items import RunnerItem

class SanSilvestreSpider(scrapy.Spider):
    name = "san_silvestre"
    start_urls = ["https://sansilvestrecoruna.com/es/web/resultado/"]
    
    # Caché para no entrar en los perfiles de todos los corredores
    distancias_cache = {}

    def parse(self, response):
        eventos = response.css('div.col-6.col-sm-4.col-md-3.mb-4')
        
        for evento in eventos:
            fecha = evento.css('p.year::text').get()
            fecha = fecha.strip() if fecha else ""

            if fecha in ["2020", "2013"]:
                self.logger.info(f"Saltando edición excluida: {fecha}")
                continue
            
            localizacion = evento.css('div.caption-content h3::text').get() or "A Coruña"
            enlace_edicion = evento.css('a.portfolio-link::attr(href)').get()
            
            if enlace_edicion:
                yield response.follow(
                    enlace_edicion, 
                    callback=self.parse_edicion, 
                    meta={'fecha': fecha, 'location': localizacion}
                )

    def parse_edicion(self, response):
        enlaces_absoluta = []
        for enlace in response.css('a'):
            texto = enlace.css('::text').get('').lower()
            if "absoluta" in texto or "competición" in texto:
                enlaces_absoluta.append(enlace)

        if enlaces_absoluta:
            for enlace in enlaces_absoluta:
                self.logger.info(f"Año {response.meta['fecha']}: Entrando en carrera absoluta.")
                yield response.follow(enlace, callback=self.parse_resultados, meta=response.meta)
        else:
            if response.css('table'):
                self.logger.info(f"Año {response.meta['fecha']}: Tabla directa encontrada.")
                yield from self.parse_resultados(response)
            else:
                self.logger.warning(f"Año {response.meta['fecha']}: No se encontraron resultados.")

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
                yield response.follow(
                    perfil_url, 
                    callback=self.parse_perfil, 
                    meta={'item': item},
                    dont_filter=True 
                )
            else:
                item['race_distance'] = None
                yield item

        
        siguiente = response.css('li.next a::attr(href), a[aria-label="Next"]::attr(href), a.next::attr(href)').get()
        
        if siguiente:
            self.logger.info(f"Año {fecha}: Pasando a la siguiente página...")
            yield response.follow(
                siguiente, 
                callback=self.parse_resultados, 
                meta=response.meta,
                dont_filter=True 
            )

    def extraer_datos_tabla(self, fila, meta):
        item = RunnerItem()
        nombre = fila.css('td.nombre a::text').get('')
        apellidos = fila.css('td.apellidos a::text').get('')
        item['runner_name'] = f"{nombre} {apellidos}".strip()
        
        item['finish_time'] = fila.css('td.tiempo_display::text').get()

        raw_agegroup = fila.css('td.get_puesto_categoria_display::text').get()
        item['age_group'] = raw_agegroup.split("-")[0].strip() if raw_agegroup and "-" in raw_agegroup else None

        raw_gender = fila.css('td.get_puesto_sexo_display::text').get()
        item['gender'] = raw_gender.split("-")[0].strip() if raw_gender and "-" in raw_gender else None

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

        if distancia:
            try:
                distancia = float(distancia.lower().replace('m', '').strip())
            except ValueError:
                distancia = None
        
        self.distancias_cache[fecha] = distancia
        item['race_distance'] = self.distancias_cache[fecha]
        
        yield item