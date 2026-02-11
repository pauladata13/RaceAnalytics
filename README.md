# RaceAnalytics
Made by Mateo Fernández Rivera and Paula Domínguez Reig

## INTRODUCTION
The project consist in fetching race results from San Silvestre's race editions in A Coruña, Spain. 

## REQUIREMENTS
The requirements to run this project are listed in `requirements.txt`.

## TUTORIAL
1. Install all python dependencies listed in the file mentioned before.
2. Run the spider to start fetching race results.
```terminal
scrapy crawl san_silvestre -o carrera_san_silvestre.json
```
