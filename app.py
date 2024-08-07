from fastapi import FastAPI, Request, HTTPException, Depends, File,Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import shutil
import psycopg2
from dotenv import load_dotenv
import os

app = FastAPI()

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")

load_dotenv('.env')

# Read the CSV file
df = pd.read_csv("restaurants.csv", encoding='ISO-8859-1')

# Convert the DataFrame to a dictionary for easy access
# restaurants = df.to_dict(orient='records')


conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host="postgres",
    port=os.getenv("DATABASE_PORT")
)

cursor = conn.cursor()


# Query to fetch column names from a specific table
table_name = 'restaurant_info'
cursor.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = %s
""", (table_name,))

# Fetch all rows from the result set
columns = cursor.fetchall()
# Print the column names
for column in columns:
    print(column[0])

columns = df.columns.tolist()

cursor = conn.cursor()

query = f"""
    SELECT *
    FROM restaurant_info;
    """

cursor.execute(query)
restaurants_details = cursor.fetchall()

all_restaurants = []

for k in restaurants_details:
    l = list(k)
    all_restaurants.append(l)

restaurants = []
for row in all_restaurants:
    row_dict = dict(zip(columns, row))
    restaurants.append(row_dict)
for i in range(5):
    print(restaurants[i])

PER_PAGE = 10

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@app.get("/sign")
def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/sign")
async def signup(
    request: Request, username: str = Form(...), email: str = Form(...),password1: str = Form(...),password2:str = Form(...) 
):
   
    cur = conn.cursor()
    cur.execute("INSERT INTO users(Username,Email,Password_) VALUES (%s, %s,%s)", (username,email,password1))
    conn.commit()
    cur.close() 
 
    return RedirectResponse("/login", status_code=303)

@app.get("/login")
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def do_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE Username=%s and Password_=%s", (username,password))
    existing_user = cur.fetchone()
    cur.close()
    
    if existing_user:
        print(existing_user)
        return RedirectResponse("/home", status_code=303)
    
    else:
        return JSONResponse(status_code=401, content={"message": "Wrong credentials"})



# Home route
@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, page: int = 1):
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    paginated_restaurants = restaurants[start:end]
    
    prev_url = None
    next_url = None

    if start > 0:
        prev_url = f"/home?page={page - 1}"
    if end < len(restaurants):
        next_url = f"/home?page={page + 1}"
    
    return templates.TemplateResponse(
        "home.html", 
        {"request": request, "restaurants": paginated_restaurants, "prev_url": prev_url, "next_url": next_url}
    )

# Endpoint to retrieve restaurant details by ID and render template
@app.get("/restaurant/{restaurant_id}", response_class=HTMLResponse)
async def get_restaurant(request: Request, restaurant_id: str):
    for restaurant in restaurants:
        if restaurant['Restaurant ID'] == restaurant_id:
            return templates.TemplateResponse("restaurant.html", {"request": request, "restaurant": restaurant})
    raise HTTPException(status_code=404, detail="Restaurant not found")

# Route to handle the search form submission
@app.get("/search")
async def search(request: Request, restaurant_id: str):
    return RedirectResponse(url=f"/restaurant/{restaurant_id}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)