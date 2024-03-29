# For creating the zipfile
import zipfile

# For some mathmatical validations
import math

# For casting some numbers to decimals
from decimal import Decimal

# Famous Pandas library , to work with DataFrames
import pandas as pd

# Needed to work with robocorp RPA
from robocorp.tasks import task

# To interact with browser
from robocorp import browser

# To conncet to webpages
from RPA.HTTP import HTTP

# For creating some dates
from datetime import date

# Webpage to be scrapped
main_URL = "http://books.toscrape.com/index.html"

# Where I uploaded the "source" book inventory file
csv_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR4CyrkI46jNRJQhmeqidOeQsyNtPgECX6bkJrn0MTXOjpPQ1ihR_po7R-R5xWUHzqyNNONUNf-paLu/pub?output=csv"

# I put today's date into a variable
today = date.today()
today = today.strftime("%d_%m_%Y")

@task
def look_for_book_prices_and_save_them():
    """
    This is the main robot function

    """

    # Browser configuration
    browser.configure(
        browser_engine="firefox",
        screenshot="only-on-failure",
        headless=False,
        slowmo=100
    )

    download_csv()
    open_website_to_scrap()

    book_list = pd.read_csv("input/book_inventory_"+today+".csv")

    # I create the new columns on the CSV
    # Series are like vectors in Pandas, so I create empty vectors (new columns)
    book_list['Name_book_found'] = pd.Series()
    book_list['Price_book_found'] = pd.Series()
    book_list['Comparisson'] = pd.Series()

    # I will then loop for each row on the CSV
    for i in range(len(book_list)):

        # Saving the name of the book to look for
        book_to_look_for = book_list.loc[i,'Name']

        # Some validations in case the name has incorrect format
        if isinstance(book_to_look_for, str) == False:
            book_list.loc[i,'Name_book_found'] = "Book not found"
            continue

        # I save the category of the book
        caregory = book_list.loc[i,'Category']

        # I call the function that will look for the price of the book in the webpage and also return me the match made regarding the "Name"
        book_price,book_name = get_book_price(book_to_look_for,caregory)

        # I store both results on their corresponding columns in the CSV (DataFrame, for now)
        book_list.loc[i,'Name_book_found'] = book_name
        book_list.loc[i,'Price_book_found'] = book_price
        
        # I save in variables the different book prices, in order to then compare
        our_price = book_list.loc[i,'Our_price']
        their_price = book_list.loc[i,'Price_book_found']

        # Some validations in case there is no price to compare
        if isinstance(our_price, Decimal) == True:
            if math.isnan(our_price) == True:
                book_list.loc[i,'Comparisson'] = "No price from our side to compare"
                continue
        elif our_price == None or "":
            book_list.loc[i,'Comparisson'] = "No price from our side to compare"
            continue
        
        if their_price == None:
            book_list.loc[i,'Comparisson'] = "No competitor price to compare"
            book_list.loc[i,'Name_book_found'] = "Book not found"
            continue

        # In case the price on the website is with a comma, I will change it into a proper decimal format
        if "," in our_price:
            our_price = our_price.replace(",",".")

        # Finally, I cast both values into decimals before comparing
        our_price = Decimal(our_price)
        their_price = Decimal(their_price)
        
        # This is all the comparing logic. The result of the comparisson will be put on the "Comparisson" column
        if our_price == their_price:
            book_list.loc[i,'Comparisson'] = "Same price"
        elif our_price > their_price:
            book_list.loc[i,'Comparisson'] = "We are selling it more expensive"
        elif our_price < their_price:
            book_list.loc[i,'Comparisson'] = "We are selling it cheaper"
        else:
            book_list.loc[i,'Comparisson'] = "Could not compare"

    # Transforming the DataFrame into an output CSV
    book_list.to_csv("output/book_inventory_"+today+"result.csv")

    # Zipping the output CSV file
    zip_file("book_inventory_"+today+"result.csv")

# Function that will open the main website
def open_website_to_scrap():
    browser.goto(main_URL)

