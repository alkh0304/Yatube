# Yatube

## Описание

Социальная сеть на Django (frontend и backend) для ведения дневников с возможностью у пользователей создавать учетные записи, публиковать посты, подписываться на авторов, отмечать понравившиеся записи и комментировать посты.

Встроено тестирование на базе Unittest для проверки работоспособности всего проекта (запуск - python manage.py test).

## Статус проекта:

![example workflow](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml)

## Технологии и библиотеки:
- [Python](https://www.python.org/);
- [Django](https://www.djangoproject.com);
- [Pillow](https://pillow.readthedocs.io/en/stable/);
- [Mixer](https://pypi.org/project/mixer/);
- [Bootstrap](https://getbootstrap.com);
- [Unittest](https://docs.python.org/3/library/unittest.html).

## Для локального запуска:
1. Клонируйте репозиторий.

2. Создайте и активируйте виртуальное окружение:
```
python3 -m venv venv
source venv/bin/activate
```
3. Установите зависимости:
```
pip install -r requirements.txt
```
4. В директории yatube выполните команду:
```
python manage.py runserver
```
5. Проект запущен по адресу http://127.0.0.1:8000/

## Над проектом Yatube работал:

[Александр Хоменко](https://github.com/alkh0304)