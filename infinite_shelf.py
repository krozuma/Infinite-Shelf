from sqlalchemy import asc
from flask import Flask, render_template, url_for, request, flash, redirect, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Genre, Books
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import os
from flask import make_response
import requests

app = Flask(__name__)
app.secret_key = 'super_secret_key'

CLIENT_ID = json.loads(
    open('/var/www/infiniteShelf/infinite_shelf/client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Infinite Shelf"


engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# validating current loggedin user

def check_user():
    email = login_session['email']
    return session.query(User).filter_by(email=email).one_or_none()


@app.route('/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    #return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/')
@app.route('/genres')
def showGenres():
    genres = session.query(Genre).order_by(Genre.name.asc()).all()
    return render_template('genres.html', genres=genres)

    if 'username' not in login_session:
        return render_template('publicgenres.html', genres=genres)
    else:
        return render_template('genres.html', genres=genres)


@app.route('/genres/new', methods=['GET', 'POST'])
def newGenre():
    if 'username' not in login_session:
        return(redirect('/login'))
    if request.method == 'POST':
        newGenre = Genre(name=request.form['name'])
        session.add(newGenre)
        session.commit()
        flash("New genre created!")
        return(redirect(url_for('showGenres')))
    else:
        return(render_template('newgenre.html'))


@app.route('/genres/<int:genre_id>/edit', methods=['GET', 'POST'])
def editGenre(genre_id):
    if 'username' not in login_session:
        return(redirect('/login'))
    editedGenre = session.query(Genre).filter_by(id=genre_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedGenre.name = request.form['name']
        session.add(editedGenre)
        session.commit()
        flash("Genre has been edited.")
        return(redirect(url_for('showGenres')))
    else:
        return(render_template('editgenre.html', genre_id=genre_id, editedGenre=editedGenre))


@app.route('/genres/<int:genre_id>/delete', methods=['GET', 'POST'])
def deleteGenre(genre_id):
    if 'username' not in login_session:
        return(redirect('/login'))
    genreToDelete = session.query(Genre).filter_by(id=genre_id).one()
    if request.method == 'POST':
        if book.user.user_id == user_id:
            session.delete(genreToDelete)
            session.commit()
            flash("Genre has been deleted.")
            return redirect(url_for('showGenres'))
        else: flash("You're not authorized to edit another user's post.")    
    else:
        return render_template('deletegenre.html', genreToDelete=genreToDelete, genre_id=genre_id)


@app.route('/genres/<int:genre_id>')
@app.route('/genres/<int:genre_id>/books')
def showBooks(genre_id):
    genre = session.query(Genre).filter_by(id=genre_id).one()
    items = session.query(Books).filter_by(genre_id=genre_id).order_by(Books.name.asc())
    if 'username' not in login_session:
        return render_template('publicbooks.html', genre=genre, items=items, genre_id=genre_id)
    else:
        return render_template('books.html', genre=genre, items=items, genre_id=genre_id)


@app.route('/genres/<int:books_id>')
@app.route('/genres/<int:books_id>/book')
def showBook(books_id):
    selected_book = session.query(Books).filter_by(id=books_id).one()
    if 'username' not in login_session:
        return render_template('publicshowbook.html', books_id=books_id, selected_book=selected_book)
    else:
        return render_template('showbook.html', books_id=books_id, selected_book=selected_book)


@app.route('/genres/<int:genre_id>/books/new', methods=['GET', 'POST'])
def newBook(genre_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Books(name=request.form['name'], author=request.form['author'],
                        description=request.form['description'], price=request.form['price'],
                        rating=request.form['rating'], genre_id=genre_id)
        session.add(newItem)
        session.commit()
        flash("New book added!")
        return(redirect(url_for('showBooks', genre_id=genre_id)))
    else:
        return render_template('newbook.html', genre_id=genre_id)


@app.route('/genres/<int:genre_id>/<int:books_id>/edit', methods=['GET', 'POST'])
def editBook(genre_id, books_id):
    if 'username' not in login_session:
        return(redirect('/login'))
    editedItem = session.query(Books).filter_by(id=books_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['author']:
            editedItem.author = request.form['author']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['rating']:
            editedItem.rating = request.form['rating']
        session.add(editedItem)
        session.commit()
        flash("Book listing has been edited.")
        return(redirect(url_for('showBooks', genre_id=genre_id)))
    else:

        return(render_template('editbook.html', genre_id=genre_id, books_id=books_id, item=editedItem))


@app.route('/genres/<int:genre_id>/<int:books_id>/delete', methods=['GET', 'POST'])
def deleteBook(genre_id, books_id):
    if 'username' not in login_session:
        return(redirect('/login'))
    itemToDelete = session.query(Books).filter_by(id=books_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Book listing has been deleted.")
        return(redirect(url_for('showBooks', genre_id=genre_id)))
    else:
        return(render_template('deletebook.html', item=itemToDelete, genre_id=genre_id))



@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/infiniteShelf/infinite_shelf/client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;' \
              '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showGenres'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showGenres'))


@app.route('/genres/JSON', methods=['GET'])
def genresGetJSON():
    getGenres = session.query(Genre).order_by(Genre.name.asc()).all()
    return jsonify(Genre=[i.list for i in getGenres])


@app.route('/genres/<int:genre_id>/books/JSON', methods=['GET'])
def getBooksJSON(genre_id):
    bookList = session.query(Books).filter_by(genre_id=genre_id).all()
    return jsonify(BookList=[i.serialize for i in bookList])


if __name__ == '__main__':
    app.run()
