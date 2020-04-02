# インポートしよう。
from flask import Flask, request, abort
from linebot import(
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import(
    MessageEvent, MessageAction, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, QuickReply, QuickReplyButton
)
import os
import json
import datetime
import re


# 学生の皆さん
class Student:
    def __init__(self, line, no=None, state='linking', param=0, condition=[]):
        self.line = line
        self.no = no
        self.state = state
        self.param = param
        self.condition = condition


# ファイル類
LINKS_JSON = os.path.join('json', 'links.json')

# app作成
app = Flask(__name__)
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['CHANNEL_SECRET']

api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 質問
choices = ['はい', 'いいえ']
choice_questions = [
            'のどが痛いですか？',
            '咳はでますか？',
            '痰(たん)がでる、あるいはからんだりしますか？',
            '鼻水がたり、鼻づまりがあったりしますか？',
            '体がだるい、重い等の症状はありますか？',
            '37.5℃以上の発熱がありますか？',
            'いつもとは違った息苦しさがありますか？',
            '一緒に住んでいる家族の中で、具合の悪い人はいますか？'
            ]

# 変数
students = []

@app.route('/callback', methods=['Post'])
def callback():
    # 取得したい
    signature = request.headers['X-Line-Signature']

    # リクエストをテキストで取得
    body = request.get_data(as_text=True)
    app.logger.info('Request body:' + body)

    # 例外処理とか
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 変数
    user_id = event.source.user_id
    user_msg = event.message.text

    # json読み込み
    with open(LINKS_JSON, 'r', encoding='utf-8') as f:
        links = json.load(f)

        for link in list(links.items()):
            student = Student(link[0], link[1], 'linked')
            students.append(student)

    # jsonの中になかったらとりま
    if not(user_id in links.keys()):
        student = Student(user_id)

    # 返信するとこ
    for student in students:
        if student.line == user_id: break

    # studentのstateで分岐
    # 出席番号危機だす
    if student.state == 'linking':
        # 番号
        user_no = list(map(lambda str: re.sub(r'\D', '', str), user_msg.split('-')))
        print(user_no)

        # 有効な入力
        if (len(user_no) == 3) and ((user_no[0]+user_no[1]+user_no[2]).isdigit()) and (1 <= int(user_no[0]) <= 3) and (1 <= int(user_no[1]) <= 6) and (1 <= int(user_no[2]) <= 40):
            user_no = '-'.join(user_no)

            # かぶった時
            if user_no in links.values():
                msg = '既に登録されている出席番号です。別の出席番号を入力してください。'

            # 登録
            else:
                student.no = user_no
                student.state = 'linked'
                links[student.line] = student.no
                msg = '登録が完了しました。'

        # 無効な入力
        elif not(len(user_no) == 3) or not(user_no[0]+user_no[1]+user_no[2].isdigit()):
            msg = '存在しない出席番号です。\nもう一度、有効な出席番号を入力してください。'

        else:
            msg = '出席番号を、次の(例)のように入力してください。\n(例):「1年C組27番」の場合\n─────[1-3-27]と入力\n(例):「2年E組9番」の場合\n─────[2-5-09]と入力'

        # 変身！
        api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )






# 動かすとこ
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
