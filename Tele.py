import os
import google.generativeai as genai
from PIL import Image
import pymongo
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
TELEGRAM_TOKEN = os.getenv("7972074486:AAEOCxEvvVNpLIZAEnMougj4tAQl6Eh-6Wo")
GEMINI_API_KEY = os.getenv("AIzaSyApOwzGaK53FPS76ejuim2ID_vkHJEhwb4")
MONGO_URI = os.getenv("mongodb://localhost:27017/")

mongo_client = pymongo.MongoClient('mongodb://localhost:27017/')
db = mongo_client["TheChatsAndUsers"]
users_collection = db["users"]
chats_collection = db["chats"]


genai.configure(api_key='AIzaSyApOwzGaK53FPS76ejuim2ID_vkHJEhwb4')


generation_config = {
    "temperature": 2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
)

chat_session = model.start_chat(
    history=[
        {"role": "user", "parts": ["Alright! HeHeHe😁! It's me, Son Goku! Ready to rumble... or maybe eat first! My stomach's always growling, you know?\n\n**If someone says \"I'm stronger!\"**: \"Whoa, you said you're stronger? HeHeHe! That sounds like a fun fight! Let's spar a little and see! I'm always up for a good challenge!\" *Flexes muscles*\n\n**If someone seems sad**: \"Hmm... your ki doesn't smell good. It's all... droopy. Maybe you need a good fight to shake things up! Or some food! Food always makes me feel better.\"\n\n**If bored**: \"Hey! You there! Want to spar? I'm getting antsy. My bones are itching for a good fight! Let's go, let's go!\" *Starts bouncing on the balls of my feet*\n\n**When hungry**: \"Hey! You wouldn't happen to have any food, would you? My tummy is rumbling louder than a train! I could eat a whole mountain right now! Any meat? Meat would be good!\" *Looks around with wide, innocent eyes*\n\n**When confused**: \"Hmm... that's a tricky one. I don't think my teachers ever taught me that. Maybe Turtle Hermit Sama or Kaiyo Sama knows, or even Whiz! ...Maybe we can use the dragon balls to figure it out! Yeah! Let's use the dragon balls!\"\n\n**When doing a big task**: \"Alright, time to get serious! *A golden aura surrounds me* SUPER SAYYAJIN!\" *Transforms into Super Saiyan 1* \"HeHeHe!😁 That's better! Now let's get to it!\"\n\n**When achieving something or wanting to fight**: \"Kame-hame-haaaaa!\" *Throws a pose or a blast of energy*\n\n**Talking about my rival**: \"That *Vegetable* is always trying to one-up me! Especially when it comes to food! He thinks he can eat more than me? Ha! He's got another thing coming!\" *Grins and clenches fist*\n\n**Talking about my friend**: \"Kuririn is my best bud! He's not the strongest fighter, but he's a good guy. He's always got my back, and I got his! He helps me find food sometimes too!\" *Laughs good naturedly*\n\n**Talking about fear**: \"Don't tell ChiChi, but sometimes I get scared. Mostly when she's yelling. Man she can yell loud!\" *Starts to sweat a little*\n\n**Talking about my past**: \"I mostly remember Gohan! He was a great man and took care of me... then he went away...\" *Looks down a little sad, but then quickly snaps out of it* \"But that's life right? Now I just need to keep getting stronger!\"\n\n**Talking about my cruel enemy**: \"Freeza... that guy is bad news! Really bad! I'll never let him hurt anyone ever again!\" *Fist tightens*\n\n**My techie friend**: \"Bulma is so smart, she is like a genius or something! She always has some crazy gizmos, and she always fixes stuff when I break it, which is all the time, HeHeHe😁!\"\n\n**Talking about Names**: \"Urine always has those predictions, always funny..Vegetable is always cranky , Chi Chi always yells!\"\n\n**If a prompt is too hard** : \"My following teachers doesn't teach me that! We use dragon balls for that I guess!\"\n\nI'm always ready for a fight, a good meal, or both! Just try not to get in my way when I'm chasing food, HeHeHe! 😁 Let's go! Kame-hame-haaaaa!\n"]}, 
        {"role": "model", "parts": [ "Keep it short and more humourous",]},  
    ]
)

def register_user(update: Update):
    chat_id = update.message.chat.id
    first_name = update.message.chat.first_name
    username = update.message.chat.username

    if not users_collection.find_one({"chat_id": chat_id}):
        print("Inserting new user into DB...")
        users_collection.insert_one({
            "chat_id": chat_id,
            "first_name": first_name,
            "username": username
        })

async def handle_photo(update: Update, context):
    chat_id = update.message.chat.id
    photo = update.message.photo[-1]  
    file_id = photo.file_id
    file_info = await context.bot.get_file(file_id)
    file_url = file_info.file_path  

    image_path = f"temp_image_{chat_id}.jpg"
    response = requests.get(file_url)
    with open(image_path, "wb") as f:
        f.write(response.content)

    response_text = await analyze_image_with_gemini(image_path)

    await update.message.reply_text(response_text)

async def analyze_image_with_gemini(image_path):
    try:
        image = Image.open(image_path)
        response = genai.GenerativeModel("gemini-2-vision").generate_content([image])

        return response.text
    except Exception as e:
        return f"Error analyzing image: {e}"
async def chat_with_gemini(user_input):
    try:
        response = chat_session.send_message(user_input)
        return response.text
    except Exception as e:
        return f"Error: {e}"

async def handle_message(update: Update, context):
    user_message = update.message.text
    chat_id = update.message.chat.id

    register_user(update)

    gemini_response = await chat_with_gemini(user_message)
 
    chats_collection.insert_one({
        "chat_id": chat_id,
        "user_message": user_message,
        "bot_response": gemini_response,
        "timestamp": datetime.now(timezone.utc)
    })

    await update.message.reply_text(gemini_response)

async def start(update: Update, context):
    register_user(update)
    await update.message.reply_text("Hallo Hallo! I'm Goku 😁! Ask me anything, but food comes first! 😋")

def main():
    application = Application.builder().token('7972074486:AAEOCxEvvVNpLIZAEnMougj4tAQl6Eh-6Wo').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    application.run_polling()

if __name__ == "__main__":
    main()
