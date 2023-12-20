# Technical Test

To start the project just run the docker-compose command:

```sh
docker-compose build
docker-compose up -d
docker-compose exec web ./manage.py migrate
```

To run the tests do

```sh
docker-compose exec web ./manage.py test
```