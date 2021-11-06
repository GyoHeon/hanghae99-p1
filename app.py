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

# 암호화 키
SECRET_KEY = 'SPARTA'

client = MongoClient('15.165.158.230', 27017, username="test", password="test")
db = client.dbproject1


# 메인페이지-챌린지 정보 주기__이교헌
@app.route('/')
def home():
    # 로그인 정보 토큰 가져옴
    token_receive = request.cookies.get('mytoken')
    try:
        # 토큰 디코드
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 토큰 id와 일치하는 정보
        user_info = db.users.find_one({"username": payload["id"]})
        # 참여인원 수 내림차순으로 설정된 챌린지 목록
        challenges = db.chall.find({}, {"_id": False}).sort('participate', -1)
        return render_template('index.html', user_info=user_info, challenges=challenges)
    # 로그인 안되는 경우
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


# 로그인 - 이교헌
@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 아이디 입력값
    username_receive = request.form['username_give']
    # 비밀번호 입력값
    password_receive = request.form['password_give']
    # 비밀번호 입력값 암호화함
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    # id,pw 맞는 데이터 탐색
    result = db.users.find_one({'username': username_receive, 'password': password_hash})
    # 만약 맞는 데이터가 있으면 로그인
    if result is not None:
        payload = {
            'id': username_receive,
            # 로그인 1시간 유지
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token})
    # 맞는 데이터가 없으면 경고문 출력
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# 회원가입 - 이교헌
@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    # 아이디 입력값
    username_receive = request.form['username_give']
    # 비밀번호 입력값
    password_receive = request.form['password_give']
    # 비밀번호 입력값 암호화함
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    # 아이디, 비밀번호, 프로필 이름, 프로필 사진, 프로필 한마디, 참가한 챌린지(어레이) 저장
    doc = {
        "username": username_receive,  
        "password": password_hash,  
        "profile_name": username_receive,
        "profile_pic": "",
        "profile_pic_real": "profile_pics/profile_placeholder.png",
        "profile_info": "",
        "profile_chall": []
    }
    # DB에 저장
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
        users = db.users.find({})
        user_info = db.users.find_one({"username":payload["id"]})
        username = user_info["username"]             #상세페이지에서 마이프로필 가기위한 username
        profile_chall = user_info["profile_chall"]
        challenge = db.chall.find_one({"title": title_give}, {"_id": False})
        participate = challenge["participate"]
        img = challenge["url"]
        desc = challenge["description"]
        comments = db.comment.find({"title":title_give}).sort("date", -1)
        return render_template('detail.html',title=title_give, img=img, desc=desc,comments=comments,username=username,participate=participate, profile_chall=profile_chall, users=users)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 상세페이지 내용 db에저장 참가하기  2021/11/04
# 상세페이지 인증글 db에 저장-이한울
@app.route('/posting', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        # 로그인된 jwt 토큰을 디코드하여 payload에 설정한다.#
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 로그인 정보를 토대로 user_info설정한다.#
        user_info = db.users.find_one({"username": payload["id"]})
        # title_give로 가져온 값을 가져오면 그게 title_receive가 된다.#
        title_receive=request.form["title_give"]
        # comment_give로 가져온 값을 가져오면 그게 commnet_receive가 된다.#
        comment_receive = request.form["comment_give"]
        # date_give로 가져온 값을 가져오면 그게 data_receive가 된다.#
        date_receive = request.form["date_give"]
        # 아이디,프로필 닉네임, 프로필사진, 코멘트,날짜, 참가한 챌린지 저장
        doc = {
            "username": user_info["username"],
            "profile_name": user_info["profile_name"],
            "profile_pic_real": user_info["profile_pic_real"],
            "comment": comment_receive,
            "date": date_receive,
            "title": title_receive
        }
        db.comment.insert_one(doc)                       #2중배열 인증글 db 입력

    # 성공시 포스팅성공 출력
        return jsonify({"result": "success", 'msg': '포스팅 성공'})

    #실패시 home으로 이동.
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 상세페이지 참가 db에 저장 - 이한울
@app.route('/my_chall', methods=['POST'])
def my_chall():
    token_receive = request.cookies.get('mytoken')
    try:
        #로그인된 jwt 토큰을 디코드하여 payload에 설정한다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        #로그인 정보를 토대로 user_info을 설정한다.
        user_info = db.users.find_one({"username": payload["id"]})
        #Profile_cahll_give로 가져온값을 가져오면 그게 profile_chall_receive가 된다.
        profile_chall_receive = request.form["profile_chall_give"]
        #해당하는 chall에 particiapte를 표현한다.
        participate = db.chall.find_one({"title":profile_chall_receive})["participate"]
        #title로 데이터로 찾은 후 particiapte의 데이터에 +1을 추가한다.
        db.chall.update_one({'title':profile_chall_receive}, {'$inc':{'participate' : 1}})
        #유저네임을 데이터로 찾은 후 profile_chall을 추가한다.
        db.users.update_one({'username':user_info["username"]},{'$push':{'profile_chall':profile_chall_receive}})
        #성공시 포스팅 성공 출력
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
        #실패시 home으로 이동
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 마이페이지 렌더링 코드 - 이한울 2021/11/04, 이교헌 2021/11/05
# 참가한 챌린지 목록 끌고 오기, 코멘트 넘겨서 성취도 확인
@app.route('/myPage/<username>')
def main(username):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 내 프로필이면 True, 다른 사람 프로필 페이지면 False
        status = (username == payload["id"])
        # 해당 유저 DB.
        user_info = db.users.find_one({"username": username}, {"_id": False})
        # 해당 유저가 참가한 챌린지한 title 정보
        user_challenges_title = user_info["profile_chall"]
        # 해당 유저가 참가한 챌린지를 참가인원이 많은 순으로 내려 받기.
        user_challenges = db.chall.find({'title':{'$in':user_challenges_title}}).sort("participate", -1)
        # 해당 유저가 참가한 챌린지 인증글 횟수 내려받기.
        num_comment = db.comment.find({'title':{'$in':user_challenges_title}, 'username':username})
        #myPage로 정보전달
        return render_template('myPage.html', user_info=user_info, status=status, user_challenges=user_challenges, num_comment=num_comment)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


#마이프로필 변경 -사진.소개.닉네임 -이한울 2021/11/05
@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload["id"]
        # 유저 이름
        name_receive = request.form["name_give"]
        # '나는 누구?' 내용
        about_receive = request.form["about_give"]
        new_doc = {
            "profile_name": name_receive,
            "profile_info": about_receive
        }
        if 'file_give' in request.files:
            #프로필 사진 파일 받기
            file = request.files["file_give"]
            # 프로필 사진 파일 이름 받기
            filename = secure_filename(file.filename)
            # 프로필 사진 파일 이름 '.'으로 분리 후 확장자명 extension 에 할당
            extension = filename.split(".")[-1]
            # 해당 유저 이름으로 파일명 변경
            file_path = f"profile_pics/{username}.{extension}"
            # static 폴더에 파일 저장
            file.save("./static/"+file_path)
            # 파일 이름 업데이트
            new_doc["profile_pic"] = filename
            # 파일 업데이트
            new_doc["profile_pic_real"] = file_path
            # 해당 유저의 new_doc 업데이트
        db.users.update_one({'username': payload['id']}, {'$set':new_doc})
        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

      
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
