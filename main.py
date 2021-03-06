# link の形式
# {line_id:{no:no, state:state, param:param, symptoms:{symptoms}, temperature:temperature}}

# インポートしよう。
import os, json, datetime, re
from encoder import encrypt, decrypt
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


# ファイル類
LINKS_JSON = os.path.join('json', 'links.json')

# app作成
app = Flask(__name__)
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['CHANNEL_SECRET']

# 初期ベクトルとパスワード
JSON_CRYPTO_PASSWORD = os.environ['JSON_CRYPTO_PASSWORD']
JSON_CRYPTO_IV = os.environ['JSON_CRYPTO_IV']

api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 質問
choices = ['はい', 'いいえ']
choices = [QuickReplyButton(action=MessageAction(label=f'{choice}', text=f'{choice}')) for choice in choices]
choice_questions = [
            'dummy',
            'のどが痛いですか？',
            '咳はでますか？',
            '痰(たん)がでる、あるいはからんだりしますか？',
            '鼻水がたり、鼻づまりがあったりしますか？',
            '体がだるい、重い等の症状はありますか？',
            'いつもとは違った息苦しさがありますか？',
            '一緒に住んでいる家族の中で、具合の悪い人はいますか？',
            ]
tempr_question = '今の体温を摂氏(℃)単位で入力して下さい。小数点以下1位までお願いします。\n(例):36.2℃の場合\n 36.2 と入力\n(例):37.0℃の場合\n 37.0 と入力'

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
    user_id_coded = encrypt(user_id, JSON_CRYPTO_PASSWORD, JSON_CRYPTO_IV)
    user_msg = event.message.text
    now = datetime.datetime.now()

    # json読み込み
    with open(LINKS_JSON, 'r', encoding='utf-8') as f:
        links = json.load(f)

    # jsonの中になかったらとりま
    if not(user_id_coded in links.keys()):
        links[user_id_coded] = {'no':0, 'state':'linking', 'param':0, 'symptoms':[], 'temperature':0}

    # ここで変数
    user_info = links[user_id_coded]

    # 生徒のstateで分岐
    # 出席番号危機だす
    if user_info['state'] == 'linking':
        # 番号
        user_no = list(map(lambda str: re.sub(r'\D', '', str), user_msg.split('-')))

        # 有効な入力
        if (len(user_no) == 3) and ((user_no[0]+user_no[1]+user_no[2]).isdecimal()) and (1 <= int(user_no[0]) <= 3) and (1 <= int(user_no[1]) <= 6) and (1 <= int(user_no[2]) <= 40):
            user_no = '{0}-{1}-{2}'.format(user_no[0], user_no[1], user_no[2])

            # かぶった時
            if user_no in links.values():
                msg = '既に登録されている出席番号です。別の出席番号を入力してください。'

            # 登録
            else:
                user_info['no'] = user_no
                user_info['state'] = 'linked'
                msg = '登録が完了しました。'

        else:
            msg = '出席番号を、次の(例)のように入力してください。\n(例):「1年C組27番」の場合\n 1-3-27 と入力\n(例):「2年E組9番」の場合\n 2-5-9と入力'

        # 変身！
        api.reply_message(event.reply_token, TextSendMessage(text=msg))

    # リンクしてるとき
    elif user_info['state'] == 'linked':
        if user_msg == '体調チェック':
            # 時刻によって分岐
            if (4 <= now.hour < 9) and (user_info['param'] == 0):
                msg = '朝の体調チェックを開始します。'
                user_info['symptoms'] = []
                user_info['param'] += 1

            else:
                msg = '体調チェックの時間外です。\n朝は4時から9時の間\n昼は12時から14時の間にお願いします。'

            # 変身！
            api.reply_message(event.reply_token, TextSendMessage(text=msg))

        # 朝のやつ
        if 1 <= user_info['param'] < 7:
            if re.fullmatch(r'はい|いいえ', user_msg):
                user_info['param'] += 1
                if re.fullmatch('はい', user_msg):
                    user_info['symptoms'].append(user_info['param'] - 1)

            else:
                error_msg = 'はい か いいえ で答えてください。'
                api.push_message(user_id, TextSendMessage(text=error_msg))


            msg = TextSendMessage(text=choice_questions[user_info['param']], quick_reply=QuickReply(items=choices))

            # 変人
            api.push_message(user_id, messages=msg)

        elif user_info['param'] == 7:
            # 前のやつの処理
            if re.fullmatch('はい', user_msg):
                user_info['symptoms'].append(user_info['param'])

            msg = tempr_question
            api.push_message(user_id, TextSendMessage(text=msg))

            user_info['param'] += 1

        elif user_info['param'] == 8:
            # 有効な入力か
            user_msg = re.sub(r'\D', '', user_msg)
            if not(user_msg == '') and (user_msg.isdecimal) and (300 <= int(user_msg) <= 450):
                user_info['temperature'] = round(float(int(user_msg) / 10), 1)

                msg = '朝の体調チェックが終了しました！お疲れさまでした。\n明日も忘れずにおねがいします\n\nこの体調チェックをやり直したい場合は、4時から9時までの間に、もう一度 体調チェックと入力してください。'
                user_info['param'] = 0

            else:
                msg = '無効な入力です。数値ではない、もしくはあり得ない体温です。\n\n' + tempr_question

            api.push_message(user_id, TextSendMessage(text=msg))

    # json保存
    links[user_id_coded] = user_info
    with open(LINKS_JSON, 'w', encoding='utf-8') as f:
        json.dump(links, f)

    # コマンドラインに出力
    if user_msg == os.environ['SECRET_WORD_BEE']:
        infos = [] # infoに複数形ありましぇええええんｗｗｗ
        fmt = '| {0:>6} | {1:>18} | {2:>6} |'
        # 先に情報を取得
        for v in links.values():
            # info = [grade, class, num, no, symptoms, temperature]
            info = {'grade':v['no'][0], 'class':v['no'][2], 'num':v['no'][4:], 'no':v['no'], 'symptoms':v['symptoms'], 'temperature':v['temperature']}
            if not(info['symptoms'] == []) or (37.5 <= info['temperature']): infos.append(info)

        infos.sort(key=lambda x: (x['grade'], x['class'], x['num']))

        print('----------------------------------------------------------------')
        print(fmt.format('NO', 'SYMPTOMS', 'TEMP'))
        for info in infos: print(fmt.format(info['no'], ','.join(map(str, info['symptoms'])), str(info['temperature'])))
        print('----------------------------------------------------------------')

    elif user_msg == os.environ['SECRET_WORD_BUTTERFLY']:
        print(links)

# ステータスをリセット
@app.route('/')
def reset_status():
    now = datetime.datetime.now()

    if now.hour == 0:
        # json読み込み
        with open(LINKS_JSON, 'r', encoding='utf-8') as f:
            links = json.load(f)
            for v in links.values():
                v['param'] = 0

        with open(LINKS_JSON, 'w', encoding='utf-8') as f:
            json.dump(links, f)

    elif now.hour == 11:
        # json読み込み
        with open(LINKS_JSON, 'r', encoding='utf-8') as f:
            links = json.load(f)
            for v in links.values():
                v['param'] = 100

                with open(LINKS_JSON, 'w', encoding='utf-8') as f:
                    json.dump(links, f)


# 動かすとこ
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
