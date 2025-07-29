# Manual checking script
import requests
from bs4 import BeautifulSoup

def manual_check():
    url = "https://www.croma.com/vivo-x200-fe-5g-12gb-ram-256gb-frost-blue-/p/316890"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    
    print(f"Manually checking Vivo X200 FE 5G...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("Successfully loaded product page")
        
        # Save HTML for inspection
        with open("vivo_x200_manual_check.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Saved HTML to vivo_x200_manual_check.html")
        
        # Parse and analyze the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check page title
        title = soup.title.text if soup.title else "No title"
        print(f"Page title: {title}")
        
        # Look for Add to Cart button
        add_to_cart_buttons = soup.select('button[data-testid="add-to-cart"], .pdp-action, .add-to-cart, .buy-button')
        if add_to_cart_buttons:
            print(f"Found {len(add_to_cart_buttons)} potential Add to Cart buttons:")
            for i, button in enumerate(add_to_cart_buttons):
                print(f"  Button {i+1}: Text='{button.text.strip()}', Class='{button.get('class')}', Disabled='{button.get('disabled')}'")
        else:
            print("No Add to Cart buttons found")
        
        # Check for "Out of Stock" text
        if "out of stock" in response.text.lower():
            print("Found 'out of stock' text on the page")
        else:
            print("No 'out of stock' text found")
            
        # Check for price elements
        price_elements = soup.select('.price, .pdp-price, [data-testid="price"]')
        if price_elements:
            print("Found price elements:")
            for i, element in enumerate(price_elements):
                print(f"  Price {i+1}: '{element.text.strip()}'")
        
        print("\nBased on manual analysis:")
        if "out of stock" not in response.text.lower() and add_to_cart_buttons and not all(button.get('disabled') for button in add_to_cart_buttons):
            print("✅ Vivo X200 FE 5G appears to be IN STOCK")
        else:
            print("❌ Vivo X200 FE 5G appears to be OUT OF STOCK")
    else:
        print(f"Failed to load product page. Status code: {response.status_code}")

# Run the manual check
if __name__ == "__main__":
    manual_check()
