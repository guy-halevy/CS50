import os
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
# from httpx import URL, Proxy, Timeout, Response, BaseTransport, AsyncBaseTransport
from openai import OpenAI
from helpers import apology
import socket

## load chatGPT
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
client = OpenAI()

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///DataBase.db")

## this code was taken from the Finance exercise


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

## register new user
## Reused the code I wrote on the Finance exercise


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 400)
        username = request.form.get("username")
        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 400)
        password = request.form.get("password")
        if not request.form.get("confirmation"):
            return apology("must provide password", 400)
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if password != request.form.get("confirmation"):
            return apology("Passwords do not match", 400)
        if len(user) == 1:
            return apology("Username already taken", 400)
        db.execute("insert into users (username, hash) values(?, ?)", username, generate_password_hash(password))
        session["user_id"] = db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]

        # If an "anonymous user" wants to save his plan, redirect to login or register
        if request.form.get("save"):
            # print(1)
            visbol_prompt = request.form.get("visbol_prompt")
            name = request.form.get("save")
            ip = name.split("id")[0]
            to = name.split("id")[1]
            t_o = to.replace(" ", "_")
            user_id = session["user_id"]
            name1 = f"{ip}id{t_o}"
            name2 = f"{user_id}id{t_o}"
            db.execute("DROP TABLE IF EXISTS ? ", name2)
            db.execute("ALTER TABLE ? RENAME TO ?", name1, name2)
            if not db.execute("SELECT * FROM cantrise where id=? and cantrise=? ", user_id, to):
                db.execute("INSERT INTO cantrise (id,cantrise,visbol_prompt) VALUES (?,?,?)", user_id, to, visbol_prompt)
        return redirect("/")
    return render_template("register.html")

## Login , most of it was taken from the Finance exercise


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)
        # Remember which user has logged in

        # If an "anonymous user" wants to save his trip plan, redirect to login or register
        session["user_id"] = rows[0]["id"]
        if request.form.get("save"):
            visbol_prompt = request.form.get("visbol_prompt")
            name = request.form.get("save")
            ip = name.split("id")[0]
            to = name.split("id")[1]
            user_id = session["user_id"]
            t_o = to.replace(" ", "_")
            name1 = f"{ip}id{t_o}"
            name2 = f"{user_id}id{t_o}"
            db.execute("DROP TABLE IF EXISTS ? ", name2)
            db.execute("ALTER TABLE ? RENAME TO ?", name1, name2)
            if db.execute("SELECT * FROM cantrise where id=? and cantrise=? ", user_id, to):
                db.execute("DELETE FROM cantrise where (id = ?) AND (cantrise= ? )", user_id, to)
            db.execute("INSERT INTO cantrise (id,cantrise,visbol_prompt) VALUES (?,?,?)", user_id, to, visbol_prompt)
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# logout code, taken from Finance


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")


name = ""


