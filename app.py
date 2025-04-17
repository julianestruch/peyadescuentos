import json
import os
from flask import Flask, render_template, url_for, request

app = Flask(__name__)

JSON_FILE = 'pedidosya_SOLO_OFERTAS.json'

def load_offers():
    """Carga y valida los datos del JSON."""
    if not os.path.exists(JSON_FILE):
        return None, f"Error: No se encontró el archivo '{JSON_FILE}'."
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            offers_by_category = json.load(f)
        if not isinstance(offers_by_category, dict) or not offers_by_category:
            return None, f"Archivo '{JSON_FILE}' vacío o formato incorrecto."
        # Asegurarse de que el nombre de la categoría esté en cada producto
        for category_name, product_list in offers_by_category.items():
            if isinstance(product_list, list):
                for product in product_list:
                    if 'categoryName' not in product:
                        product['categoryName'] = category_name
        return offers_by_category, None
    except json.JSONDecodeError:
        return None, f"Error: Archivo '{JSON_FILE}' no es JSON válido."
    except Exception as e:
        return None, f"Error inesperado al leer archivo: {e}"

def calculate_discount_percentage(product):
    """Calcula un porcentaje de descuento ESTIMADO."""
    # ... (igual que antes) ...
    percentage = 0.0
    pricing = product.get('pricing', {})
    before_price = pricing.get('beforePrice')
    current_price = pricing.get('price')
    if before_price is not None and current_price is not None and before_price > 0 and before_price > current_price:
        try: percentage = ((float(before_price) - float(current_price)) / float(before_price)) * 100; return percentage
        except: pass
    campaigns = product.get('campaigns')
    if campaigns and isinstance(campaigns, list) and len(campaigns) > 0:
        campaign = campaigns[0]; config = campaign.get('configuration', {}); campaign_type = campaign.get('type')
        config_type = config.get('type'); value = config.get('value'); pay = config.get('pay'); take = config.get('take')
        try:
            if campaign_type == 'percentageDiscount' and config_type == 'PERCENTAGE' and value is not None: percentage = float(value)
            elif campaign_type == 'multi-buy' and config_type == 'free_item' and take is not None and pay is not None and take > pay and pay >= 0: percentage = ((float(take) - float(pay)) / float(take)) * 100
            elif campaign_type == 'sameItemBundle' and config_type == 'percentage' and value is not None and take is not None and take > 0: percentage = float(value) / float(take)
        except: percentage = 0.0
    return percentage

@app.route('/')
def mostrar_ofertas_con_filtro():
    """
    Carga datos, filtra por búsqueda, procesa según 'sort'.
    """
    sort_mode = request.args.get('sort', 'category')
    search_query = request.args.get('search', '').strip() # Leer término de búsqueda

    offers_by_category_loaded, error_message = load_offers()

    filtered_offers_by_category = {} # Para guardar datos después de filtrar
    all_offers_list_filtered = []   # Para guardar datos aplanados después de filtrar

    if offers_by_category_loaded:
        print(f"Filtrando por: '{search_query}'")
        search_query_lower = search_query.lower()
        # --- Filtrar por búsqueda ---
        for category_name, product_list in offers_by_category_loaded.items():
            if isinstance(product_list, list):
                matching_products = []
                for product in product_list:
                    product_name = product.get('name', '')
                    # Si no hay búsqueda o si el término está en el nombre (insensible)
                    if not search_query_lower or search_query_lower in product_name.lower():
                        # Calcular descuento si se necesita ordenar por él más tarde
                        if sort_mode == 'discount':
                             product['discount_percentage'] = calculate_discount_percentage(product)
                        matching_products.append(product)

                if matching_products: # Solo añadir la categoría si tiene productos coincidentes
                    filtered_offers_by_category[category_name] = matching_products
                    if sort_mode != 'category': # Si no es por categoría, aplanar
                        all_offers_list_filtered.extend(matching_products)

        if not filtered_offers_by_category and search_query:
             # No limpiar error_message si ya existe uno por carga de archivo
             if not error_message:
                  error_message = f"No se encontraron productos que coincidan con '{search_query}'."

    template_data = {
        "error_message": error_message,
        "current_sort": sort_mode,
        "search_query": search_query, # Pasar el query a la plantilla
        "offers_by_category": {},
        "products_sorted": []
    }

    # --- Ordenar o agrupar los datos YA FILTRADOS ---
    if filtered_offers_by_category: # Si hay datos después de filtrar
        if sort_mode == 'price':
            if all_offers_list_filtered:
                try:
                    all_offers_list_filtered.sort(key=lambda p: p.get('pricing', {}).get('price', float('inf')))
                    template_data["products_sorted"] = all_offers_list_filtered
                    print(f"Datos filtrados y ordenados por precio ({len(all_offers_list_filtered)} productos)")
                except Exception as e_sort:
                    template_data["error_message"] = f"Error al ordenar por precio: {e_sort}"
            # else: No hacer nada si la lista está vacía, el mensaje de error ya se habrá puesto

        elif sort_mode == 'discount':
            if all_offers_list_filtered:
                try:
                    all_offers_list_filtered.sort(key=lambda p: p.get('discount_percentage', 0.0), reverse=True)
                    template_data["products_sorted"] = all_offers_list_filtered
                    print(f"Datos filtrados y ordenados por descuento ({len(all_offers_list_filtered)} productos)")
                except Exception as e_sort:
                    template_data["error_message"] = f"Error al ordenar por descuento: {e_sort}"
            # else: No hacer nada si la lista está vacía

        else: # 'category'
            template_data["offers_by_category"] = filtered_offers_by_category # Usar los datos ya filtrados por búsqueda
            print("Datos filtrados y agrupados por categoría.")


    return render_template('index.html', **template_data)


if __name__ == '__main__':
    # Listen on all network interfaces with your local IP
    app.run(host='192.168.0.14', port=5000, debug=True)