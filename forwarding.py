import os
import json
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events

load_dotenv()
API_ID = int(os.getenv('30157302'))
API_HASH = os.getenv('0052039fb2fca727868d0228cdaad569')
BOT_TOKEN = os.getenv('8548114461:AAHPh6ko0lx2iP4uXEiKoZ_mRZv9-UU7_vw')
ADMIN_TG_ID = int(os.getenv('8255552078'))
SESSION_NAME = 'user_session'
CONFIG_FILE = 'config.json'

message_id_map = {}

# Initialize clients WITHOUT starting them
bot_client = TelegramClient('bot', API_ID, API_HASH)
user_client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Conversation state
user_states = {}

# Config functions
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {'sources': [], 'dests': []}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def is_admin(event):
    return event.sender_id == ADMIN_TG_ID

# Bot client command handlers
@bot_client.on(events.NewMessage(pattern='/addsource'))
async def add_source_start(event):
    if not is_admin(event):
        return
    user_states[event.sender_id] = {'mode': 'addsource', 'step': 1}
    await event.respond('Send the numeric group/channel ID for the new source.')

@bot_client.on(events.NewMessage(pattern='/removesource'))
async def remove_source_start(event):
    if not is_admin(event):
        return
    user_states[event.sender_id] = {'mode': 'removesource', 'step': 1}
    await event.respond('Send the numeric group/channel ID to remove.')

@bot_client.on(events.NewMessage(pattern='/adddest'))
async def add_dest_start(event):
    if not is_admin(event):
        return
    user_states[event.sender_id] = {'mode': 'adddest', 'step': 1}
    await event.respond('Send the numeric group/channel ID for the destination.')

@bot_client.on(events.NewMessage(pattern='/removedest'))
async def remove_dest_start(event):
    if not is_admin(event):
        return
    user_states[event.sender_id] = {'mode': 'removedest', 'step': 1}
    await event.respond('Send the numeric group/channel ID to remove.')

@bot_client.on(events.NewMessage(pattern='/showconfig'))
async def show_config(event):
    if not is_admin(event):
        return
    config = load_config()
    srcs = "\n".join(
        f"{s['chat_id']} (topic {s['topic_id']})" if s.get('topic_id') else str(s['chat_id'])
        for s in config['sources']
    ) or "(none)"
    dsts = "\n".join(
        f"{d['chat_id']} (topic {d['topic_id']})" if d.get('topic_id') else str(d['chat_id'])
        for d in config['dests']
    ) or "(none)"
    msg = f"**Sources:**\n{srcs}\n\n**Destinations:**\n{dsts}"
    await event.respond(msg)

