# Imports
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

# Use proxy api to simplify web scraping
from scraper_api import ScraperAPIClient
client = ScraperAPIClient('api_key')

# Loop over multiple search results pages: 30 results per page * 10 pages
object_name = []
object_href = []
for i in range(10):
    if i == 0:
        url = 'https://www.yelp.com/search?find_desc=Restaurants&find_loc=Portland%2C+OR&ns=1'
    else:
        url = 'https://www.yelp.com/search?find_desc=Restaurants&find_loc=Portland%2C%20OR&start=' + str(i * 30)
    main_page = client.get(url).text
    soup = BeautifulSoup(main_page, 'lxml')
    subpages = soup.select('.text-size--inherit__373c0__2fB3p .link-color--inherit__373c0__3dzpk')
    for j in subpages[2:32]:
        object_name.append(j.string)
        object_href.append(j.get('href'))

# DataFrame: Master list: Business name; Business link
object_href = ['https://www.yelp.com' + url for url in object_href]
object_data = list(zip(object_name, object_href))
object_df = pd.DataFrame(data = object_data, columns = ['name', 'url'])

# Inspect duplicated values
print(sum(object_df.duplicated(subset = ['name'], keep = 'first')))

# Drop duplicated values
object_df.drop_duplicates(subset = ['name'], keep = 'first', inplace = True)

# Create csv file
with open('Business.csv', 'a', newline = '') as f:
    object_df.to_csv(f, index = False, header = True, encoding = 'utf8')

# Navigate the tree

# The find method: 
# # Signature: find(name, attrs, recursive, string, **kwargs)
# # If it cannot find anything, it returns none.

# The find_all method:
# # Signature: find_all(name, attrs, recursive, string, limit, **kwargs)
# # Search by a class attribute: class_=
# # Search by a dictionary: {"attribute": "value"}

# Extract the reviews information
def crawl_review_page(client, review_url):
    reviews_info = []

    html = client.get(review_url).text
    soup = BeautifulSoup(html, 'lxml')
    
    reviwers_block_list = soup.find_all('li', 
                                        {'class': 'lemon--li__373c0__1r9wz margin-b3__373c0__q1DuY padding-b3__373c0__342DA border--                                                            bottom__373c0__3qNtD border-color--default__373c0__3-ifU'})
    for reviewer_block in reviwers_block_list:
        # Reviewers: Name
        reviewer_name = reviewer_block.find('span', {'class': 'lemon--span__373c0__3997G text__373c0__2Kxyz fs-block text-color--blue-dark__373c0__1jX7S text-align--left__373c0__2XGa- text-weight--bold__373c0__1elNz'}).text
  
        # Reviewers: Location
        reviewers_location_info = reviewer_block.find('span', {'class': 
        'lemon--span__373c0__3997G text__373c0__2Kxyz text-color--normal__373c0__3xep9 text-align--left__373c0__2XGa- text-weight--bold__373c0__1elNz text-size--small__373c0__3NVWO'})
        if reviewers_location_info == None:
            reviewer_location = 'NA'
        else:
            reviewer_location = reviewers_location_info.text

        # Reviewers: Number of friends
        reviewer_friends_icon = reviewer_block.find('span', {'class': 'icon--18-friends'})
        if reviewer_friends_icon == None:
            reviewer_friends = 'NA'
        else:
            reviewer_friends = reviewer_friends_icon.next_sibling.text.split()[0]

        # Reviewers: Number of reviews
        reviewers_reviews_icon = reviewer_block.find('span', {'class': 'icon--18-review'})
        if reviewers_reviews_icon == None:
            reviewer_reviews = 'NA'
        else:
            reviewer_reviews = reviewers_reviews_icon.next_sibling.text.split()[0]

        # Reviewers: Number of photos
        reviewers_photos_icon = reviewer_block.find('span', {'class': 'icon--18-camera'})
        if reviewers_photos_icon == None:
            reviewer_photos = 'NA'
        else:
            reviewer_photos = reviewers_photos_icon.next_sibling.text.split()[0]

        # Reviewers: Ratings
        reviewers_ratings_img = reviewer_block.find('img', {'class': 'lemon--img__373c0__3GQUb offscreen__373c0__1KofL'})
        reviewer_ratings = reviewers_ratings_img.parent.attrs['aria-label']
        reviewer_ratings = float(reviewer_ratings.split(' ')[0])
    
        # Reviewers: Text
        reviewers_text_info = reviewer_block.find('span', {'class': 'lemon--span__373c0__3997G raw__373c0__3rKqk'})
        if reviewers_text_info == None:
            reviewer_text = 'NA'
        else:
            reviewer_text = reviewers_text_info.text
        
        # Reviewers: Rating dates
        reviewers_date_info = reviewer_block.find_all('span', {'class': 
        'lemon--span__373c0__3997G text__373c0__2Kxyz text-color--mid__373c0__jCeOG text-align--left__373c0__2XGa-'}, limit = 1)
        for j in reviewers_date_info:
            if j == None:
                reviewer_date = 'NA'
            else:
                reviewer_date = j.text
        
        # Put together 
        reviews_info += [(reviewer_name, reviewer_location, reviewer_friends, reviewer_reviews, 
                          reviewer_photos, reviewer_ratings, reviewer_text, reviewer_date)]

    return reviews_info

