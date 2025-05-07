# Development
```
pip install -r requirements.txt
```

## Migrations
After creating/modifying the model in models.py
```
alembic revision --autogenerate -m "migration name"
alembic upgrade head
```
