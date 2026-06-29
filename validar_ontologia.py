import os
import re
import sys

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DIRS = [
    os.path.join(WORKSPACE_DIR, "cortex/ontology"),
    os.path.join(WORKSPACE_DIR, "cortex/agents/ontology")
]

def parse_markdown_table(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    headers = []
    rows = []
    
    for idx, line in enumerate(lines, 1):
        if not line.startswith('|') or not line.endswith('|'):
            continue
        if re.search(r'\|[-:\s]+\|', line):  # Separator line
            continue
        
        parts = [p.strip() for p in line.strip('|').split('|')]
        
        if not headers:
            headers = parts
            continue
            
        rows.append((idx, parts))
            
    return headers, rows

def main():
    errors = 0
    warnings = 0
    all_ids = {}
    
    print("[C5-REAL] Iniciando Auditoría de Ontologías...")
    
    for target_dir in TARGET_DIRS:
        if not os.path.exists(target_dir):
            continue
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, WORKSPACE_DIR)
                    headers, rows = parse_markdown_table(filepath)
                    
                    if not headers:
                        print(f"[WARN] {rel_path}: No se detectó cabecera de tabla válida.")
                        warnings += 1
                        continue
                        
                    if not rows:
                        print(f"[WARN] {rel_path}: La tabla está vacía o carece de filas de datos.")
                        warnings += 1
                        continue
                    
                    num_cols = len(headers)
                    
                    for line_idx, row in rows:
                        # Validar longitud de columnas
                        if len(row) != num_cols:
                            print(f"[ERROR] {rel_path}:L{line_idx} - Fila tiene {len(row)} columnas, se esperaban {num_cols}.")
                            errors += 1
                            
                        # Validar presencia de ID
                        if not row:
                            print(f"[ERROR] {rel_path}:L{line_idx} - Fila completamente vacía.")
                            errors += 1
                            continue
                            
                        entity_id = row[0]
                        if not entity_id:
                            print(f"[ERROR] {rel_path}:L{line_idx} - ID de entidad ausente.")
                            errors += 1
                            continue
                            
                        # Validar duplicados globales de ID
                        if entity_id in all_ids:
                            prev_path, prev_line = all_ids[entity_id]
                            print(f"[ERROR] {rel_path}:L{line_idx} - ID duplicado '{entity_id}'. Previamente visto en {prev_path}:L{prev_line}.")
                            errors += 1
                        else:
                            all_ids[entity_id] = (rel_path, line_idx)
                            
    print(f"\n[C5-REAL] Auditoría finalizada: {errors} Errores, {warnings} Advertencias.")
    if errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
