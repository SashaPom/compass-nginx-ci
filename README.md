# Compass

Nginx віддає сторінку devops7-compass-21, JSON зі станом випуску та HTTP 404 для відсутнього ресурсу.

## Базовий приклад

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    docker build -t compass-demo ./demo
    docker run -d --name compass-demo -p 127.0.0.1:8080:80 compass-demo
    curl --fail --max-time 5 http://127.0.0.1:8080/
    python -m pytest -q --hosts=docker://compass-demo demo/tests

Для досліду заміни сторінку в запущеному контейнері.

    docker exec compass-demo sh -c 'echo "<h1>wrong-release</h1>" > /usr/share/nginx/html/index.html'
    curl --fail --max-time 5 -w '\nHTTP %{http_code}\n' http://127.0.0.1:8080/
    python -m pytest -q --hosts=docker://compass-demo demo/tests
    docker rm -f compass-demo
    docker run -d --name compass-demo -p 127.0.0.1:8080:80 compass-demo
    python -m pytest -q --hosts=docker://compass-demo demo/tests
    docker rm -f compass-demo

## Запуск і три групи перевірок

    export BASE_URL=http://127.0.0.1:8674 EXPECTED_RELEASE=devops7-compass-21 CHECK_TIMEOUT=2.5
    docker build -t compass-lab .
    docker run -d --name compass-web -p 127.0.0.1:8674:8080 compass-lab
    curl --fail --max-time 5 --retry 5 --retry-all-errors "$BASE_URL/"
    python -m pytest -q --hosts=docker://compass-web checks
    python probe_compass.py

Testinfra читає файли в контейнері. Зовнішні тести звертаються до опублікованого порту. Команда повертає 0 в разі успіху, 1 в разі помилки та 2 після тайм-ауту.

## Відтворення відмов

Перед кожним дослідом підтвердь 17 успішних тестів. Після внесення зміни та після відновлення повтори pytest і команду перевірки.

1. Переміщення документа стану. Файл зникає з очікуваного шляху, а HTTP-маршрут відповідає 404.

       docker exec compass-web mv /srv/compass/health.json /tmp/compass-health.json
       curl -sS --max-time 5 -o /dev/null -w 'HTTP %{http_code}\n' "$BASE_URL/health.json"
       docker exec compass-web mv /tmp/compass-health.json /srv/compass/health.json

2. Перенаправлення головної сторінки. Синтаксис Nginx коректний, клієнт отримує HTTP 307, маркер відсутній у тілі відповіді.

       docker exec compass-web sed -i 's|try_files /index.html =404;|return 307 /health.json;|' /etc/nginx/conf.d/default.conf
       docker exec compass-web nginx -t
       docker exec compass-web nginx -s reload
       curl -sS --max-time 5 -D - -o /dev/null "$BASE_URL/"
       docker cp nginx/site.conf compass-web:/etc/nginx/conf.d/default.conf
       docker exec compass-web nginx -t
       docker exec compass-web nginx -s reload

   Після reload дай Nginx застосувати конфігурацію й повтори запит.

3. Пауза контейнера. Прямий HTTP-запит вичерпує тайм-аут, а Docker відхиляє exec.

       docker pause compass-web
       python -m pytest -q --hosts=docker://compass-web checks
       python probe_compass.py
       docker unpause compass-web

Для повного відновлення видали контейнер, повтори збірку та запуск із вихідних файлів і перевір 17 тестів. Після роботи виконай docker rm -f compass-web.

## GitHub Actions

Workflow .github/workflows/qualify.yml запускається після push у main або media-type-check. Для контрольованої помилки зміни application/json на text/plain у nginx/site.conf й відправ коміт у media-type-check. У другому коміті поверни application/json. Тест заголовка працює в обох прогонах. У compass-evidence зберігаються JUnit XML, вивід команди та журнал Nginx.
