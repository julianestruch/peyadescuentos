import json
import os
import sys

# --- Configuración ---
# Nombre del archivo JSON de entrada (con TODOS los productos)
input_filename = 'pedidosya_todos_los_productos.json'
# Nombre del archivo JSON de salida (SOLO con ofertas)
output_filename_offers = 'pedidosya_SOLO_OFERTAS.json'

# --- 1. Verificar si el archivo de entrada existe ---
if not os.path.exists(input_filename):
    print(f"Error: El archivo de entrada '{input_filename}' no se encontró.")
    print("Asegúrate de que el archivo exista en la misma carpeta y que contenga todos los productos.")
    sys.exit(1)

# --- 2. Cargar los datos del archivo JSON de entrada ---
print(f"Cargando datos desde '{input_filename}'...")
try:
    with open(input_filename, 'r', encoding='utf-8') as f:
        # Asume que el JSON es un diccionario {nombre_categoria: [lista_productos, ...]}
        all_data = json.load(f)
    print("Datos cargados exitosamente.")
except json.JSONDecodeError:
    print(f"Error: El archivo '{input_filename}' no es un JSON válido.")
    sys.exit(1)
except IOError as e:
    print(f"Error al leer el archivo '{input_filename}': {e}")
    sys.exit(1)
except Exception as e:
    print(f"Ocurrió un error inesperado al cargar el archivo: {e}")
    sys.exit(1)

# --- 3. Filtrar productos en oferta ---
print("Filtrando productos en oferta...")
discounted_products_by_category = {}
total_discounted_count = 0

# Iterar a través de cada categoría y su lista de productos en los datos cargados
for category_name, product_list in all_data.items():
    offers_in_category = [] # Lista para guardar las ofertas de esta categoría específica

    # Verificar que product_list sea una lista (por si el JSON tuviera algún error)
    if isinstance(product_list, list):
        for product in product_list:
            # --- Lógica para identificar si es una oferta ---
            is_offer = False # Empezar asumiendo que no es oferta

            # Criterio 1: ¿El campo 'campaigns' existe y NO está vacío?
            if product.get('campaigns'): # bool(lista_no_vacia) es True
                is_offer = True

            # Criterio 2 (Alternativo/Adicional): ¿Hay descuento directo en el precio?
            pricing = product.get('pricing')
            if not is_offer and pricing: # Solo chequear si el criterio 1 no se cumplió
                before_price = pricing.get('beforePrice')
                current_price = pricing.get('price')
                # Verificar que ambos precios existan y beforePrice sea mayor
                if before_price is not None and current_price is not None and before_price > current_price:
                    is_offer = True
            # -------------------------------------------------

            # Si el producto fue identificado como oferta, agregarlo a la lista de la categoría
            if is_offer:
                offers_in_category.append(product)

    # Si se encontraron ofertas en esta categoría, añadir la lista al diccionario final
    if offers_in_category:
        discounted_products_by_category[category_name] = offers_in_category
        total_discounted_count += len(offers_in_category)
        print(f"  -> {len(offers_in_category)} ofertas encontradas en '{category_name}'")

# --- 4. Guardar los productos filtrados en el nuevo archivo JSON ---
if discounted_products_by_category:
    print(f"\nTotal de productos en oferta encontrados en todas las categorías: {total_discounted_count}")
    print(f"Guardando SOLO OFERTAS en '{output_filename_offers}'...")
    try:
        with open(output_filename_offers, 'w', encoding='utf-8') as f:
            json.dump(discounted_products_by_category, f, indent=4, ensure_ascii=False)
        print("¡Archivo con solo ofertas guardado exitosamente!")
    except IOError as e_io:
        print(f"Error de E/S al guardar el archivo de ofertas: {e_io}")
    except Exception as e_write_offers:
        print(f"Error inesperado al guardar el archivo de ofertas: {e_write_offers}")
else:
    print("\nNo se encontraron productos en oferta en el archivo de entrada.")

print("\nProceso de filtrado completado.")