# Test the function output
crawl_review_page(client, 'https://www.yelp.com/biz/screen-door-portland?osq=Restaurants')

# Test the scraper output
for i in range(len(object_df)):
    business_link = object_df.iloc[i]['url']
    business_name = object_df.iloc[i]['name']
    obs = client.get(business_link).text
    soup = BeautifulSoup(obs, 'lxml')
    
    # One-To-One mapping: Get each business page information
    # # Name
    name = []
    name += [business_name]
    
    # # Total ratings
    ratings_img = soup.find('img', {'class': 'lemon--img__373c0__3GQUb offscreen__373c0__1KofL'})
    overall_ratings = []
    if ratings_img:
        ratings_info = ratings_img.parent
        overall_ratings.append(ratings_info.attrs['aria-label'])
    else:
        overall_ratings.append('NA')
    overall_ratings = [re.sub(' star rating', '',  r) for r in overall_ratings]
    overall_ratings = [float(r) for r in overall_ratings]

    # # Cuisine styles
    styles_info = soup.select('.margin-r1__373c0__zyKmV .link-size--inherit__373c0__1VFlE')
    styles = []
    if styles_info:
        for j in styles_info:
            styles.append(j.get_text())
    else:
        styles.append('NA')

    # # Price range
    price_info = soup.select('.text-bullet--after__373c0__3fS1Z.text-size--large__373c0__3t60B')
    price = []
    for j in price_info:
        price.append(j.get_text().replace(' ', ''))

    # # Number of reviews
    num_reviews_info = soup.select('.text-color--mid__373c0__jCeOG.text-size--large__373c0__3t60B')
    num_reviews = []
    for j in num_reviews_info:
        num_reviews.append(int(j.get_text().split(' ')[0]))

    # # Number of photos
    num_photos_info = soup.find_all('a', {'class': 'lemon--a__373c0__IEZFH button__373c0__3lYgT secondary-white__373c0__2OPxz'}, limit = 1)
    num_photos = []
    if num_photos_info:
        for j in num_photos_info:
            num_photos.append(j.get_text().split(' ')[2])
    else:
        num_photos.append('NA')

    # # Highlights
    high_info = soup.select('.display--inline-block__373c0__1ZKqC.margin-r1__373c0__zyKmV')
    high = []
    if high_info:
        for j in high_info:
            high.append(j.get_text().split(' ')[0])
    else:
        high.append('NA')
    
    # # DataFrame
    rating_data = list(zip(name, 
                           overall_ratings, 
                           styles, 
                           price,
                           num_reviews,
                           num_photos,
                           high))
    rating_df = pd.DataFrame(data = rating_data, columns = ['name',
                                                            'rating',
                                                            'styles',
                                                            'price_range',
                                                            'num_reviews',
                                                            'num_photos',
                                                            'highlights'])
    with open('Rating.csv', 'a', newline = '') as f:
        rating_df.to_csv(f, index = False, header = False, encoding = 'utf8')
    
    # One-To-Many mapping: Get each review page information
    # # Defined function
    reviewers_info = []
    for k in range(0, 3):
        if k == 0:
            review_link = business_link
        else:
            review_link = business_link + '&start=' + str(k * 20)
        print(review_link)
        page_reviewers_info = crawl_review_page(client, review_link)
        reviewers_info += page_reviewers_info
        
    # # DataFrame
    review_data = [(business_name, business_link, *(reviewers_info[i][:])) for i in range(len(reviewers_info))]  
    review_df = pd.DataFrame(data = review_data, columns = ['business', 
                                                            'hyperreference',
                                                            'reviewers',
                                                            'reviewers_location',
                                                            'reviewers_num_friends',
                                                            'reviewers_num_photos',
                                                            'reviewers_num_reviews',
                                                            'reviewers_rating',
                                                            'reviewers_text', 
                                                            'reviewers_rating_date'])
    with open('Review.csv', 'a', newline = '') as f:
        review_df.to_csv(f, index = False, header = False, encoding = 'utf8')
            
    print(f'Page {i}: O') 
    time.sleep(2)

