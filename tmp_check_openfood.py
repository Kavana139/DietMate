import urllib.request, urllib.parse, json
qs = ['masala dosa', 'dosa', 'rice dosa', 'masala']
for q in qs:
    url = 'https://world.openfoodfacts.org/cgi/search.pl?search_terms=' + urllib.parse.quote(q) + '&search_simple=1&action=process&json=1&page_size=2'
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        print('QUERY', q, 'COUNT', data.get('count'))
        for p in data.get('products', []):
            print('  NAME', repr(p.get('product_name')), 'BRANDS', repr(p.get('brands')))
            nutr = p.get('nutriments', {})
            print('   kcal', nutr.get('energy-kcal_100g'), 'prot', nutr.get('proteins_100g'), 'carb', nutr.get('carbohydrates_100g'), 'fat', nutr.get('fat_100g'))
    except Exception as e:
        print('ERROR', q, e)
