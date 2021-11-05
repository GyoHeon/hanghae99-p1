from pymongo import MongoClient
import pymongo
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

#client = MongoClient('localhost', 27017)
client = MongoClient('15.165.158.230', 27017, username="test", password="test")
#client = MongoClient('mongodb://test:test@localhost', 27017)
db = client.dbproject1


# 메인페이지-챌린지 정보 주기__이교헌
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        challenges = db.chall.find({}, {"_id": False}).sort('participate', -1)
        return render_template('index.html', user_info=user_info, challenges=challenges)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


# 로그인 - 이교헌
@app.route('/sign_in', methods=['POST'])
def sign_in():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})
    print(result)
    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60)  # 로그인 1시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# 회원가입 - 이교헌
@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,  # 프로필 이름 기본값은 아이디
        "profile_pic": "",  # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png",  # 프로필 사진 기본 이미지
        "profile_info": "",  # 프로필 한 마디
        "profile_chall": []  # 참가한 챌린지
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


# 중복확인 - 이교헌
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


# 상세페이지이동 - 이한울  2021/11/04
@app.route('/detail/<title_give>/')
def detail(title_give):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username":payload["id"]})
        username = user_info["username"]             #상세페이지에서 마이프로필 가기위한 username
        profile_chall = user_info["profile_chall"]
        challenge = db.chall.find_one({"title": title_give}, {"_id": False})
        participate = challenge["participate"]
        img = challenge["url"]
        desc = challenge["description"]
        comments = db.comment.find({"title":title_give}).sort("date", -1)

        return render_template('detail.html',title=title_give, img=img, desc=desc,username=username,participate=participate, profile_chall=profile_chall, comments=comments)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 상세페이지 참가 db에 저장 - 이한울
@app.route('/my_chall', methods=['POST'])
def my_chall():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        profile_chall_receive = request.form["profile_chall_give"]
        participate = db.chall.find_one({"title":profile_chall_receive})["participate"]
        db.chall.update_one({'title':profile_chall_receive}, {'$inc':{'participate' : 1}})
        db.users.update_one({'username':user_info["username"]},{'$push':{'profile_chall':profile_chall_receive}})
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 마이페이지 렌더링 코드 - 이한울 2021/11/04
# 참가한 챌린지 목록 끌고 오기
@app.route('/myPage/<username>')
def main(username):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False
        user_info = db.users.find_one({"username": username}, {"_id": False})
        user_challenges_title = user_info["profile_chall"]
        user_challenges = db.chall.find({'title':{'$in':user_challenges_title}}).sort("participate", -1)
        num_comment = db.comment.find({'title':{'$in':user_challenges_title}, 'username':username})
        return render_template('myPage.html', user_info=user_info, status=status, user_challenges=user_challenges, num_comment=num_comment)

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))
      
      
if __name__ == '__main__':
    app.run('0.0.0.0', port=8000, debug=True)