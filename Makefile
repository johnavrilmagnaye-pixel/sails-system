.PHONY: frontend-gettext-check i18n-update i18n-check i18n-compile

frontend-gettext-check:
	python3 scripts/frontend_i18n.py

i18n-update:
	docker compose exec -T web python manage.py makemessages -l ru --no-wrap '--ignore=static/libs/*'
	docker compose exec -T web python manage.py makemessages -d djangojs -l ru --no-wrap --extension=js,html '--ignore=static/libs/*'
	python3 scripts/frontend_i18n.py --update-catalog

i18n-check:
	python3 scripts/frontend_i18n.py
	docker compose exec -T web sh -c 'msgfmt --check --check-format -o /dev/null locale/ru/LC_MESSAGES/django.po && msgfmt --check --check-format -o /dev/null locale/ru/LC_MESSAGES/djangojs.po'

i18n-compile:
	docker compose exec -T web sh -c 'msgfmt --check --check-format -o locale/ru/LC_MESSAGES/django.mo locale/ru/LC_MESSAGES/django.po && msgfmt --check --check-format -o locale/ru/LC_MESSAGES/djangojs.mo locale/ru/LC_MESSAGES/djangojs.po'