# Generic message handler for state machine
@bot_client.on(events.NewMessage())
async def handle_all(event):
    if not is_admin(event):
        return
    state = user_states.get(event.sender_id)
    if not state:
        return

    mode = state['mode']
    step = state['step']
    text = event.text.strip()

    # Add source flow
    if mode == 'addsource':
        if step == 1:
            try:
                chat_id = int(text)
                state['chat_id'] = chat_id
                state['step'] = 2
                await event.respond('Add topic? (yes/no)')
            except ValueError:
                await event.respond('Please send a valid numeric chat ID.')
        elif step == 2:
            if text.lower().startswith('y'):
                state['step'] = 3
                await event.respond('Send the topic/thread ID:')
            else:
                config = load_config()
                config['sources'].append({'chat_id': state['chat_id'], 'topic_id': None})
                save_config(config)
                user_states.pop(event.sender_id)
                await event.respond(f'Added source {state["chat_id"]} without topic.')
        elif step == 3:
            try:
                topic_id = int(text)
                config = load_config()
                config['sources'].append({'chat_id': state['chat_id'], 'topic_id': topic_id})
                save_config(config)
                user_states.pop(event.sender_id)
                await event.respond(f'Added source {state["chat_id"]} with topic {topic_id}.')
            except ValueError:
                await event.respond('Please send a valid numeric topic ID.')

    # Remove source flow
    elif mode == 'removesource':
        if step == 1:
            try:
                chat_id = int(text)
                config = load_config()
                before = len(config['sources'])
                config['sources'] = [s for s in config['sources'] if s['chat_id'] != chat_id]
                save_config(config)
                user_states.pop(event.sender_id)
                await event.respond(f'Removed {before - len(config["sources"])} sources matching {chat_id}.')
            except ValueError:
                await event.respond('Please send a valid numeric chat ID.')

    # Add destination flow
    elif mode == 'adddest':
        if step == 1:
            try:
                chat_id = int(text)
                state['chat_id'] = chat_id
                state['step'] = 2
                await event.respond('Add topic? (yes/no)')
            except ValueError:
                await event.respond('Please send a valid numeric chat ID.')
        elif step == 2:
            if text.lower().startswith('y'):
                state['step'] = 3
                await event.respond('Send the topic/thread ID:')
            else:
                config = load_config()
                config['dests'].append({'chat_id': state['chat_id'], 'topic_id': None})
                save_config(config)
                user_states.pop(event.sender_id)
                await event.respond(f'Added destination {state["chat_id"]} without topic.')
        elif step == 3:
            try:
                topic_id = int(text)
                config = load_config()
                config['dests'].append({'chat_id': state['chat_id'], 'topic_id': topic_id})
                save_config(config)
                user_states.pop(event.sender_id)
                await event.respond(f'Added destination {state["chat_id"]} with topic {topic_id}.')
            except ValueError:
                await event.respond('Please send a valid numeric topic ID.')

    # Remove destination flow
    elif mode == 'removedest':
        if step == 1:
            try:
                chat_id = int(text)
                config = load_config()
                before = len(config['dests'])
                config['dests'] = [d for d in config['dests'] if d['chat_id'] != chat_id]
                save_config(config)
                user_states.pop(event.sender_id)
                await event.respond(f'Removed {before - len(config["dests"])} destinations matching {chat_id}.')
            except ValueError:
                await event.respond('Please send a valid numeric chat ID.')
                
@user_client.on(events.NewMessage())
async def forwarder(event):
    config = load_config()
    forwarding_sources = config.get('sources', [])
    forwarding_dests = config.get('dests', [])

    chat_id = remove_prefix(event.chat_id)
    # print(f"Received message in chat {chat_id}")

    for source in forwarding_sources:
        if chat_id == source['chat_id']:
            msg_topic_id = getattr(event.message, 'message_thread_id', None)
            if source.get('topic_id') is None or source.get('topic_id') == msg_topic_id:
                for dest in forwarding_dests:
                    try:
                        # Determine reply_to id for destination based on mapping
                        reply_to_id = None
                        if event.message.reply_to_msg_id:
                            reply_to_id = message_id_map.get(
                                (chat_id, event.message.reply_to_msg_id, dest['chat_id'])
                            )

                        # Use reply_to_id if message is a reply (and we have mapping), otherwise use topic_id
                        sent_msg = await user_client.send_message(
                            dest['chat_id'],
                            event.message,
                            reply_to=reply_to_id if reply_to_id else dest.get('topic_id')
                        )

                        # Cache the mapping of source and forwarded message IDs
                        message_id_map[(chat_id, event.message.id, dest['chat_id'])] = sent_msg.id

                    except Exception as e:
                        print(f"Error sending to {dest['chat_id']}: {e}")

def remove_prefix(chat_id):
    chat_id_str = str(chat_id)
    if chat_id_str.startswith('-100'):
        return int(chat_id_str[4:])  # Remove first 4 characters: '-100'
    return chat_id

# Main function to run both clients
async def main():
    # Start bot client with bot token
    await bot_client.start(bot_token=BOT_TOKEN)
    print("Bot client started")
    
    # Start user client (will prompt for login on first run)
    await user_client.start()
    print("User client started")
    
    print("Both clients running...")
    
    await asyncio.gather(
        bot_client.run_until_disconnected(),
        user_client.run_until_disconnected()
    )

if __name__ == "__main__":
    asyncio.run(main())
