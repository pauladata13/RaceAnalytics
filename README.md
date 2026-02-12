# RaceAnalytics
Made by Mateo Fernández Rivera and Paula Domínguez Reig

## INTRODUCTION
The project consist in fetching race results from San Silvestre's race editions in A Coruña, Spain. 

## REQUIREMENTS
The requirements to run this project are listed in `requirements.txt`.

## TUTORIAL
1. Install all python dependencies and programs listed in the file mentioned before into your environment.
2. At the root of the repository folder, initialize Docker container by using Docker Compose. This will download all necessary images and create a container with a MySQL DB will be enabled.
```bash
cd RaceAnalytics
docker-compose up -d
```
3. Run the spider to start fetching race results and save it to a `.json` file below `/data/` path.
> Note: This will take about 5-10 minutes.
```bash
scrapy crawl san_silvestre -o data/carrera_san_silvestre.json
```
4. Move to `/database/` diretory, execute `import_data.py` and start exporting all data in the fetched file to the MySQL database in Docker container.
```bash
cd database
python import_data.py
```