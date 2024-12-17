import os

db_path = 'instance/store.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print("Database deleted successfully")
