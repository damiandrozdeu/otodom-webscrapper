import requests
from bs4 import BeautifulSoup
import csv
import time

def scrape_otodom(start_page, end_page):
    base_url = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/cala-polska?page="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    properties = []
    
    for page in range(start_page, end_page + 1):
        url = base_url + str(page)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Błąd pobierania strony {page}")
            continue
        
        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.find_all("article", attrs={"data-cy": "listing-item"})
        
        for listing in listings:
            try:
                title_tag = listing.find("p", attrs={"data-cy": "listing-item-title"})
                price_tag = listing.find("span", class_="css-2bt9f1")
                location_tag = listing.find("p", class_="css-42r2ms")
                rooms_tag = listing.find("dt", string="Liczba pokoi")
                size_tag = listing.find("dt", string="Powierzchnia")
                link_tag = listing.find("a", attrs={"data-cy": "listing-item-link"})
                
                title = title_tag.text.strip() if title_tag else "Brak tytułu"
                price = price_tag.text.strip() if price_tag else "Brak ceny"
                location = location_tag.text.strip() if location_tag else "Brak lokalizacji"
                rooms = rooms_tag.find_next_sibling("dd").text.strip() if rooms_tag else "Brak danych"
                size = size_tag.find_next_sibling("dd").text.strip() if size_tag else "Brak danych"
                link = "https://www.otodom.pl" + link_tag["href"] if link_tag else "Brak linku"

                # Visit individual listing page to extract the description
                description = "Brak opisu"
                if link != "Brak linku":
                    desc_response = requests.get(link, headers=headers)
                    if desc_response.status_code == 200:
                        desc_soup = BeautifulSoup(desc_response.text, "html.parser")
                        desc_tag = desc_soup.find("div", class_="css-1t85kbn")  # Adjust class based on actual page structure
                        description = desc_tag.text.strip() if desc_tag else "Brak opisu"
                    else:
                        print(f"Błąd pobierania strony oferty: {link}")

                properties.append([title, price, location, rooms, size, link, description])

                time.sleep(1)  # Add delay to prevent blocking
                
            except Exception as e:
                print(f"Błąd podczas przetwarzania oferty na stronie {page}: {e}")
    
    # Save to CSV
    with open("otodom_listings.csv", "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Tytuł", "Cena", "Lokalizacja", "Liczba pokoi", "Metraż", "Link", "Opis"])
        writer.writerows(properties)
    
    print("Dane zapisane do otodom_listings.csv")

if __name__ == "__main__":
    start_page = int(input("Podaj numer początkowej strony: "))
    end_page = int(input("Podaj numer końcowej strony: "))
    scrape_otodom(start_page, end_page)
