from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from api.chatgpt import ChatGPT
from api.utils import generate_excel_and_upload_wrapper, QuoteItem, QuoteData

import os

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"
start_quote_wf_hm = {} #key: user-id, value:  QuoteData

app = Flask(__name__)
chatgpt = ChatGPT()

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    global start_quote_wf_hm

    user_id = event.source.user_id

    if event.message.type != "text":
        return

    if event.message.text == "說話":
        working_status = True
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
        return

    if event.message.text == "閉嘴":
        working_status = False
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"))
        return

    if event.message.text == "圖片":
        image_message = ImageSendMessage(
        original_content_url='https://play-lh.googleusercontent.com/ZyWNGIfzUyoajtFcD7NhMksHEZh37f-MkHVGr5Yfefa-IX7yj9SMfI82Z7a2wpdKCA=w480-h960-rw',
        preview_image_url='https://play-lh.googleusercontent.com/ZyWNGIfzUyoajtFcD7NhMksHEZh37f-MkHVGr5Yfefa-IX7yj9SMfI82Z7a2wpdKCA=w480-h960-rw'
        )

        line_bot_api.reply_message(
            event.reply_token,
            image_message)
        return

    if event.message.text == "打估價單":
        start_quote_wf_hm[user_id] = QuoteData(status=1)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{user_id} 請輸入 [客戶名稱] [工程名稱]"))
        return

    if user_id in start_quote_wf_hm:
        quote_data:QuoteData = start_quote_wf_hm[user_id]
        if quote_data.is_ready:
            # generate excel
            customer_name, project_name = event.message.text.split()
            upload_file_url = generate_excel_and_upload_wrapper(
                customer_name=customer_name, project_name=project_name
                )
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"估價單下載網址= {upload_file_url}"))
            
            # delete user_id from hashmap
            start_quote_wf_hm.pop(user_id, None)
            return
        
        # 1: wait for cn, 2: wait for pn 
        # 3: during item - name 4: during item - quantity
        # 5: during item - unit 6: during item - amount
        # 7: during item - complete
        if quote_data.status == 1: 
            quote_data.customer_name = event.message.text
            quote_data.status += 1
        elif quote_data.status == 2: 
            quote_data.project_name = event.message.text
            quote_data.status += 1
        elif quote_data.status == 3 or event.message.text == "停止估價": 
            start_quote_wf_hm.pop(user_id, None)

        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"估價單下載網址= {quote_data}"))
        return

    if working_status:
        chatgpt.add_msg(f"HUMAN:{event.message.text}?\n")
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        chatgpt.add_msg(f"AI:{reply_msg}\n")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))


if __name__ == "__main__":
    app.run()
