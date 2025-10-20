import sqlite3

connection = sqlite3.connect('database.db')

with connection:
    connection.execute('''
        CREATE TABLE medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            expiry_date DATE NOT NULL,
            batch_number TEXT,
            category TEXT
        )
    ''')
    
    # Sample data
    connection.execute('''
        INSERT INTO medicines (name, quantity, expiry_date, batch_number, category)
        VALUES ('Paracetamol', 50, '2025-11-15', 'B12345', 'Pain Relief')
    ''')
    
    connection.execute('''
        INSERT INTO medicines (name, quantity, expiry_date, batch_number, category)
        VALUES ('Aspirin', 30, '2025-10-20', 'B67890', 'Pain Relief')
    ''')
    
    connection.commit()

print("Database initialized successfully!")
