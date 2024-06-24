build:
	python -m uvicorn main:app --reload

start:
	brew services start mongodb-community@7.0

stop:
	brew services start mongodb-community@7.0