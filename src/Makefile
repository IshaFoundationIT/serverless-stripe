invoke:
	sls invoke local --function paypal --path ./fixtures/paypal-capture-complete-formatted.json

format:
	black -l 90 ./handlers

lint:
	flake8 ./handlers

deploy:
	sls deploy
