import discord
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
import re

callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

apps = {
    "gremlin": "YOUR_BOT_TOKEN_GOES_HERE",
}

my_name = "gremlin"
TOKEN = apps[my_name]
model_path = "/path/to/model/file" # I recommend Llama-3.1-8B-Instruct-abliterated_via_adapter.Q8_0.gguf

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

client = discord.Client(intents=intents)
bot_name = client.user.name

llm = LlamaCpp(
    model_path=model_path,
    callback_manager=callback_manager,
    verbose=False,
    n_ctx=2048,
)

def query_unfiltered(question):
    message = llm.invoke(question, stop=["@", "<|eot_id|>"])
    return message


@client.event
async def on_ready():
    print(f"Bot is ready. Logged in as {client.user}")


async def process_message(prompt, channel):
    async with channel.typing():
        response = query_unfiltered(prompt).strip()
    await channel.send(response)


def lookup(match):
    numeric_id = match.group(0)[2:-1]
    replacement = client.get_user(int(numeric_id))
    if replacement is not None:
        return replacement.name
    return ""

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

@client.event
async def on_message(msg):

    confirmed = False

    if client.user in msg.mentions or str(client.user) in msg.content:
        confirmed = True

    if msg.author.id != client.user.id:

        messages = []
        async for history_msg in msg.channel.history(limit=48):
            edit_msg = history_msg.content.replace("\n", " ")
            if edit_msg != "" and not (history_msg.author.id == client.user.id and has_numbers(edit_msg)):

                edit_msg = re.sub(r"<@[0-9]+>", lookup, edit_msg)
                edit_msg.replace(bot_name, my_name).strip()

                if my_name not in edit_msg:
                    messages.append("@" + history_msg.author.name + ": " + edit_msg)

        messages.reverse()
        messages = "\n".join(messages)

        print(confirmed)
        if confirmed:
            await process_message(messages + "\n@" + my_name + ": ", msg.channel)


client.run(TOKEN)