@app.route("/", methods=["GET", "POST"])
# @login_required
def index():
    if request.method == "POST":

        ##On the home page, the the user selects to see/modify an existing trip:
        if request.form.get("home"):
            ## print("1")
            ## Check if user is loged-in. If so get the user-ID, If not, use the IP as the User-id
            try:
                user_id = session["user_id"]
            except:
                user_id = socket.gethostbyname(socket.gethostname())
            a = 1
            cantri = str(request.form.get("cantri"))

            ## replance spaces with _underscore_ (used for coutries with 2 names like united_states)
            t_o = cantri.replace(" ", "_")

            ## the trip name is generated from the user_ID and the place he wants to visit
            ## There is a limitatoin to fix on V2 that user can't save 2 trips to the same place
            name = f"{user_id}id{t_o}"
            # print(name)
            tabs = {}
            d = 0
            visbol_prompt = ""
            try:
                ## Get the trip dates + description from the DB
                if db.execute("SELECT tabs FROM cantrise where id=? and cantrise=?", user_id, cantri)[0]['tabs']:
                    dates = str(db.execute("SELECT tabs FROM cantrise where id=? and cantrise=?", user_id, cantri)[0]['tabs'])
                    visbol_prompt = db.execute("SELECT visbol_prompt FROM cantrise where id=? and cantrise=?", user_id, cantri)[0]['visbol_prompt']
                    # print(dates)
                    ## Convert the list of dates to an array
                    dates = dates.replace(")", "").replace("(", "")
                    # print(dates)
                    dates = dates.split(",")
                    i = 0

                    for date in dates:
                        # worekd = 1
                        i = i+1
                        tabs[i] = date
                else:
                    ## At the beginning I used a different format to save the data into the DB
                    ## this is the olf method:
                    ## Now it is used to convert from the old way of saving to the new one
                    ## If I create a new DB, I can delete this section
                    for date in db.execute("SELECT date FROM ?", name):
                        date = date['date']
                        try:
                            if not date in tabs[d-1]:
                                worked = 1
                                # print(tabs)
                                tabs[d] = date
                                d = d + 1
                        except:
                            worked = 1
                            tabs[d] = date
                            # print(tabs)
                            d = d + 1
                    db.execute("UPDATE cantrise SET tabs = ? WHERE cantrise=?", ','.join(tabs.values()), cantri)
            except:
                return apology("", 403)

            # try:
            try:  # prints the trip plan on the screen with the user name
                return render_template("plan.html", response_content=db.execute("SELECT * FROM ?", name), tabs=tabs, loge=1, user_name=db.execute("SELECT username FROM users where id = ?", user_id)[0]["username"], csv=name, visbol_prompt=visbol_prompt)
            except:  # prints the trip plan on the screen without the user name
                return render_template("plan.html", response_content=db.execute("SELECT * FROM ?", name), tabs=tabs, loge=1, csv=name, visbol_prompt=visbol_prompt)
            # except:
            #    try:
             #       return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs,loge = 1,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"],csv=name)
              #  except:
               #     return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs,loge = 1,csv=name)

        # Create a new trip plan
        else:
            worked = 0
            # print("2")
            # From_wher = request.form.get("From")
            to = str(request.form.get("to"))  # the trip location
            dates = request.form.get("dates")  # 2 dates -  from which date till which date
            Adults = request.form.get("Adults")  # number of adults in the trip
            children_amount = request.form.get("children_amount")
            kids = request.form.get("kids")  # the ages of the kids
            # until = request.form.get("until")
            visbol_prompt = request.form.get("visbol_prompt")  # contain all the trip details above
            like = request.form.get("like")  # things the user usually likes to do
            Places = request.form.get("Places")  # places the user likes to visit

            ## Check if user is loged-in. If so get the user-ID, If not, use the IP as the User-id
            try:
                # print("3")
                user_id = session["user_id"]
                loge = 1
            except:
                # print("4")
                user_id = socket.gethostbyname(socket.gethostname())
                loge = 0

            ## replance spaces with _underscore_ (used for coutries with 2 names like united_states)
            t_o = to.replace(" ", "_")

            ## the trip name is generated from the user_ID and the place he wants to visit
            ## There is a limitatoin to fix on V2 that user can't save 2 trips to the same place
            name = f"{user_id}id{t_o}"
            db.execute("DROP TABLE IF EXISTS ? ", name)

            # Set the GPT prompt
            # The prompt tells GPT to create a trip plan according the data that the user gave
            # It also tells GPT to use a CSV format, and use |P| as the paragraph sepertor value. and |R| as the Raw end/seperator
            # Example: plan a trip with a 60 minutes breakdown, to NYC, for 3 adults and 2 kids, from 15.8 until 17.8 . Usually i like History. And I wouls like to see central park. The output should include (date, time, location and description) columns, and only those columns. The output should be in a CSV format, but instead of coma use '|P|' as the values separator, and also add '|R|' at the end of each line. The date format should be (month/day) and location should include (name/address) - in this order and nothing else. dont do greeting . Give me a full answer for all days from 9:00 till 22:00 PM.
            text = f"write in English ,plan a trip with a 60 minutes breakdown, to {to}, for {Adults} adults and for {children_amount} kids in age {kids} , from {dates} . Usually i like {like}. And I would like to see {Places}.The output must include 4 columns - (1) date, (2) time, (3) location and (4) description , and only those columns. The output should be in a CSV format, but instead of coma use '|P|' as the values separator, and also add '|R|' at the end of each line, and dont add 'enter' or '\n' at the end of the lines, and dont add headers at the first line. The date format should be (month/day) and location should include (name/address) - in this order and nothing else. dont do greeting . Give me a full answer for all days and every hour from 9:00 till 22:00 PM, dont stop at the middle of my trip. And dont worry about checking-in or checking-out from the hotel or going to or from the airport - I have full days there  from 9:00 AM till 22:00 PM."
            stream = client.chat.completions.create(messages=[{"role": "user", "content": text}], model="gpt-4o",)
            ##print(stream.choices[0].message)
            response_content = ""
            ##print(response_content)
            ##print("$")
            db.execute("CREATE TABLE IF NOT EXISTS ? (id INTEGER ,date string ,time string ,location string ,description string )", name)

            ## Takes ChatGPT response and renders it into a table
            ## print(response_content)
            i = 0
            # b = 0
            d = 0
            date = " "
            time = " "
            location = " "
            description = " "
            tabs = {}
            # print("--- ##printing message --- ")
            # print(stream.choices[0].message.content)
            # print("--- ##printed message --- ")
            # GPT answer is in stream.choices[0].message.content
            for response_content in stream.choices[0].message.content.split("|R|"):
                response_content = response_content.replace("\n", "")
                response_content = response_content.split("|P|")
                if len(response_content) == 4:
                    try:
                        date = response_content[0]
                        date = date.replace(" ", "")  # remove spaces in the date category for input consistency
                        time = response_content[1]
                        time = time.replace(" ", "")  # remove spaces in the date category for input consistency
                        location = response_content[2]
                        description = response_content[3]
                        i = i + 1

                        # takes the data from date, and set into an array with a slot per date
                        try:
                            if not date in tabs[d-1]:
                                worked = 1
                                # print(tabs)
                                tabs[d] = date
                                d = d + 1
                        except:
                            worked = 1
                            # print(tabs)
                            tabs[d] = date
                            d = d + 1
                        db.execute("INSERT INTO ? (id,date ,time ,location ,description) VALUES (?,? ,? ,? ,?)", name, i, date, time, location, description)
                        time = " "
                        location = " "
                        description = " "
                        date = ""
                    except:
                        try:
                            if worked == 1:  # if worked=1 so tabs[] includes data from ChatGPT, otherwise the API woth ChatGPT didnt work

                                try:  # Checks if the user is loged-in
                                    if user_id == session["user_id"]:
                                        # print("1")
                                        if db.execute("SELECT * FROM cantrise where id=? and cantrise=? ",user_id,to):   ## Checks if the user already planned a trip to this location, and if so, delete it (on V2 I will support multiple trips to the same place)
                                            # print("2")
                                            db.execute("DELETE FROM cantrise WHERE id=? AND cantrise=?)", user_id, to)

                                        ## add this trip to the DB
                                        db.execute("INSERT INTO cantrise (id,cantrise,tabs,visbol_prompt) VALUES (?,?,?,?)",user_id, to, ','.join(tabs.values()), visbol_prompt)

                                    # prints the planned-trip on the screen
                                    return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs, loge=loge, csv=name, visbol_prompt=visbol_prompt)
                                except: #The user havn't loged-in,
                                    # prints the planned-trip on the screen
                                    return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs,loge=loge,csv=name,visbol_prompt=visbol_prompt)

                            else: # We didnt get a valid response from GPT (due to any issue)
                                try:
                                    return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,like=like,Places=Places,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"])
                                except:
                                    try:
                                        return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,like=like,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"])
                                    except:
                                        return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"])

                        except:
                            if worked == 1:  # got a valid response from GPT
                                #print("in worked")
                                return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs,loge=loge,csv=name,visbol_prompt=visbol_prompt,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"])
                            else: # didnt get a valid response from GPT
                                #print("not in worked")
                                try:
                                    return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,like=like,Places=Places)
                                except:
                                    try:
                                        return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,like=like)
                                    except:
                                        return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids)
        if worked == 1:  # got a valid response from GPT
            if socket.gethostbyname(socket.gethostname()) != user_id:
                # print("1")
                if db.execute("SELECT * FROM cantrise where id=? and cantrise=? ",user_id,to):
                    db.execute("DELETE FROM cantrise where id=? and cantrise=? ",user_id,to)
                db.execute("INSERT INTO cantrise (id,cantrise,tabs,visbol_prompt) VALUES (?,?,?,?)",user_id,to,','.join(tabs.values()),visbol_prompt)
            try: # prints the trip plan on the screen with the user name
                #print("in worked")
                return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs,loge=loge,csv=name,visbol_prompt=visbol_prompt,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"])
            except: # prints the trip plan on the screen without the user name
                #print("in worked")
                return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs,loge=loge,csv=name,visbol_prompt=visbol_prompt)

    else:  # if we are here, the request method is not "POST"
        try:
            user_id = session["user_id"]
        except:
            user_id=socket.gethostbyname(socket.gethostname())
        try:
            cantrise=db.execute("SELECT cantrise FROM cantrise where id=?",user_id) ## gets all existing planned-trips of this user
            user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"] # get the name of the user

        except: # user has no trips that are already planed
           cantrise = {}
           cantrise[0] = " "
        try:
            return render_template("index.html",cantrise=cantrise ,user_name=user_name) # runs the home page
        except:
            return render_template("index.html",cantrise=cantrise) # runs the home page without the user name becayse the user is not logged-in



