# Файл: app/d1_manager.py
class D1Manager:
    def __init__(self, db):
        self._db = db

    async def execute(self, query, params=None):
        stmt = self._db.prepare(query)
        if params:
            stmt = stmt.bind(*params)
        return await stmt.run()

    async def fetch_one(self, query, params=None):
        stmt = self._db.prepare(query)
        if params:
            stmt = stmt.bind(*params)
        result = await stmt.first()
        return dict(result) if result else None
    
    async def fetch_val(self, query, params=None, column=0):
        stmt = self._db.prepare(query)
        if params:
            stmt = stmt.bind(*params)
        return await stmt.first(column)

    async def fetch_all(self, query, params=None):
        stmt = self._db.prepare(query)
        if params:
            stmt = stmt.bind(*params)
        result = await stmt.all()
        return [dict(row) for row in result["results"]] if result and result["results"] else []