build:
	python -m uvicorn main:app --reload

clean:
	find . -name "__pycache__" -exec rm -rf {} +

start:
	brew services start mongodb-community@7.0

stop:
	brew services start mongodb-community@7.0