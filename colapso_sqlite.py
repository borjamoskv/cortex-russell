import os
import re
import sqlite3

WORKSPACE_DIR = "/Users/borjafernandezangulo/.gemini/antigravity/scratch/cortex-russell"
DB_PATH = os.path.join(WORKSPACE_DIR, "cortex_ontology.db")
TARGET_DIRS = [
    os.path.join(WORKSPACE_DIR, "cortex/agents/primitives"),
    os.path.join(WORKSPACE_DIR, "cortex/agents/ontology")
]

def init_db(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            domain TEXT,
            col1 TEXT,
            col2 TEXT,
            col3 TEXT,
            col4 TEXT,
            col5 TEXT,
            source_file TEXT
        )
    ''')
    conn.commit()

def parse_markdown_table(filepath):
    entities = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Busca lineas de tabla que empiecen y terminen con |
    # Ignora lineas de separador |---|---|
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line.startswith('|') or not line.endswith('|'):
            continue
        if re.search(r'\|[-:\s]+\|', line):  # Separator line
            continue
        if ' ID ' in line or '|ID|' in line or '| ID|' in line or '|ID |' in line: # Header line
            continue
        
        parts = [p.strip() for p in line.strip('|').split('|')]
        if len(parts) >= 2:
            entity_id = parts[0]
            domain = os.path.basename(filepath).replace('.md', '')
            cols = parts[1:] + [''] * (5 - len(parts[1:])) # Pad to 5 columns
            entities.append((entity_id, domain, cols[0], cols[1], cols[2], cols[3], cols[4], filepath))
            
    return entities

def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    cursor = conn.cursor()
    
    total_inserted = 0
    
    for target_dir in TARGET_DIRS:
        if not os.path.exists(target_dir):
            continue
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    entities = parse_markdown_table(filepath)
                    for entity in entities:
                        try:
                            cursor.execute('''
                                INSERT OR REPLACE INTO entities 
                                (id, domain, col1, col2, col3, col4, col5, source_file) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', entity)
                            total_inserted += 1
                        except Exception as e:
                            print(f"Error inserting {entity[0]}: {e}")
                            
    conn.commit()
    conn.close()
    print(f"Colapso Termodinámico completado: {total_inserted} entidades inyectadas en SQLite (C5-REAL).")

if __name__ == "__main__":
    main()
