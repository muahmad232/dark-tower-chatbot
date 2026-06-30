import sys, json
sys.path.append('e:/Data Science projects/Dark Tower Chatbot/backend')
from chatbot import Chatbot
bot = Chatbot()
# mock metadata summaries
bot.metadata = []
for name,_ in bot.BOOK_ORDER:
    bot.metadata.append({'metadata':{'source':name,'chunk_type':'summary'},'text':f"{name} is a book. It tells a story about ..."})
print(bot.ask('Give me a short description for each book'))