# Functino that downloads the CSV origin file
def download_csv():
    http = HTTP()
    http.download(url=csv_URL, overwrite=True, target_file="input/book_inventory_"+today+".csv")

# Important function, that will need as an input a book name, and its category. It will look in the corresponding part of the webpage for that book and then get the price.
def get_book_price(book_name,category):

    # I call the "map_category" function and get the mapped caregory in order to contruct the final URL where to look for the book
    category_mapped = map_category(category)

    # I build the specific URL of the book
    category_url = "http://books.toscrape.com/catalogue/category/books/"+category_mapped+"/index.html"

    # I go to that URL
    browser.goto(category_url)

    # Both XPATHs, one for looking for the price and another to look for the book name found
    base_search_xpath_price = "//article/h3/a[contains(text(),'"+book_name+"')]/parent::h3/parent::article//*[@class='price_color']"
    base_search_xpath_name =  "//article/h3/a[contains(text(),'"+book_name+"')]"

    page = browser.page()

    # I here use a try-except structure, because if no book is found, the robot would fail.
    try:
        webpage_price = page.locator(base_search_xpath_price).inner_html(timeout=30)
        webpage_price = str(webpage_price).replace("£","")
        webpage_price = Decimal(webpage_price)*Decimal(1.17)
        webpage_price = Decimal("%.2f" % round(webpage_price,2))
        
    except:
        # This is just a message for the log
        print("Error while looking for book price")
        # I took the decision to return both None if no book is found
        return None, None

    # If the book is found, the price should exist, so no try / except here used
    webpage_bookname = page.locator(base_search_xpath_name).inner_html(timeout=30)
    
    return webpage_price,webpage_bookname

# Function to map the category from the original CSV, in order to use the format for the URL's in the webpage
def map_category(unmapped):
    category_list = {
    "Travel" : "travel_2",
    "Mystery" : "mystery_3",
    "Historical Fiction" : "historical-fiction_4",
    "Sequential Art" : "sequential-art_5",
    "Classics" : "classics_6",
    "Philosophy" : "philosophy_7",
    "Romance" : "romance_8",
    "Womens Fiction" : "womens-fiction_9",
    "Fiction" : "fiction_10",
    "Childrens" : "childrens_11",
    "Religion" : "religion_12",
    "Nonfiction" : "nonfiction_13",
    "Music" : "music_14",
    "Default" : "default_15",
    "Science Fiction" : "science-fiction_16",
    "Sports and Games" : "sports-and-games_17",
    "Add a comment" : "add-a-comment_18",
    "Fantasy" : "fantasy_19",
    "New Adult" : "new-adult_20",
    "Young Adult" : "young-adult_21",
    "Science" : "science_22",
    "Poetry" : "poetry_23",
    "Paranormal" : "paranormal_24",
    "Art" : "art_25",
    "Psychology" : "psychology_26",
    "Autobiography" : "autobiography_27",
    "Parenting" : "parenting_28",
    "Adult Fiction" : "adult-fiction_29",
    "Humor" : "humor_30",
    "Horror" : "horror_31",
    "History" : "history_32",
    "Food and Drink" : "food-and-drink_33",
    "Christian Fiction" : "christian-fiction_34",
    "Business" : "business_35",
    "Biography" : "biography_36",
    "Thriller" : "thriller_37",
    "Contemporary" : "contemporary_38",
    "Spirituality" : "spirituality_39",
    "Academic" : "academic_40",
    "Self Help" : "self-help_41",
    "Historical" : "historical_42",
    "Christian" : "christian_43",
    "Suspense" : "suspense_44",
    "Short Stories" : "short-stories_45",
    "Novels" : "novels_46",
    "Health" : "health_47",
    "Politics" : "politics_48",
    "Cultural" : "cultural_49",
    "Erotica" : "erotica_50",
    "Crime" : "crime_51"
    }
    return category_list[unmapped]

# Function for zipping the final report
def zip_file(file):
    with zipfile.ZipFile('output/Comparisson_report.zip', 'w',
                        compression=zipfile.ZIP_DEFLATED,
                        compresslevel=9) as zf:
        zf.write("output/"+file, arcname=file)
