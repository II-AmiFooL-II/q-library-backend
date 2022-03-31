from operator import ilshift
from flask import Flask,jsonify,request,Response
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson.json_util import loads
from datetime import datetime

app = Flask(__name__)
app.config["MONGO_URI"] = 'mongodb+srv://zupay_demo:EOwEaDgWWxFYJeeo@cluster.pubwu.mongodb.net/library?retryWrites=true&w=majority'
try:
    print("hello")
    mongo = PyMongo(app)
    print(mongo)

except Exception as e:
    print(e)

@app.route('/')
def hello_world():
    return 'Hello World'


@app.route("/add_many")
def add_many():
    books_data = [
                {'book name': "one", 'category': "one",'rent per day': 1},
                {'book name': "two", 'category': "two",'rent per day': 2},
                {'book name': "three", 'category': "three",'rent per day': 3},
                {'book name': "four", 'category': "four",'rent per day': 4},
                {'book name': "five", 'category': "one",'rent per day': 5},
                {'book name': "six", 'category': "two",'rent per day': 1},
                {'book name': "seven", 'category': "one",'rent per day': 1},
                {'book name': "eight", 'category': "two",'rent per day': 2},
                {'book name': "nine", 'category': "three",'rent per day': 3},
                {'book name': "ten", 'category': "four",'rent per day': 4},
                {'book name': "eleven", 'category': "one",'rent per day': 5},
                {'book name': "twelve", 'category': "two",'rent per day': 1},
                {'book name': "thirteen", 'category': "one",'rent per day': 1},
                {'book name': "fourteen", 'category': "two",'rent per day': 2},
                {'book name': "fifteen", 'category': "three",'rent per day': 3},
                {'book name': "sixteen", 'category': "four",'rent per day': 4},
                {'book name': "seventeen", 'category': "one",'rent per day': 5},
                {'book name': "eighteen", 'category': "two",'rent per day': 1},
                {'book name': "ninteen", 'category': "one",'rent per day': 5},
                {'book name': "twenty", 'category': "two",'rent per day': 1},
            ]
    print(books_data)
    mongo.db.books.insert_many(books_data)
    return jsonify(message="success")


@app.route("/findbook",methods=['GET'])
def find_book():
    print(request.args)
    if "book name" in request.args:
        if "category" in request.args:
            if not 'low' in request.args and not 'high' in request.args:
                return Response(
                    "Not enough parmeters",
                    status=400,
                )    
            cursor = mongo.db.books.find({"book name":{'$regex':request.args['book name']},'category':request.args['category'],'rent per day':{ '$gt':int(request.args['low']), '$lt':int(request.args['high'])}})
        else:
            if not 'book name' in request.args:
                return Response(
                    "Not enough parmeters",
                    status=400,
                )    
            cursor = mongo.db.books.find({"book name":{'$regex':request.args['book name']}})
    else:
        if not 'low' in request.args and not 'high' in request.args:
            return Response(
                "Not enough parmeters",
                status=400,
            )
        print(request.args['low'])
        cursor = mongo.db.books.find({'rent per day':{ '$gt':int(request.args['low']), '$lt':int(request.args['high'])}})

    print(cursor)
    return dumps(cursor)

@app.route("/issue_book",methods=['POST'])
def issue_book():
    #print(dir(request))
    print(request.json)
    if not 'book name' in request.json and not 'person name' in request.json and not "issue date" in request.json:
        return Response(
            "Not enough parmeters",
            status=400,
        )

    try:
        new_date = datetime.fromisoformat(request.json["issue date"])
    except ValueError:
        return Response(
            "improper date format",
            status=400,
        )

    trans = {
        'book name': request.json["book name"],
        'person name': request.json['person name'],
        'issue date': new_date,
    }
    print(trans)
    mongo.db.transaction.insert_one(trans)
    return jsonify(message="success")

@app.route("/return_book",methods=['POST'])
def return_book():
    if not 'book name' in request.json and not 'person name' in request.json and not "return date" in request.json:
        return Response(
            "Not enough parmeters",
            status=400,
        )
    try:
        new_date = datetime.fromisoformat(request.json["return date"])
    except ValueError:
        return Response(
            "improper date format",
            status=400,
        )

    trans = mongo.db.transaction.find_one({'book name':request.json["book name"],'person name':request.json["person name"]})
    if trans == None:
        return Response(
            "no record found",
            status=400,
        )
    delta = datetime.fromisoformat(request.json["return date"]) - trans['issue date']
    book_cost = mongo.db.books.find_one({"book name":request.json["book name"]})
    total_cost = delta.days*book_cost['rent per day']
    mongo.db.transaction.update_one(trans,{"$set":{'return_book':new_date,'rent':total_cost}},upsert=True)
    return jsonify(message="success")

@app.route("/total_list_current_issue",methods=["GET"])
def total_list_current_issue():
    if not "book name" in request.args:
        return Response(
            "Not enough parmeters",
            status=400,
        )
  
    trans = mongo.db.transaction.find({'book name':request.args["book name"]})
    count = 0
    current_issue = []
    for i in trans:
        if "return_book" in i:
            count+=1
        else:
            current_issue.append(i["person name"])
    return jsonify(total_no_of_ppl_issued=count,currently_issued=current_issue)

@app.route("/total_rent",methods=["GET"])
def total_rent():
    if not "book name" in request.args:
        return Response(
            "Not enough parmeters",
            status=400,
        )  

    trans = mongo.db.transaction.find({'book name':request.args["book name"]})
    total_rent = 0
    for i in trans:
        if 'rent' in i:
            total_rent += i['rent']
    print(total_rent)
    return jsonify(message="success",rent=total_rent)

@app.route("/list_books_taken",methods=["GET"])
def list_books_taken():
    if not "person name" in request.args:
        return Response(
            "Not enough parmeters",
            status=400,
        )  

    trans = mongo.db.transaction.find({'person name':request.args["person name"]})
    books_issued = []
    for i in trans:
        books_issued.append(i['book name'])
    return jsonify(books_issued_to_person=books_issued)

@app.route("/books_issued_bydate",methods=["GET"])
def books_issued_bydate():
    if not "end_date" in request.args and not "start_date" in request.args:
        return Response(
        "Not enough parmeters",
        status=400,
    )
    try:
        end_date = datetime.fromisoformat(request.args["end_date"])
    except ValueError:
        return Response(
            "improper date format",
            status=400,
        )

    try:
        start_date = datetime.fromisoformat(request.args["start_date"])
    except ValueError:
        return Response(
            "improper date format",
            status=400,
        )

    trans = mongo.db.transaction.find({'issue date':{'$gte':start_date,'$lte':end_date }})
    list_books = []
    for i in trans:
        list_books.append({'book name':i['book name'],
                            'issued person':i['person name']})
    return jsonify(all_books_issued=list_books)
    