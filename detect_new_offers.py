import json
import os
import sys

# --- Configuración de Nombres de Archivo ---
latest_offers_file = 'pedidosya_SOLO_OFERTAS_latest.json'
previous_offers_file = 'pedidosya_SOLO_OFERTAS_previous.json'

def load_and_extract_product_ids(filename):
    """
    Carga un archivo JSON de ofertas y extrae un set con los IDs de los productos
    y un diccionario mapeando ID a la información completa del producto.
    Maneja la estructura {categoria: [productos...]}.
    Devuelve (set_de_ids, dict_id_a_producto, error_message).
    """
    product_ids = set()
    product_data_map = {}
    if not os.path.exists(filename):
        return product_ids, product_data_map, f"Archivo no encontrado: {filename}"

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
             return product_ids, product_data_map, f"Error: El archivo {filename} no tiene el formato esperado (diccionario)."

        for category_name, product_list in data.items():
            if isinstance(product_list, list):
                for product in product_list:
                    product_id = product.get('id')
                    if product_id:
                        product_ids.add(product_id)
                        # Guardar datos completos, asegurando categoría si no está
                        if 'categoryName' not in product:
                             product['categoryName'] = category_name
                        product_data_map[product_id] = product
            else:
                print(f"Advertencia: Clave '{category_name}' en {filename} no contiene una lista.")

        return product_ids, product_data_map, None # Sin error

    except json.JSONDecodeError:
        return product_ids, product_data_map, f"Error: Archivo {filename} no es JSON válido."
    except Exception as e:
        return product_ids, product_data_map, f"Error inesperado leyendo {filename}: {e}"

# --- 1. Cargar Datos Actuales ---
print(f"Cargando ofertas actuales desde: {latest_offers_file}")
latest_ids, latest_products_map, error = load_and_extract_product_ids(latest_offers_file)
if error:
    print(error)
    sys.exit(1)
if not latest_ids:
    print("El archivo de ofertas actuales está vacío o no contiene productos con ID.")
    sys.exit(0)

print(f"Se encontraron {len(latest_ids)} IDs de productos en oferta en el archivo actual.")

# --- 2. Cargar Datos Anteriores ---
print(f"\nCargando ofertas anteriores desde: {previous_offers_file}")
previous_ids, _, error = load_and_extract_product_ids(previous_offers_file) # No necesitamos el map aquí
is_first_run = False
if error:
    # Si el archivo anterior no existe, es la primera ejecución o no se renombró
    print(f"Advertencia: {error}")
    print("-> Asumiendo que es la primera ejecución o falta el archivo anterior.")
    print("-> Todos los productos en oferta actuales se considerarán 'nuevos'.")
    is_first_run = True
    previous_ids = set() # Tratar como si no hubiera ofertas antes

print(f"Se encontraron {len(previous_ids)} IDs de productos en oferta en el archivo anterior.")

# --- 3. Comparar y Encontrar Nuevos IDs ---
print("\nComparando listas...")
newly_added_offer_ids = latest_ids - previous_ids # IDs en latest que NO están en previous

# --- 4. Mostrar Resultados ---
if newly_added_offer_ids:
    print("-" * 60)
    print(f"¡Se encontraron {len(newly_added_offer_ids)} NUEVAS OFERTAS!")
    if is_first_run:
         print("(Detectadas en la primera comparación o archivo anterior ausente)")
    print("-" * 60)

    for i, product_id in enumerate(newly_added_offer_ids):
        # Obtener los detalles del producto nuevo del diccionario 'latest_products_map'
        product_info = latest_products_map.get(product_id)
        if product_info:
            print(f"*** Nueva Oferta #{i + 1} (ID: {product_id}) ***")
            # Imprimir info completa del producto nuevo
            print(json.dumps(product_info, indent=4, ensure_ascii=False))
            print("-" * 40) # Separador más corto
        else:
            # Esto no debería pasar si la carga fue correcta, pero por si acaso
            print(f"*** Nueva Oferta #{i + 1} (ID: {product_id}) - Error: No se encontraron detalles ***")
            print("-" * 40)

elif not is_first_run: # Solo decir que no hay *nuevas* si no es la primera ejecución
    print("-" * 60)
    print("No se encontraron nuevas ofertas desde la última comparación.")
    print("-" * 60)
elif is_first_run and not latest_ids:
    print("-" * 60)
    print("No se encontraron ofertas en el archivo actual para marcar como nuevas.")
    print("-" * 60)

# --- Opcional: Detectar ofertas que desaparecieron ---
# removed_offer_ids = previous_ids - latest_ids
# if removed_offer_ids:
#     print(f"\nSe detectaron {len(removed_offer_ids)} ofertas que ya NO están disponibles.")
#     # Podrías cargar los detalles del archivo anterior para mostrarlas si quisieras

print("\nAnálisis de nuevas ofertas completado.")