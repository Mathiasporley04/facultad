import csv
import json

def limpiar_datasets():
    print("Iniciando limpieza de datasets...\n")
    
    # 1. Limpieza de CSV
    print("--- Procesando CSV ---")
    csv_limpio = []
    # Leer con encoding latin-1 y delimitador ';'
    with open('mini-dataset.csv', 'r', encoding='latin-1') as f:
        # csv.DictReader maneja automáticamente las comas internas si están entrecomilladas
        # El delimitador del archivo roto es ';'
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if not row:
                continue
            
            clean_row = {}
            for k, v in row.items():
                if k is None:
                    continue
                # Asegurar de limpiar espacios extra en strings
                val = v.strip() if isinstance(v, str) else v
                
                # Gestionar valores faltantes ("N/A", "")
                if val == 'N/A' or val == '':
                    val = None
                    
                clean_row[k.strip()] = val
            
            csv_limpio.append(clean_row)
            
    print("Datos extraídos del CSV:")
    for row in csv_limpio:
        print(row)
    
    # Guardar CSV limpio, cambiamos a codificación utf-8 estándar y separador ','
    with open('mini-dataset_limpio.csv', 'w', encoding='utf-8', newline='') as f:
        if csv_limpio:
            fieldnames = csv_limpio[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=',')
            writer.writeheader()
            writer.writerows(csv_limpio)
            print("\nCSV limpio guardado como 'mini-dataset_limpio.csv' (UTF-8 y separado por comas)\n")
            
    # 2. Limpieza de JSON
    print("--- Procesando JSON ---")
    with open('mini-dataset2.json', 'r', encoding='utf-8') as f:
        data_json = json.load(f)
        
    json_limpio = []
    for item in data_json:
        nuevo_item = {}
        
        # ID
        nuevo_item['id'] = item.get('id')
        
        # Estandarizar nombre (nombre vs name)
        if 'nombre' in item and item['nombre']:
            nuevo_item['nombre'] = item['nombre']
        elif 'name' in item and item['name']:
            nuevo_item['nombre'] = item['name']
        else:
            nuevo_item['nombre'] = None
            
        # Estandarizar email (mail vs email)
        if 'email' in item and item['email']:
            nuevo_item['email'] = item['email']
        elif 'mail' in item and item['mail']:
            nuevo_item['email'] = item['mail']
        else:
            nuevo_item['email'] = None
            
        # Pais
        nuevo_item['pais'] = item.get('pais')
        
        # Reemplazar valores vacíos o strings como "N/A", "null" por None real (null en JSON)
        for k, v in nuevo_item.items():
            if isinstance(v, str):
                v_strip = v.strip()
                if v_strip == "" or v_strip.upper() == "N/A" or v_strip.lower() == "null":
                    nuevo_item[k] = None
                else:
                    nuevo_item[k] = v_strip
                    
        json_limpio.append(nuevo_item)
        
    print("Datos extraídos del JSON:")
    for item in json_limpio:
        print(item)
    
    # Guardar JSON limpio
    with open('mini-dataset2_limpio.json', 'w', encoding='utf-8') as f:
        json.dump(json_limpio, f, ensure_ascii=False, indent=4)
        print("\nJSON limpio guardado como 'mini-dataset2_limpio.json'")

if __name__ == '__main__':
    limpiar_datasets()
