import requests
import json
import time

# --- URLs ---
categories_url = "https://www.pedidosya.com.ar/groceries/web/v1/vendors/183591/categories"
products_base_url = "https://www.pedidosya.com.ar/groceries/web/v1/vendors/183591/products"
output_filename = 'pedidosya_todos_los_productos.json'

# --- Solicitar Cookie al usuario ---
print("\n=== Configuración de Cookie ===")
print("Por favor, ingrese su cookie de PedidosYa:")
cookie = input("> ").strip()

# --- Cabeceras ---
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Cookie': cookie,
}

# --- Función para obtener productos de UNA categoría (la del script anterior) ---
def get_products_for_category(category_id, category_name):
    print(f"\n--- Obteniendo productos para Categoría: {category_name} (ID: {category_id}) ---")
    category_products = []
    page = 0
    max_pages_to_fetch = 10 # Límite por categoría

    while page < max_pages_to_fetch:
        current_url = f"{products_base_url}?categoryId={category_id}&limit=100&page={page}"
        print(f"  Obteniendo página {page}: {current_url}")
        try:
            response = requests.get(current_url, headers=headers, timeout=15) # Añadido timeout
            if response.status_code == 200:
                try:
                    data = response.json()
                    items = data.get('items', [])
                    last_page = data.get('lastPage', True)

                    if items:
                        # Añadir la categoría a cada producto para saber de dónde vino (opcional)
                        for item in items:
                            item['categoryName'] = category_name
                            item['categoryIdSource'] = category_id
                        category_products.extend(items)
                        print(f"    -> Recibidos {len(items)}. Total para categoría: {len(category_products)}")
                    else:
                         print("    -> No se encontraron más items en esta página.")
                         if not last_page:
                            print("    -> Marcando como última página ya que no hay items.")
                            last_page = True

                    if last_page:
                        print("    -> Última página alcanzada o sin items para esta categoría.")
                        break
                    else:
                        page += 1
                        sleep_time = 1.5 # Pausa entre páginas de la misma categoría
                        print(f"    -> Esperando {sleep_time} seg...")
                        time.sleep(sleep_time)

                except json.JSONDecodeError:
                    print(f"    -> Error JSON en página {page}.")
                    break
                except Exception as e_json:
                     print(f"    -> Error procesando JSON de página {page}: {e_json}")
                     break
            elif response.status_code in [401, 403]:
                 print(f"    -> Error {response.status_code} (Probable cookie inválida). Deteniendo categoría.")
                 return None # Indicar fallo de cookie
            else:
                print(f"    -> Error HTTP {response.status_code} en página {page}.")
                break
        except requests.exceptions.RequestException as e:
            print(f"    -> Error de conexión en página {page}: {e}")
            # Podrías implementar reintentos aquí
            break
        except Exception as e_general:
             print(f"    -> Error inesperado en página {page}: {e_general}")
             break

    return category_products

# --- 1. Obtener Categorías ---
all_categories_data = {} # Usaremos un diccionario para guardar por categoría
print(f"Obteniendo lista de categorías desde: {categories_url}")
subcategories_to_fetch = []
try:
    response_cat = requests.get(categories_url, headers=headers, timeout=10)
    if response_cat.status_code == 200:
        categories_data = response_cat.json()
        # Extraer las subcategorías (children)
        for main_category in categories_data.get('categories', []):
            for sub_category in main_category.get('children', []):
                cat_id = sub_category.get('id')
                cat_name = sub_category.get('name')
                if cat_id and cat_name and sub_category.get('status') == 'ACTIVE':
                     subcategories_to_fetch.append({'id': cat_id, 'name': cat_name})
        print(f"Se encontraron {len(subcategories_to_fetch)} subcategorías activas para procesar.")
    elif response_cat.status_code in [401, 403]:
         print(f"Error {response_cat.status_code} al obtener categorías. Probablemente la cookie es inválida.")
         subcategories_to_fetch = [] # No continuar si falla aquí
    else:
        print(f"Error HTTP {response_cat.status_code} al obtener categorías.")
        subcategories_to_fetch = []
except requests.exceptions.RequestException as e:
    print(f"Error de conexión al obtener categorías: {e}")
except json.JSONDecodeError:
    print("Error: La respuesta de categorías no es JSON válido.")
except Exception as e_cat:
     print(f"Error inesperado al obtener/procesar categorías: {e_cat}")


# --- 2. Obtener Productos para cada Subcategoría ---
if subcategories_to_fetch:
    total_products_all_categories = 0
    for category_info in subcategories_to_fetch:
        cat_id = category_info['id']
        cat_name = category_info['name']

        # Llamar a la función para obtener productos de esta categoría
        products = get_products_for_category(cat_id, cat_name)

        if products is None: # Chequea si hubo error de cookie
             print("!!! Se detectó un posible error de Cookie. Deteniendo el proceso general. !!!")
             break # Salir del bucle principal de categorías

        if products: # Solo añadir si se obtuvieron productos
             all_categories_data[cat_name] = products # Guardar en diccionario por nombre
             total_products_all_categories += len(products)
             print(f"  -> Finalizado categoría '{cat_name}'. Total acumulado general: {total_products_all_categories}")
        else:
             print(f"  -> No se obtuvieron productos para la categoría '{cat_name}' o hubo un error.")

        # Pausa MÁS LARGA entre categorías diferentes
        inter_category_sleep = 3
        print(f"\n== Esperando {inter_category_sleep} segundos antes de la siguiente CATEGORÍA ==\n")
        time.sleep(inter_category_sleep)

# --- 3. Guardar Resultados ---
print("\n--- Proceso General Finalizado ---")
if all_categories_data:
    print(f"Se obtuvieron datos para {len(all_categories_data)} categorías.")
    print(f"Guardando resultados en '{output_filename}'...")
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_categories_data, f, indent=4, ensure_ascii=False)
        print("¡Resultados guardados exitosamente!")
        
        # Ejecutar filtrar_ofertas.py
        print("\n=== Ejecutando filtrar_ofertas.py ===")
        import subprocess
        
        # Ejecutar filtrar_ofertas.py
        result_filter = subprocess.run(['python', 'filtrar_ofertas.py'], capture_output=True, text=True)
        print(result_filter.stdout)
        if result_filter.stderr:
            print("Errores:", result_filter.stderr)
        
        # Ejecutar detect_new_offers.py
        print("\n=== Ejecutando detect_new_offers.py ===")
        result_detect = subprocess.run(['python', 'detect_new_offers.py'], capture_output=True, text=True)
        print(result_detect.stdout)
        if result_detect.stderr:
            print("Errores:", result_detect.stderr)
            
    except IOError as e_io:
        print(f"Error de E/S al guardar el archivo: {e_io}")
    except Exception as e_write:
        print(f"Error inesperado al guardar el archivo: {e_write}")
else:
     print("No se obtuvieron datos de productos para guardar (posible error inicial o tienda vacía).")