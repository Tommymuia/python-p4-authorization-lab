from flask import Flask, request, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_cors import CORS

# Import models
from models import db, User, Article

app = Flask(__name__)
app.secret_key = b'\x15\x16\x1a\xde\x94\x97\xda\x7f\xc0\xc1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

CORS(app)
migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

# --- AUTHENTICATION RESOURCES ---

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        user = User.query.filter(User.username == username).first()
        
        if user:
            session['user_id'] = user.id
            return make_response(user.to_dict(), 200)
        
        return make_response({'error': 'Unauthorized'}, 401)

class Logout(Resource):
    def delete(self):
        session['user_id'] = None
        return make_response({}, 204)

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            if user:
                return make_response(user.to_dict(), 200)
        return make_response({}, 401)

# --- MEMBERS ONLY RESOURCES ---

class MemberOnlyIndex(Resource):
    def get(self):
        # 1. Check if user is signed in
        user_id = session.get('user_id')
        if not user_id:
            return make_response({"error": "Unauthorized"}, 401)
        
        # 2. Return JSON data for members-only articles
        articles = Article.query.filter(Article.is_member_only == True).all()
        return make_response([a.to_dict() for a in articles], 200)

class MemberOnlyArticle(Resource):
    def get(self, id):
        # 1. Check if user is signed in
        user_id = session.get('user_id')
        if not user_id:
            return make_response({"error": "Unauthorized"}, 401)
        
        # 2. Return JSON data for the specific members-only article
        article = Article.query.filter(Article.id == id, Article.is_member_only == True).first()
        
        if article:
            return make_response(article.to_dict(), 200)
        
        return make_response({"error": "Article not found"}, 404)

# --- ROUTE REGISTRATION ---

api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')

# Updated these paths to plural "members_only_articles" per pytest log
api.add_resource(MemberOnlyIndex, '/members_only_articles')
api.add_resource(MemberOnlyArticle, '/members_only_articles/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)