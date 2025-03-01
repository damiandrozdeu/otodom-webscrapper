import requests
from bs4 import BeautifulSoup
import csv
import time

def scrape_listing_details(url):
    """Funkcja do scrapowania szczegółowych danych z pojedynczej strony oferty"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {}
            
        soup = BeautifulSoup(response.text, "html.parser")
        details = {}

        # Podstawowe informacje
        details['Tytuł'] = soup.find("h1").text.strip() if soup.find("h1") else "Brak tytułu"
        details['Cena'] = soup.find("strong", {"data-cy": "adPageHeaderPrice"}).text.strip() if soup.find("strong", {"data-cy": "adPageHeaderPrice"}) else "Brak ceny"
        
        # Lokalizacja
        location_tag = soup.find("a", class_="css-1jjm9oe")
        details['Lokalizacja'] = location_tag.text.strip() if location_tag else "Brak lokalizacji"

        # Metraż i piętro
        details['Metraż'] = soup.find("div", class_="css-1ftqasz").text.strip() if soup.find("div", class_="css-1ftqasz") else "Brak danych"
        
        # Piętro z apostrofem
        # Piętro z apostrofem
 # Piętro z apostrofem
# Poprawione scrapowanie piętra
        details['Piętro'] = "Brak danych"
        info_sections = soup.find_all("div", class_="css-1xw0jqp eows69w1")
        for section in info_sections:
            label = section.find("p", class_="eows69w2 css-1airkmu")
            if label and "Piętro" in label.text:
                floor_value = label.find_next_sibling("p", class_="eows69w2 css-1airkmu")
                if floor_value:
                    floor_text = floor_value.text.strip()
                    # Dodaj apostrof przed wartością i formatuj jako tekst
                    details['Piętro'] = f"'{floor_text}"  # Gwarantuje format tekstowy w CSV
                break

        # Dodatkowe szczegóły
        for item in soup.find_all("div", class_="css-1xw0jqp"):
            label = item.find("p", class_="eows69w2")
            value = item.find_all("p", class_="eows69w2")[-1]
            if label and value:
                details[label.text.strip().replace(":", "")] = value.text.strip()

        # Informacje dodatkowe
        additional_info_list = [item.text.strip() for item in soup.find_all("span", class_="css-axw7ok")]
        details['Informacje dodatkowe'] = " ".join(additional_info_list) if additional_info_list else "Brak danych"

        return {
            'Ogrzewanie': details.get("Ogrzewanie", "Brak danych"),
            'Czynsz': details.get("Czynsz", "Brak danych"),
            'Stan wykończenia': details.get("Stan wykończenia", "Brak danych"),
            'Rynek': details.get("Rynek", "Brak danych"),
            'Forma własności': details.get("Forma własności", "Brak danych"),
            'Dostępne od': details.get("Dostępne od", "Brak danych"),
            'Typ ogłoszeniodawcy': details.get("Typ ogłoszeniodawcy", "Brak danych"),
            'Rok budowy': details.get("Rok budowy", "Brak danych"),
            'Winda': details.get("Winda", "Brak danych"),
            'Rodzaj zabudowy': details.get("Rodzaj zabudowy", "Brak danych"),
            'Materiał budynku': details.get("Materiał budynku", "Brak danych"),
            'Okna': details.get("Okna", "Brak danych"),
            'Media': details.get("Media", "Brak danych"),
            **details
        }

    except Exception as e:
        print(f"Błąd podczas scrapowania {url}: {e}")
        return {}

def scrape_otodom(start_page, end_page):
    base_url = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?limit=24&ownerTypeSingleSelect=ALL&by=DEFAULT&direction=DESC&viewType=listing&page="
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    properties = []
    
    for page in range(start_page, end_page + 1):
        print(f"Scrapowanie strony {page}...")
        url = base_url + str(page)
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Błąd pobierania strony {page}")
            continue
            
        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.find_all("article", attrs={"data-cy": "listing-item"})

        for listing in listings:
            try:
                link_tag = listing.find("a", attrs={"data-cy": "listing-item-link"})
                if not link_tag:
                    continue
                    
                full_url = "https://www.otodom.pl" + link_tag["href"]
                print(f"Przetwarzanie oferty: {full_url}")
                
                # Scrapowanie szczegółów z pojedynczej strony
                details = scrape_listing_details(full_url)
                
                # Dodawanie do wyników
                properties.append({
                    'Tytuł': details.get('Tytuł', 'Brak danych'),
                    'Cena': details.get('Cena', 'Brak danych'),
                    'Lokalizacja': details.get('Lokalizacja', 'Brak danych'),
                    'Metraż': details.get('Metraż', 'Brak danych'),
                    'Piętro': details.get('Piętro', 'Brak danych'),
                    'Ogrzewanie': details.get('Ogrzewanie', 'Brak danych'),
                    'Czynsz': details.get('Czynsz', 'Brak danych'),
                    'Stan wykończenia': details.get('Stan wykończenia', 'Brak danych'),
                    'Rynek': details.get('Rynek', 'Brak danych'),
                    'Forma własności': details.get('Forma własności', 'Brak danych'),
                    'Dostępne od': details.get('Dostępne od', 'Brak danych'),
                    'Typ ogłoszeniodawcy': details.get('Typ ogłoszeniodawcy', 'Brak danych'),
                    'Informacje dodatkowe': details.get('Informacje dodatkowe', 'Brak danych'),
                    'Rok budowy': details.get('Rok budowy', 'Brak danych'),
                    'Winda': details.get('Winda', 'Brak danych'),
                    'Rodzaj zabudowy': details.get('Rodzaj zabudowy', 'Brak danych'),
                    'Materiał budynku': details.get('Materiał budynku', 'Brak danych'),
                    'Okna': details.get('Okna', 'Brak danych'),
                    'Media': details.get('Media', 'Brak danych'),
                    'Link': full_url
                })
                
                time.sleep(1.5)  # Zwiększone opóźnienie dla bezpieczeństwa

            except Exception as e:
                print(f"Błąd przetwarzania oferty: {e}")

    # Zapis do CSV
    with open("otodom_pelne_dane.csv", "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=[
            'Tytuł', 'Cena', 'Lokalizacja', 'Metraż', 'Piętro',
            'Ogrzewanie', 'Czynsz', 'Stan wykończenia', 'Rynek', 
            'Forma własności', 'Dostępne od', 'Typ ogłoszeniodawcy',
            'Informacje dodatkowe', 'Rok budowy', 'Winda',
            'Rodzaj zabudowy', 'Materiał budynku', 'Okna', 'Media', 'Link'
        ])
        writer.writeheader()
        # Dodaj apostrof do wszystkich wartości w kolumnie "Piętro"
        for prop in properties:
            prop['Piętro'] = f"'{prop.get('Piętro', 'Brak danych')}"
            writer.writerow(prop)

    print("Dane zapisane do otodom_pelne_dane.csv")

if __name__ == "__main__":
    start_page = int(input("Podaj numer początkowej strony: "))
    end_page = int(input("Podaj numer końcowej strony: "))
    scrape_otodom(start_page, end_page)