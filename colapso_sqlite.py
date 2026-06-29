import os
import re
import sqlite3

WORKSPACE_DIR = "/Users/borjafernandezangulo/.gemini/antigravity/scratch/cortex-russell"
DB_PATH = os.path.join(WORKSPACE_DIR, "cortex_ontology.db")
TARGET_DIRS = [
    os.path.join(WORKSPACE_DIR, "cortex/ontology"),
    os.path.join(WORKSPACE_DIR, "cortex/agents/ontology")
]

def sanitize_column_name(name):
    name = name.lower()
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n'
    }
    for char, repl in replacements.items():
        name = name.replace(char, repl)
    name = re.sub(r'[^a-z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def parse_markdown_table(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    headers = []
    rows = []
    
    for line in lines:
        if not line.startswith('|') or not line.endswith('|'):
            continue
        if re.search(r'\|[-:\s]+\|', line):  # Separator line |---|---|
            continue
        
        parts = [p.strip() for p in line.strip('|').split('|')]
        
        # El primer elemento no-separador que encontremos es la cabecera
        if not headers:
            headers = [sanitize_column_name(p) for p in parts]
            continue
            
        # Si ya tenemos cabecera, son filas de datos
        if len(parts) >= 1:
            rows.append(parts)
            
    return headers, rows

def main():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception as e:
            print(f"Advertencia: No se pudo eliminar DB existente: {e}")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    tables_created = []
    
    for target_dir in TARGET_DIRS:
        if not os.path.exists(target_dir):
            continue
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    headers, rows = parse_markdown_table(filepath)
                    
                    if not headers or not rows:
                        continue
                    
                    # El nombre de la tabla es el nombre del archivo sin extension
                    table_name = sanitize_column_name(os.path.basename(file).replace('.md', ''))
                    
                    # Asegurar columna ID primaria
                    if 'id' not in headers:
                        print(f"Error: La tabla {table_name} no tiene columna ID primaria. Omitiendo.")
                        continue
                    
                    # Construir sentencia CREATE TABLE
                    # Para garantizar tipos de datos de texto
                    col_defs = []
                    for h in headers:
                        if h == 'id':
                            col_defs.append("id TEXT PRIMARY KEY")
                        else:
                            col_defs.append(f"{h} TEXT")
                    col_defs.append("source_file TEXT")
                    
                    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})"
                    cursor.execute(create_sql)
                    
                    # Insertar filas
                    for row in rows:
                        # Rellenar la fila si tiene menos columnas que la cabecera
                        row_data = row + [''] * (len(headers) - len(row))
                        # Recortar si tiene mas
                        row_data = row_data[:len(headers)]
                        # Agregar path de origen
                        row_data.append(filepath)
                        
                        placeholders = ', '.join(['?'] * len(row_data))
                        cols_str = ', '.join(headers + ['source_file'])
                        
                        insert_sql = f"INSERT OR REPLACE INTO {table_name} ({cols_str}) VALUES ({placeholders})"
                        try:
                            cursor.execute(insert_sql, row_data)
                            total_inserted += 1
                        except Exception as e:
                            print(f"Error inyectando fila en {table_name}: {e}")
                    
                    tables_created.append(table_name)
                    
    conn.commit()
    conn.close()
    
    print(f"Colapso Termodinámico completado (C5-REAL).")
    print(f"Tablas creadas: {', '.join(tables_created)}")
    print(f"Total de entidades inyectadas: {total_inserted}")

if __name__ == "__main__":
    main()