@app.route("/save", methods=["GET", "POST"])
def save():  # saves the planned trip in the DB for unknown users who didnt logged-in
    try:
        user_id = session["user_id"]
    except:
        user_id=socket.gethostbyname(socket.gethostname())
    return render_template("login.html",name=request.form.get("save"),visbol_prompt=request.form.get("visbol_prompt"))  # Sends the user to the login code with the trip data so we can save it later


#@app.route("/open_home", methods=["GET", "POST"])
#def open_home():
#    if request.method == "POST":
#        return redirect("/")
#    else:
#        return redirect("/")

@app.route("/costomise", methods=["GET", "POST"])
def costomise(): ## After the inital trip-plan, the user can customize the trip to better fit him
    if request.method == "POST":
        try:
            user_id = session["user_id"]
            loge=1
        except:
            user_id=socket.gethostbyname(socket.gethostname())
            loge=0
        costomise = request.form.get("costomise")  # Holds all the changes that the use done to the suggesed trip (the 4 change options - like, pass, more, less )
        name = request.form.get("csv") # holds the name of the trip-plan
        #print(name)
        csv=db.execute("SELECT * FROM ?",name) # a 2 dimentional array (table) that holds all the trip , loaded from the DB
        csv_s="" # contains the table in a string format, GPT works with strings
        i = 0
        end =0
        for row in csv: # reads the table, row by row, to convert it to a string
            csv_s= csv_s + f"{row['date']}|P|{row['time']}|P|{row['location']}|P|{row['description']}|R|"
            i = i+1
            ##print(csv_s)
            ##print(b)
        #print(csv_s)
        db.execute("DROP TABLE IF EXISTS ? ",name) # deleting the previouse table so we can add the new trip-plan data to the table
        #print(costomise)
        db.execute("CREATE TABLE IF NOT EXISTS ? (id INTEGER ,date string ,time string ,location string ,description string )",name) # create the table again to hold the customized trip
        text = f"({csv_s}) . This is the trip that you created for me in a csv format. Its good , but please halp me to customize it by doing those changes - {costomise}. Make it in the same format: write in English ,plan a trip with a 60 minutes breakdown .The output must include 4 columes - (1) date, (2) time, (3) location and (4) description , and only those columns. The output should be in a CSV format, but instead of coma use '|P|' as the values separator, and also add '|R|' at the end of each line, and dont add 'enter' or '\n' at the end of the lines, and dont add headers at the first line. The date format should be (month/day) and location should include (name/address) - in this order and nothing else. dont do greeting . Give me a full answer for all days and every hour from 9:00 till 22:00 PM, dont stop at the middle of my trip. And dont worry about checking-in or checking-out from the hotel or going to or from the airport - I have full days there  from 9:00 AM till 22:00 PM."
        # text holds the prompt that is sent to GPT
        stream = client.chat.completions.create(messages=[{"role": "user","content": text}],model="gpt-4o",)  # sends the prompt to GPT and hold the response in STREAM parameter
        #response_content = ""

        # create the variables to send to GPT
        i = 0
        d=1
        date = " "
        time = " "
        location = " "
        description = " "
        tabs = {}
        # gpt_output = ""
        tabs[0] = date

        # sends the prompt to GPT and get the answer into response_content
        for response_content in stream.choices[0].message.content.split("|R|"):  # every location that GPT put |R| is a new Row in the array
                #  gpt_output = gpt_output + response_content
                response_content = response_content.replace("\n", "") #remove all \n to avoice new line in the output table
                response_content = response_content.split("|P|") # every location that GPT put |P| is a new cell in the array (P stands for Parts in the output)
                if len(response_content) == 4: # verify that the row is splitted into 4 cells
                    try:
                                date = response_content[0] #first cell is the date
                                date = date.replace(" ", "") # remove spaces
                                time = response_content[1] # 2nd cell is the time
                                time = time.replace(" ", "") # remove spaces
                                location = response_content[2] #3rd cell is the locaiton
                                description = response_content[3] #4th cell in the description
                                i = i + 1
                                try:
                                    if not date in tabs[d-1]: # tabs holds a list of all the trip days, date is the specific date, checking if we are still in the same day or its a new one
                                        worked=1
                                        #print(tabs)
                                        tabs[d] = date # add a new day to tab
                                        d = d + 1
                                except: # we are in the 1st day of the trip, so d-1 is "-1" -> we need to have the 1st date in slot 0 in the tabs array
                                    worked=1
                                    #print(tabs)
                                    tabs[d] = date
                                    d = d + 1


                                # add the line from GPT into the DB
                                db.execute("INSERT INTO ? (id,date ,time ,location ,description) VALUES (?,? ,? ,? ,?)",name,i,date,time ,location ,description)

                                # reset the parameters for the next row
                                time = " "
                                location = " "
                                description = " "
                                date = ""


                    except:   # we are after the last row of the GPT output
                                    if worked == 1:  # we got all data from GPT - all OK
                                        #print("in worked")
                                        if socket.gethostbyname(socket.gethostname()) != user_id: # the user is logedin
                                            #print("1")
                                            if not db.execute("SELECT * FROM cantrise where id=? and cantrise=? ",user_id,to): # this is your fiest trip plan for this country
                                                #print("2")
                                                db.execute("INSERT INTO cantrise (id,cantrise,tabs,visbol_prompt) VALUES (?,?,?,?)",user_id,to,','.join(tabs.values()),visbol_prompt) # add the trip plan to the DB
                                        try: # prints the trip plan on the screen with the user name
                                            return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs,loge=loge,csv=name,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"])
                                        except: # prints the trip plan on the screen without the user name
                                            return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs,loge=loge,csv=name)
                                    else: # we didnt get all data from GPT -> run Customize again
                                      return render_template("Loading.html",costomise=costomise,csv=name,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"])
        #print(stream.choices[0].message.content)
        try: # prints the trip plan on the screen with the user name
            return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs,loge=loge,csv=name,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"])
        except: # prints the trip plan on the screen without the user name
            return render_template("plan.html", response_content=db.execute("SELECT * FROM ?",name), tabs=tabs,loge=loge,csv=name)
    else:
        return redirect("/")

@app.route("/login_register", methods=["GET", "POST"])
def login_register():  # switch the UI from login to register and from register to login
    if request.form.get("type") == "register":  # from the login screen to the register screen
        try: # prints the trip plan on the screen with the user name
            return render_template("register.html",name=request.form.get("save"),visbol_prompt=request.form.get("visbol_prompt"),user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"])
        except: # prints the trip plan on the screen without the user name
            return render_template("register.html",name=request.form.get("save"),visbol_prompt=request.form.get("visbol_prompt"))
    if request.form.get("type") == "login": # from the register screen to the login screen
        try: # prints the trip plan on the screen with the user name
            return render_template("login.html",name=request.form.get("save"),visbol_prompt=request.form.get("visbol_prompt"),user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"])
        except: # prints the trip plan on the screen without the user name
            return render_template("login.html",name=request.form.get("save"),visbol_prompt=request.form.get("visbol_prompt"))

#sorry for my typo-s, I have dyslexia, I am 16 years old, and English is my second language (lode = load)
# I dont fix it as it might be riscky to do such a change
#
# Lode or Load creates a nice icon on the screen while the porgram interacts with Chat-GPT in the background
@app.route("/lode", methods=["GET", "POST"])
def lode():  #lode = load...
    if request.form.get("index"):  # lode was called from the index part (and not from the customize part)
        #print("1")
        try:
            user_id = session["user_id"]
            loge=1
        except:
            user_id=socket.gethostbyname(socket.gethostname())
            loge=0
        to = request.form.get("to").upper().replace(",", "") # get the trip destination and covert it to upper case
        dates = request.form.get("dates") # whats the dates of the trip
        Adults = request.form.get("Adults") #how many adults in this trip
        children_amount = int(request.form.get("children_amount")) #how many children in this trip
        visbol_prompt = f"A trip to {to} for {Adults} adults" # the high level trip details
        kids ="" # contains the children ages
        if children_amount:
            ###print(f"{kids=}")
            for i in range(children_amount):
                ###print(f"{i=}")
                kidAge=f"kidAge{i+1}"
                ###print(f"{str(request.form.get(kidAge))=}")
                ###print(f"{kidAge=}")
                ###print(f"{kids=}")
                if kids == "":
                    kids=str(request.form.get(kidAge))
                else:
                    kids = kids + "," + str(request.form.get(kidAge)) # add ages of the children
            visbol_prompt = visbol_prompt + f"and {children_amount} kids in age {kids} "# adding the kids ages to the high level trip details
        visbol_prompt = visbol_prompt+f" , from {dates}" # adding the trip dates to the high level trip details

        like = request.form.get("like") #contains things that the user usually likes to do, used as an example for CHAT-GPT when planning the trip
        if like:
            visbol_prompt = visbol_prompt + f" Usually i like {like}" # adding the things that the user likes to do to the high level trip details

        Places = request.form.get("Places") #contains places that the user would like to see in this trip, CHAT-GPT will use it toplan the trip accordingly
        if Places:
            visbol_prompt = visbol_prompt + f" And I would like to see {Places}" # adding the places that the user want to visit to the high level trip details
        try: # prints the trip plan on the screen with the user name
            try:
                return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,like=like,Places=Places,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"],index="index")
            except:
                try:
                    return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,like=like,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"],index="index")
                except:
                    return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,user_name=db.execute("SELECT username FROM users where id = ?",user_id)[0]["username"],index="index")

        except: # prints the trip plan on the screen without the user name
            try:
                return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,like=like,Places=Places,index="index")
            except:
                try:
                    return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,like=like,index="index")
                except:
                    return render_template("Loading.html",children_amount=children_amount,visbol_prompt=visbol_prompt,to=to,Adults=Adults,dates=dates,kids=kids,index="index")
    else:  # Lode was called from customize (and not from Index)
        #print("2")
        try:
            user_id = session["user_id"]
            loge=1
        except:
            user_id=socket.gethostbyname(socket.gethostname())
            loge=0
        name = request.form.get("name") #the name of this trip
        csv=db.execute("SELECT * FROM ?",name) # load the trip details from the DB to an array called CSV
        locations = {}  # a list of all places that were recommanded for this trip (each location is a line in the CSV/Table)
        i = 0
        for row in csv:  # for each row in the CSV (or line in the DB table), find the location and add it to the array
            locations[i] = row['location']
            i = i+1
        #print(locations)

        costomise = ""
        for line in range(i):  # run over all the lines in the table and collect the customization requests
            do = f"do_{line + 1}" # holds user's feedback if the user liked this activity (in this line of the table) , or asked to pass it
            #time=f"time_{line + 1}" # holds user's feedback if the user likes to spend more or less time in this activity (in this line of the table)
            #print(f"{line=} ,{request.form.get(do)=} ,{request.form.get(time)=} ,{locations[line]=}")
            # if request.form.get(time): # checks if the user asked to modify the plan by spending more or less time on any activity
            # if request.form.get(time) == "more":
            # costomise = costomise + f" I want more time in {locations[line]}. "  #customize the GPT prompt to spend more time in an activity
            # elif request.form.get(time) == "less":
            # costomise = costomise + f" I want less time in {locations[line]}. " #customize the GPT prompt to spend less time in an activity
            if request.form.get(do): #checks if the user asked to modify the plan by like specific activities or asked to remove activities
                if request.form.get(do) == "pass":
                    costomise = costomise + f" I want to pass {locations[line]}. " #customize the GPT prompt not to include a spicific activity/ies
                elif request.form.get(do) == "like":
                        costomise = costomise + f"i want more activities like {locations[line]}. "  #customize the GPT prompt to do more activities like the one(s) that the user likes
        return render_template("Loading.html", costomise=costomise, csv=name)
