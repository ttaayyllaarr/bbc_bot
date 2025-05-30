import functools, json, datetime, inspect, logging, re, os, pytz, asyncio, sys, random, uuid, dateparser, parsedatetime, discord
from datetime import datetime, date, timedelta
from dateutil import parser
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import app_commands
sys.stdout.reconfigure(encoding='utf-8')  # ✅ Ensures UTF-8 output

# ✅ Configure logging
logging.basicConfig(
    format="[%(asctime)s] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ✅ File logging
file_handler = logging.FileHandler("output.log", encoding="utf-8", mode="a")
file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
logging.getLogger().addHandler(file_handler)

# ✅ Console logging (prints logs in PowerShell)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
logging.getLogger().addHandler(console_handler)

# ✅ Log message function with correct `server_name` integration
def log_message(interaction_or_system, message, **kwargs):
    logger = logging.getLogger()

    if isinstance(interaction_or_system, discord.Interaction):
        # ✅ Use `interaction.command.name` when available, otherwise fallback to function name
        command_name = interaction_or_system.command.name if interaction_or_system.command else inspect.currentframe().f_back.f_code.co_name
        server_name = interaction_or_system.guild.name if interaction_or_system.guild else "Direct Message"
        user_name = interaction_or_system.user.name
        prefix = f"User {user_name} executed /{command_name} in {server_name}."
    else:
        prefix = f"[System] {interaction_or_system}"

    param_details = " | ".join([f"{key}: {value}" for key, value in kwargs.items() if value])

    logger.info(f"{prefix} {message} {param_details}")

    # ✅ Flush all handlers to ensure logs appear instantly
    for handler in logging.getLogger().handlers:
        handler.flush()

# Load token from environment variable
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if TOKEN:
    log_message("System", "✅ Token loaded successfully!")
else:
    log_message("System", "DISCORD_BOT_TOKEN not found!")


intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.voice_states = True  # Ensure you have voice intents enabled
intents.presences = True 
bot = commands.Bot(command_prefix="/", intents=intents)

VOICE_FILE = "voicesettings.json"
HELP_FILE = "help.json"
BONES_FILE = "bones.json"

timezones = [
            "UTC-12:00 (Baker Island)", 
            "UTC-11:00 (Pago Pago)", 
            "UTC-10:00 (Honolulu)",
            "UTC-09:30 (Marquesas Islands)",
            "UTC-09:00 (Anchorage)",
            "UTC-08:00 (Los Angeles)",
            "UTC-07:00 (Denver)",
            "UTC-06:00 (Chicago)",
            "UTC-05:00 (New York)",
            "UTC-04:00 (Santiago)",
            "UTC-03:30 (St. John's)",
            "UTC-03:00 (Buenos Aires)",
            "UTC-02:00 (South Georgia)", 
            "UTC-01:00 (Azores)",
            "UTC±00:00 (London)",
            "UTC+01:00 (Paris)",
            "UTC+02:00 (Cairo)", 
            "UTC+03:00 (Moscow)",
            "UTC+03:30 (Tehran)", 
            "UTC+04:00 (Dubai)", 
            "UTC+05:30 (New Delhi)",
            "UTC+06:00 (Dhaka)", 
            "UTC+07:00 (Bangkok)", 
            "UTC+08:00 (Beijing)", 
            "UTC+09:00 (Tokyo)"
        ]
valid_timezones = {
    "UTC-12:00 (Baker Island)": "Etc/GMT+12",
    "UTC-11:00 (Pago Pago)": "Pacific/Pago_Pago",
    "UTC-10:00 (Honolulu)": "Pacific/Honolulu",
    "UTC-09:30 (Marquesas Islands)": "Pacific/Marquesas",
    "UTC-09:00 (Anchorage)": "America/Anchorage",
    "UTC-08:00 (Los Angeles)": "America/Los_Angeles",
    "UTC-07:00 (Denver)": "America/Denver",
    "UTC-06:00 (Chicago)": "America/Chicago",
    "UTC-05:00 (New York)": "America/New_York",
    "UTC-04:00 (Santiago)": "America/Santiago",
    "UTC-03:30 (St. John's)": "America/St_Johns",
    "UTC-03:00 (Buenos Aires)": "America/Argentina/Buenos_Aires",
    "UTC-02:00 (South Georgia)": "Atlantic/South_Georgia",
    "UTC-01:00 (Azores)": "Atlantic/Azores",
    "UTC±00:00 (London)": "Europe/London",
    "UTC+01:00 (Paris)": "Europe/Paris",
    "UTC+02:00 (Cairo)": "Africa/Cairo",
    "UTC+03:00 (Moscow)": "Europe/Moscow",
    "UTC+03:30 (Tehran)": "Asia/Tehran",
    "UTC+04:00 (Dubai)": "Asia/Dubai",
    "UTC+05:30 (New Delhi)": "Asia/Kolkata",
    "UTC+06:00 (Dhaka)": "Asia/Dhaka",
    "UTC+07:00 (Bangkok)": "Asia/Bangkok",
    "UTC+08:00 (Beijing)": "Asia/Shanghai",  # Beijing shares timezone with Shanghai
    "UTC+09:00 (Tokyo)": "Asia/Tokyo"
}
weekdays = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }


def load_status_messages():
    try:
        with open("statuses.json", "r") as file:
            data = json.load(file)
            log_message("System", f"✅ Loaded status messages: {data.get('status_messages', [])}")  # ✅ Log successful load
            return data.get("status_messages", [])  # ✅ Ensures it returns an empty list if key is missing
    except Exception as e:
        log_message("System", f"⚠️ Error loading statuses: {e}")
        return []


@tasks.loop(seconds=1800)
async def change_status():
    log_message("System", "🔄 Changing bot status...")
    
    status_messages = load_status_messages()  # ✅ Reloads statuses dynamically
    if status_messages:  # ✅ Ensures there's at least one status
        new_status = random.choice(status_messages)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=new_status))
        log_message("System", f"✅ Bot status updated to: {new_status}")  # ✅ Log status update
    else:
        log_message("System", "⚠️ No valid statuses found in `statuses.json`.")


@change_status.before_loop
async def before_change_status():
    await bot.wait_until_ready()
    log_message("System", "🕒 Waiting for bot readiness before updating status...")


script_dir = os.path.dirname(os.path.abspath(__file__))  # Gets correct Linux path
bot_file = os.path.join(script_dir, "main.py")  # Builds a platform-independent path

log_message("System", f"🔹 Loading bot from `{bot_file}`")  # ✅ Debugging


# Load settings from a JSON file (persists across bot restarts)
def load_voicesettings():
    try:
        with open(VOICE_FILE, "r", encoding="utf-8") as file:
            voicesettings = json.load(file)
            log_message("System", f"✅ Loaded voicesettings: {voicesettings}")  # ✅ Log successful load
            return voicesettings
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log_message("System", f"⚠️ Error loading voicesettings.json: {e}")
        return {}


# Save settings to a JSON file (so it persists)
def save_voicesettings():
    try:
        unique_servers = {}  # ✅ Ensure unique entries
        for guild_id, settings in voicesettings.items():
            unique_servers[str(guild_id)] = settings  # ✅ Convert ID to string to avoid issues

        with open(VOICE_FILE, "w", encoding="utf-8") as file:
            json.dump(unique_servers, file, indent=4)
            log_message("System", f"💾 Saved voicesettings: {unique_servers}")  # ✅ Debugging output

    except IOError as e:
        log_message("System", f"⚠️ ERROR: Failed to save voicesettings.json! {e}")


# Load settings when the bot starts
voicesettings = load_voicesettings()
# ✅ Store temp voice channels globally
temporary_channels = {}  # Tracks created voice channels across all servers


TRIGGER_WORD = "`"  # Change this to the desired trigger word
channel_id = None  # Stores the selected channel's ID

def load_user_data():
    try:
        with open("user_timezones.json", "r", encoding="utf-8") as file:
            user_data = json.load(file)  # ✅ Load saved timezones
            log_message("System", f"✅ Loaded user timezones: {user_data}")
            return user_data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log_message("System", f"⚠️ Error loading user timezones: {e}")
        return {}  # ✅ Return empty dictionary if file is missing or corrupted

def save_user_data(user_data):
    try:
        with open("user_timezones.json", "w", encoding="utf-8") as file:
            json.dump(user_data, file, indent=4)  # ✅ Save updated timezone data
            log_message("System", f"💾 Saved user timezones: {user_data}")  # ✅ Debugging confirmation
    except IOError as e:
        log_message("System", f"⚠️ ERROR: Failed to write to user_timezones.json! {e}")


# ✅ Load JSON data for bones.json
def load_json():
    try:
        with open(BONES_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

            if not isinstance(data, dict):  # ✅ Ensure it's structured correctly
                log_message("System", f"⚠️ ERROR: Expected dictionary, got {type(data)}! Fixing...")
                return {}

            log_message("System", f"✅ Loaded bones.json successfully.")  # ✅ Log success
            return data  # ✅ Store data per guild

    except (FileNotFoundError, json.JSONDecodeError) as e:
        log_message("System", f"⚠️ ERROR: Failed to load bones.json! {e}")
        return {}  # ✅ Return an empty dictionary if file is missing or corrupted

# ✅ Save JSON data to bones.json
def save_json(guild_id, key, value):
    data = load_json()  # ✅ Load current data

    if value is None:  # ✅ Handle deletion properly
        if guild_id in data and key in data[guild_id]:
            del data[guild_id][key]  # ✅ Remove specific name
            log_message("System", f"✅ DELETED `{key}` from `{guild_id}`!")

            if not data[guild_id]:  # ✅ If last entry removed, delete guild
                del data[guild_id]
                log_message("System", f"🗑 Removed empty guild `{guild_id}`!")

    else:  # ✅ Store updated values
        if guild_id not in data:
            data[guild_id] = {}  
        data[guild_id][key] = value  # ✅ Ensure correct update

    try:
        with open(BONES_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)  
            log_message("System", f"💾 Saved updated bones.json data: {data}")  # ✅ Ensure it’s written correctly
    except IOError as e:
        log_message("System", f"⚠️ ERROR: Failed to write to bones.json! {e}")


def load_commands():
    try:
        with open("commands.json", "r") as file:
            data = json.load(file)

        if "commands" not in data or not isinstance(data["commands"], list):
            log_message("System", "⚠️ Invalid command structure in `commands.json`!")
            return []

        log_message("System", f"🔍 Raw commands data: {data['commands']}")  # ✅ Debug: Check full data before filtering

        # ✅ Filter out commands marked as deprecated
        active_commands = [cmd for cmd in data["commands"] if not cmd.get("deprecated", False)]
        log_message("System", f"✅ Loaded {len(active_commands)} active commands.")  # ✅ Log successful load
        return active_commands

    except Exception as e:
        log_message("System", f"⚠️ Error loading commands: {e}")
        return []


async def force_reset_commands():
    await bot.wait_until_ready()

    log_message("System", "🛠 Forcefully removing all registered commands from Discord API...")

    if not bot.guilds:
        log_message("System", "⚠️ Bot is not in any servers. Cannot reset commands.")
        return  

    log_message("System", f"🔍 Bot is currently in {len(bot.guilds)} guilds.")

    for guild in bot.guilds:
        if not isinstance(guild, discord.Guild):  
            log_message("System", f"⚠️ Skipping invalid guild object: {guild}")
            continue  

        log_message("System", f"🔍 Processing guild: `{guild.name}` ({guild.id})")  

        try:
            bot.tree.clear_commands(guild=guild)  # ✅ Attempt to remove commands
            await asyncio.sleep(1)  # ✅ Short delay between API calls to prevent rate limiting
            log_message("System", f"✅ Commands cleared for `{guild.name}` ({guild.id})")

        except Exception as e:
            log_message("System", f"⚠️ Error clearing commands for `{guild.name}`: {e}")

    log_message("System", "✅ Successfully removed all server-specific commands.")


async def command_function(interaction: discord.Interaction, command_name: str):
    log_message(interaction, f"🔹 Executing command `{command_name}`")  # ✅ Log command execution
    await interaction.response.defer(ephemeral=True)  # ✅ Acknowledge interaction first

    try:
        await interaction.followup.send(f"✅ Command `{command_name}` executed successfully!")  # ✅ Proper response
        log_message(interaction, f"✅ Successfully executed `{command_name}`")  # ✅ Log success
    except discord.HTTPException as e:
        log_message(interaction, f"⚠️ Failed to execute `{command_name}`: {e}")  # ✅ Log error
        await interaction.followup.send("⚠️ Error executing the command. Please try again.", ephemeral=True)


async def register_commands():
    await bot.wait_until_ready()

    log_message("System", "🛠 Registering commands before syncing...")

    commands_data = load_commands()
    existing_commands = {cmd.name for cmd in bot.tree.get_commands()}

    for cmd in commands_data:
        if cmd.get("deprecated", False):  
            log_message("System", f"⚠️ Skipping deprecated command: `{cmd['name']}`")
            continue

        if cmd["name"] not in existing_commands:
            try:
                log_message("System", f"🔹 Adding command: `{cmd['name']}`")

                async def dynamic_command(interaction: discord.Interaction):
                    await interaction.response.send_message(f"✅ Executed `{interaction.command.name}` command!")

                bot.tree.add_command(discord.app_commands.Command(
                    name=cmd["name"],
                    description=cmd["description"],  
                    callback=dynamic_command
                ))

                await asyncio.sleep(0.5)  # ✅ Add slight delay to prevent rate limiting

            except Exception as e:
                log_message("System", f"⚠️ Failed to add `{cmd['name']}`: {e}")

    log_message("System", f"✅ Commands registered before sync: {[cmd.name for cmd in bot.tree.get_commands()]}")

    try:
        await asyncio.sleep(1)  # ✅ Extra delay before syncing globally
        synced = await bot.tree.sync()  # ✅ Only sync here
        log_message("System", f"✅ Synced {len(synced)} commands globally! Synced Commands: {[cmd.name for cmd in synced]}")

    except discord.app_commands.errors.CommandSyncFailure as e:
        log_message("System", f"⚠️ Command sync failed: {e}")


async def setup_roles():
    for guild in bot.guilds:  
        log_message("System", f"🔍 Checking roles in `{guild.name}`...")
        roles = [role.name for role in guild.roles]
        log_message("System", f"📜 Available Roles: {roles}")

        role_name = "bbc"
        role = discord.utils.get(guild.roles, name=role_name)
        member = guild.get_member(bot.user.id) or await guild.fetch_member(bot.user.id)

        if role and member:
            if role in member.roles:
                log_message("System", f"✅ Bot already has `{role.name}` in `{guild.name}`")
            else:
                try:
                    await member.add_roles(role)
                    log_message("System", f"✅ Assigned `{role.name}` to bot in `{guild.name}`")
                except discord.Forbidden:
                    log_message("System", f"⚠️ Missing Permissions! Bot lacks `Manage Roles` in `{guild.name}`.")
        else:
            log_message("System", f"⚠️ Role `{role_name}` or bot member not found in `{guild.name}`.")


@bot.event
async def on_ready():
    log_message("System", f'✅ Bot is now online as {bot.user}')
    
    await force_reset_commands()  # ✅ Ensure outdated commands are removed first
    await register_commands()  # ✅ Register and sync new commands
    await setup_roles()  # ✅ Run role setup separately  
    
    if not change_status.is_running(): 
        change_status.start() # ✅ Ensures the loop starts only once

    log_message("System", "🎯 Bot setup complete. Ready for interactions!")


@bot.event
async def on_guild_join(guild):
    log_message("System", f"✅ Bot joined server: `{guild.name}` (ID: `{guild.id}`)")

    if guild.system_channel:
        await guild.system_channel.send(
            "👋 **Hello!** Thanks for adding me to your server!\n\n"
            "✨ **Check out what I can do by using** `/help` ✨"
        )

    await bot.tree.sync(guild=guild)  # ✅ Sync commands for the specific guild
    log_message("System", f"✅ Synced commands for `{guild.name}`!")


@bot.event
async def on_guild_remove(guild):
    log_message("System", f"⚠️ Bot was removed from `{guild.name}` (ID: `{guild.id}`)")
    log_message("System", f"🔍 Checking voicesettings before cleanup... {voicesettings}")

    if guild.id in voicesettings:
        log_message("System", f"🔄 Cleaning up settings for `{guild.name}`...")
        del voicesettings[guild.id]  # ✅ Remove voice settings
        save_voicesettings()  # ✅ Persist changes
        log_message("System", f"✅ Cleanup complete for `{guild.name}`.")
    else:
        log_message("System", f"⚠️ Guild ID `{guild.id}` NOT found in voicesettings. No action taken.")


def convert_to_timestamp(extracted_time, format_style, user_timezone="America/New_York"):
    try:
        parsed_time = dateparser.parse(extracted_time, settings={"RELATIVE_BASE": datetime.now()})  # ✅ Parses relative time

        if parsed_time is None:  
            log_message("System", f"⚠️ Failed to parse time: `{extracted_time}`")
            return "⚠️ Unable to process the given time format."

        # Convert stored user timezone to a valid `pytz` format
        pytz_timezone = valid_timezones.get(user_timezone, "UTC")  
        tz = pytz.timezone(pytz_timezone)  

        if parsed_time.tzinfo is None:
            parsed_time = tz.localize(parsed_time)  
        else:
            parsed_time = parsed_time.astimezone(tz)  

        if parsed_time.hour == 0 and parsed_time.minute == 0:
            log_message("System", f"📅 Date detected: `{parsed_time.strftime('%A, %B %d, %Y')}`")
            return f"📅 `{parsed_time.strftime('%A, %B %d, %Y')}`"

        formatted_timestamp = f"<t:{int(parsed_time.timestamp())}:{format_style}>"
        log_message("System", f"✅ Converted `{extracted_time}` to `{formatted_timestamp}` in `{user_timezone}`")
        return formatted_timestamp

    except Exception as e:
        log_message("System", f"⚠️ Timestamp conversion error: {e}")
        return "⚠️ An error occurred while converting the timestamp."

 
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # ✅ Ignore bot messages
    
    log_message("System", f"🔹 Message received from {message.author.name}: {message.content}")  # ✅ Log incoming message
    
    extracted_time = None  # ✅ Initialize variable to prevent UnboundLocalError
    
    # Your extraction logic...
    
    if extracted_time:  # ✅ No more UnboundLocalError
        log_message("System", f"✅ Extracted time: {extracted_time}")

    # Improved regex to detect timestamps or natural language inputs
    match = re.search(r"\b(?:\d{1,2}:\d{2}(?:\s?[APap][Mm])?)\b", message.content) or \
            re.search(r"'([\w\d\-/: ]+)'", message.content) or \
            re.search(r"\b(?:tomorrow|next|in|on|this)?\s?(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?\s?(\d{1,2}(?::\d{2})?\s?[APap][Mm]?)?", message.content, re.I)

    if match:
        extracted_time = match.group(0)  # ✅ Ensure `group()` is called explicitly
        
        if isinstance(extracted_time, str):
            words = extracted_time.lower().split()
        else:
            log_message("System", f"⚠️ ERROR: Invalid extracted_time -> {extracted_time}")
            return  # ✅ Stop execution if extraction failed

        today = date.today()
        words = extracted_time.lower().split()

        if "next" in words:
            for day, index in weekdays.items():
                if day.lower() in words:
                    target_weekday = index
                    days_ahead = (target_weekday - today.weekday() + 7) % 7 or 7
                    parsed_time = today + timedelta(days=days_ahead)
                    await message.channel.send(f"📅 Date detected: `{parsed_time.strftime('%A, %B %d, %Y')}`")
                    return
                
    if extracted_time:
        async def get_user_timezone(user_id):
            user_data = load_user_data()  
            timezone = user_data.get(str(user_id), "UTC")  # ✅ Default to UTC if missing
            return timezone
        
        user_timezone = await get_user_timezone(message.author.id)  # ✅ Fetch per-user timezone
        formatted_timestamp = convert_to_timestamp(extracted_time, "F", user_timezone)  # ✅ Pass timezone

        if formatted_timestamp:
            log_message("System", f"✅ Converted `{extracted_time}` to `{formatted_timestamp}` in `{user_timezone}`")  # ✅ Log conversion
            await message.channel.send(f"📅 Converted Time ({user_timezone}): {formatted_timestamp}")
        else:
            log_message("System", "⚠️ Invalid time format received")  # ✅ Log failure case
            await message.channel.send("⚠️ Invalid time format! Try 'tomorrow at 5pm' or 'next Friday at noon'.", ephemeral=True)

    return None  # ✅ Fallback for unsupported formats


class TimezoneDropdown(discord.ui.Select):
    def __init__(self):
        log_message("System", "🔹 Initializing TimezoneDropdown")  # ✅ Log dropdown creation

        options = [discord.SelectOption(label=tz, value=tz) for tz in timezones]
        super().__init__(placeholder="Select your timezone (UTC offset + major city)", min_values=1, max_values=1, options=options)
        self.selected_timezone = None

    async def callback(self, interaction: discord.Interaction):
        log_message(interaction, f"✅ User selected timezone: {self.values[0]}")  # ✅ Log timezone selection
        
        self.selected_timezone = self.values[0]

        embed = discord.Embed(
            title="🌍 Confirm Timezone",
            description=f"You selected `{self.selected_timezone}`. Click **Confirm** to save.",
            color=discord.Color(0x7eff00)
        )
        confirmation_view = discord.ui.View()
        confirmation_view.add_item(ConfirmTimezoneButton(interaction.user.id, self))

        await interaction.response.edit_message(embed=embed, view=confirmation_view)

class ConfirmTimezoneButton(discord.ui.Button):
    def __init__(self, user_id, dropdown: TimezoneDropdown):
        super().__init__(label="✅ Confirm", style=discord.ButtonStyle.green)
        self.user_id = str(user_id)  # ✅ Store user ID
        self.dropdown = dropdown  # ✅ Reference the dropdown instance

    async def callback(self, interaction: discord.Interaction):
        selected_timezone = self.dropdown.selected_timezone  # ✅ Get confirmed timezone
        user_data = load_user_data()

        user_data[self.user_id] = selected_timezone  # ✅ Save to user database
        save_user_data(user_data)  # ✅ Persist changes

        log_message(interaction, f"✅ Timezone updated to {selected_timezone}")  # ✅ Log timezone update

        embed = discord.Embed(
            title="🎉 Timezone Set!",
            description=f"Your timezone has been updated to `{selected_timezone}`.",
            color=discord.Color(0x7eff00)
        )

        await interaction.response.edit_message(embed=embed, view=None)  # ✅ Remove buttons after saving

@bot.tree.command(name="settimezone", description="Set your timezone using a dropdown menu")
async def settimezone(interaction: discord.Interaction):
    log_message(interaction, "🔹 Command initiated: Set Timezone")  # ✅ Log command execution

    view = discord.ui.View()
    view.add_item(TimezoneDropdown())  

    await interaction.response.send_message("🌍 Select your timezone:", view=view, ephemeral=True)


@bot.tree.command(name="set_lobby", description="Set the lobby voice channel")
@app_commands.describe(channel="Select the voice channel to set as the lobby")
async def set_lobby(interaction: discord.Interaction, channel: discord.VoiceChannel):
    log_message(interaction, "🔹 Command initiated: Set Lobby")  # ✅ Log command execution

    if not interaction.guild:  # ✅ Block DMs
        log_message(interaction, "⚠️ Command aborted: Not in a server")  # ✅ Log failure case
        await interaction.response.send_message("⚠️ This command can only be used in a server.", ephemeral=True)
        return

    guild_id = interaction.guild.id  # Get the guild ID

    if guild_id not in voicesettings:
        voicesettings[guild_id] = {}

    voicesettings[guild_id]["LOBBY_CHANNEL_ID"] = channel.id
    save_voicesettings()  # ✅ Persist settings

    log_message(interaction, f"✅ Lobby set to: {channel.name}")  # ✅ Log success
    await interaction.response.send_message(f"Lobby voice channel set to: **{channel.name}**", ephemeral=True)


@bot.tree.command(name="set_category", description="Set the category for temp voice channels")
@app_commands.describe(category="Select the category where temp voice channels will be created")
async def set_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    log_message(interaction, "🔹 Command initiated: Set Category")  # ✅ Log command execution

    if not interaction.guild:  # ✅ Block DMs
        log_message(interaction, "⚠️ Command aborted: Not in a server")  # ✅ Log failure case
        await interaction.response.send_message("⚠️ This command can only be used in a server.", ephemeral=True)
        return

    guild_id = interaction.guild.id  # Get the guild ID

    if guild_id not in voicesettings:
        voicesettings[guild_id] = {}

    voicesettings[guild_id]["CATEGORY_ID"] = category.id
    save_voicesettings()  # ✅ Persist settings

    log_message(interaction, f"✅ Category set to: {category.name}")  # ✅ Log success
    await interaction.response.send_message(f"Category set to: **{category.name}**", ephemeral=True)


@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    guild_id = guild.id  # Ensure per-server settings

    log_message("System", f"🔹 Voice state update detected for {member.display_name} in {guild.name}")  # ✅ Log user voice activity

    # ✅ Get per-server lobby & category IDs safely
    lobby_channel_id = voicesettings.get(str(guild_id), {}).get("LOBBY_CHANNEL_ID", None)
    category_id = voicesettings.get(str(guild_id), {}).get("CATEGORY_ID", None)

    if not lobby_channel_id or not category_id:
        log_message("System", f"⚠️ Missing settings for `{guild.name}`. Skipping voice event handling.")  # ✅ Log missing configuration
        return  

    # ✅ Create temporary voice channel when user joins the lobby
    if after.channel and after.channel.id == lobby_channel_id:
        category = guild.get_channel(category_id)
        if not category:
            log_message("System", f"⚠️ Category `{category_id}` not found in `{guild.name}`.")  # ✅ Log missing category
            return  

        temp_channel = await guild.create_voice_channel(
            name=f"{member.display_name}'s Lobby",
            category=category,
            reason="Temporary voice channel for lobby."
        )

        temporary_channels[temp_channel.id] = temp_channel
        log_message("System", f"✅ Created temp voice channel `{temp_channel.name}` for `{member.display_name}`.")  # ✅ Log temp channel creation

        await member.move_to(temp_channel)

    # ✅ Delete temp voice channel if it becomes empty
    if before.channel and before.channel.id in temporary_channels:
        temp_channel = temporary_channels.get(before.channel.id)

        if temp_channel and len(temp_channel.members) == 0:
            log_message("System", f"❌ Temp voice channel `{temp_channel.name}` emptied. Deleting...")  # ✅ Log cleanup
            await temp_channel.delete(reason="Temporary channel emptied.")
            del temporary_channels[before.channel.id]

"""
class MemberListTransform(app_commands.Transformer):
    # Transforms a string list into actual Discord Member objects.
    async def transform(self, interaction: discord.Interaction, value: str):
        member_ids = value.split(",")  # Expect comma-separated user IDs
        members = [interaction.guild.get_member(int(member_id.strip())) for member_id in member_ids]
        return [m for m in members if m]  # Remove None values (invalid members)
"""    

# """
@bot.tree.command(name="join", description="Bot joins your voice channel")
async def join(interaction: discord.Interaction):
    log_message(interaction, "🔹 Command initiated: Join")  # ✅ Log command execution

    if not interaction.user.voice:
        log_message(interaction, "⚠️ Command aborted: User not in a voice channel")  # ✅ Log failure case
        await interaction.response.send_message("You need to be in a voice channel for me to join!", ephemeral=True)
        return

    await interaction.response.defer()  # ✅ Prevent timeout warning
    channel = interaction.user.voice.channel

    if interaction.guild.voice_client:
        log_message(interaction, f"⚠️ Already connected to {interaction.guild.voice_client.channel.name}")  # ✅ Log existing connection
        await interaction.followup.send(f"I'm already connected to {interaction.guild.voice_client.channel.name}!", ephemeral=True)
        return

    try:
        await channel.connect()
        log_message(interaction, f"✅ Successfully joined {channel.name}")  # ✅ Log success
        await interaction.followup.send(f"✅ Joined {channel.name}!")
    except Exception as e:
        log_message(interaction, f"⚠️ Error joining voice channel: {e}")  # ✅ Log exception
        await interaction.followup.send(f"⚠️ Failed to join voice channel: {e}", ephemeral=True)


@bot.tree.command(name="leave", description="Bot leaves the voice channel")
async def leave(interaction: discord.Interaction):
    log_message(interaction, "🔹 Command initiated: Leave")  # ✅ Log command execution

    voice_client = interaction.guild.voice_client

    if not voice_client:  # ✅ Ensure bot is connected
        log_message(interaction, "⚠️ Command aborted: Bot not in a voice channel")  # ✅ Log failure case
        await interaction.response.send_message("I'm not in a voice channel!", ephemeral=True)
        return
    
    try:
        await voice_client.disconnect()
        log_message(interaction, "✅ Successfully left the voice channel")  # ✅ Log success
        await interaction.response.send_message("✅ Left the voice channel successfully.")
    except Exception as e:
        log_message(interaction, f"⚠️ Error leaving voice channel: {e}")  # ✅ Log exception
        await interaction.response.send_message(f"⚠️ Error leaving voice channel: {e}", ephemeral=True)
# """    


# View for handling dropdown
class MemberSelectView(discord.ui.View):
    def __init__(self, guild, target_channel, command_user_id):
        log_message("System", f"🔹 Initializing MemberSelectView for {target_channel.name}")  # ✅ Log view creation
        
        super().__init__()
        self.dropdown = MemberSelectDropdown(guild, target_channel)
        self.add_item(self.dropdown)

        confirm_button = ConfirmMoveButton(
            command_user_id=command_user_id, 
            parent_view=self, 
            dropdown=self.dropdown, 
            target_channel=self.dropdown.target_channel  # ✅ Ensure it's passed correctly
        )

        self.add_item(confirm_button)
        self.add_item(CancelMoveButton(command_user_id=command_user_id))

class MemberSelectDropdown(discord.ui.Select):
    def __init__(self, guild: discord.Guild, target_channel: discord.VoiceChannel):
        log_message("System", f"🔹 Initializing MemberSelectDropdown for {target_channel.name}")  # ✅ Log dropdown creation
        
        members = [member for vc in guild.voice_channels for member in vc.members]  # ✅ Get all voice-connected members
        options = [discord.SelectOption(label=member.display_name, value=str(member.id)) for member in members]
        super().__init__(placeholder="Select members to move", min_values=1, max_values=len(members), options=options)
        
        self.selected_members = []
        self.target_channel = target_channel  # ✅ Store target channel

    async def callback(self, interaction: discord.Interaction):
        log_message(interaction, f"✅ Members selected: {[m.display_name for m in self.selected_members]}")  # ✅ Log selections

        self.selected_members = [discord.utils.get(interaction.guild.members, id=int(member_id)) for member_id in self.values]
        await interaction.response.send_message("✅ Members selected! Click **Confirm Move** to proceed.", ephemeral=True)

class CancelMoveButton(discord.ui.Button):
    def __init__(self, command_user_id):
        super().__init__(label="Cancel Move", style=discord.ButtonStyle.danger)
        self.command_user_id = command_user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.command_user_id:
            log_message(interaction, "⚠️ Unauthorized cancel attempt blocked")  # ✅ Log unauthorized access
            await interaction.response.send_message("⚠️ Only the command initiator can cancel!", ephemeral=True)
            return

        log_message(interaction, "❌ Move operation canceled by user")  # ✅ Log cancellation
        await interaction.response.edit_message(content="❌ Move operation canceled.", view=None)

class ConfirmMoveButton(discord.ui.Button):
    def __init__(self, label="Confirm Move", command_user_id=None, parent_view=None, dropdown=None, moved_members=None, target_channel=None):
        super().__init__(label=label, style=discord.ButtonStyle.success, custom_id=str(uuid.uuid4()))  # ✅ Unique ID
        
        # ✅ Initialize attributes immediately
        self.command_user_id = command_user_id
        self.parent_view = parent_view
        self.dropdown = dropdown
        self.moved_members = moved_members
        self.target_channel = target_channel  # ✅ Ensures it's never None

    async def callback(self, interaction: discord.Interaction):
        log_message(interaction, "🔹 Button clicked: Confirm Move")  # ✅ Log button press

        if interaction.user.id != self.command_user_id:
            log_message(interaction, "⚠️ Unauthorized move attempt blocked")  # ✅ Log unauthorized use
            await interaction.response.send_message("⚠️ You are not authorized to confirm this move.", ephemeral=True)
            return

        # ✅ Ensure `target_channel` is correctly assigned (fallback to dropdown)
        if not self.target_channel and self.dropdown:
            log_message(interaction, "🔄 Assigning target channel from dropdown")  # ✅ Log fallback assignment
            self.target_channel = self.dropdown.target_channel  

        # ✅ Check if the target channel still exists
        if not self.target_channel or not isinstance(self.target_channel, discord.VoiceChannel):
            log_message(interaction, "⚠️ Move failed: Invalid or missing target channel")  # ✅ Log error
            await interaction.response.send_message("⚠️ Target channel is invalid or no longer exists!", ephemeral=True)
            return

        log_message(interaction, f"✅ Moving selected members to {self.target_channel.name}")  # ✅ Log move initiation

        selected_members = self.moved_members if self.moved_members else (self.dropdown.selected_members if self.dropdown else [])
        if not selected_members:
            log_message(interaction, "⚠️ Move failed: No members selected")  # ✅ Log error
            await interaction.response.send_message("⚠️ No members selected!", ephemeral=True)
            return

        for member in selected_members:
            try:
                await member.move_to(self.target_channel)
                log_message(interaction, f"✅ Successfully moved {member.display_name}")  # ✅ Log each successful move
            except discord.HTTPException:
                log_message(interaction, f"⚠️ Move failed for {member.display_name}")  # ✅ Log failure
                await interaction.response.send_message(f"⚠️ Failed to move `{member.display_name}`!", ephemeral=True)

        log_message(interaction, f"🎯 Move completed: {len(selected_members)} members moved to {self.target_channel.name}")  # ✅ Log move completion
        await interaction.response.send_message(f"✅ Moved {len(selected_members)} members to `{self.target_channel.name}`.", ephemeral=True)

        self.disabled = True
        if interaction.message:
            try:
                await interaction.message.edit(view=self.parent_view)
            except discord.errors.NotFound:
                log_message(interaction, "⚠️ Message no longer exists. Skipping edit.")  # ✅ Log failure


@bot.tree.command(name="move", description="Move selected users to another voice channel")
@app_commands.describe(channel="Voice channel to move members to")
async def move(interaction: discord.Interaction, channel: discord.VoiceChannel):
    log_message(interaction, "🔹 Command initiated")  # ✅ Log the start of execution

    if not interaction.guild:
        log_message(interaction, "⚠️ Command aborted: Not in a server")  # ✅ Log failure case
        await interaction.response.send_message("⚠️ This command can only be used in a server.", ephemeral=True)
        return

    log_message(interaction, f"✅ User initiating move to {channel.name}")  # ✅ Log user action
    
    view = MemberSelectView(interaction.guild, channel, interaction.user.id)

    log_message(interaction, "⚠️ Awaiting member selection")  # ✅ Log waiting state
    
    await interaction.response.send_message("Select members to move:", view=view)

@bot.tree.command(name="moveall", description="Move all users from one voice channel to another")
@app_commands.describe(source_channel="Source voice channel", target_channel="Destination voice channel")
async def moveall(interaction: discord.Interaction, source_channel: discord.VoiceChannel, target_channel: discord.VoiceChannel):
    log_message(interaction, "🔹 Command initiated")  # ✅ Log start of command execution
    
    if not interaction.guild:
        log_message(interaction, "⚠️ Command aborted: Not in a server")  # ✅ Log failure case
        await interaction.response.send_message("⚠️ This command can only be used in a server.", ephemeral=True)
        return

    if not source_channel.members:
        log_message(interaction, "⚠️ Command aborted: No members found in source channel")  # ✅ Log failure case
        await interaction.response.send_message("No users found in the source channel!", ephemeral=True)
        return
    
    log_message(interaction, f"✅ Moving members from {source_channel.name} to {target_channel.name}")  # ✅ Log action

    moved_members = source_channel.members  # ✅ Store bulk move members
    view = discord.ui.View()
    confirm_button = ConfirmMoveButton(
        command_user_id=interaction.user.id, 
        parent_view=view, 
        dropdown=None, 
        target_channel=target_channel  # ✅ Ensure it's passed correctly
    )
    view.add_item(confirm_button)  # ✅ Now works with a unique `custom_id`
    view.add_item(CancelMoveButton(command_user_id=interaction.user.id))  # ✅ Ensure cancel button also has unique ID

    log_message(interaction, f"⚠️ Awaiting user confirmation to move {len(moved_members)} members")  # ✅ Log waiting state

    await interaction.response.send_message(
        f"⚠️ You are about to move {len(moved_members)} members to `{target_channel.name}`. Click **Confirm Move** to proceed or **Cancel Move** to stop.",
        view=view,
        ephemeral=True
    )

                  
# ✅ Split data into pages (10 items per page)
def paginate_data(data, items_per_page=10):
    log_message("System", f"🔄 Paginating data ({len(data)} items, {items_per_page} per page)")
    return [data[i:i + items_per_page] for i in range(0, len(data), items_per_page)]

# ✅ Create Embed for a specific page
def create_embed(data, page, total_pages, total_bones):
    log_message("System", f"📜 Generating embed for Page {page+1}/{total_pages} (Total: {total_bones} bones)")
    
    embed = discord.Embed(
        title=f"**__Bones List__** (Total: {total_bones} bones) [Page {page+1}/{total_pages}]",
        color=discord.Color(0x7eff00)
    )
    
    for item in data:
        percentage = (item['count'] / total_bones) * 100 if total_bones > 0 else 0  
        embed.add_field(name=f"{item['name']} - {item['count']} bones ({percentage:.2f}%)", value="", inline=False)

    return embed

# ✅ View for pagination buttons
class PaginationView(discord.ui.View):
    def __init__(self, data, guild_id):
        log_message("System", f"🔹 Initializing PaginationView for `{guild_id}`")
        super().__init__()

        guild_data = data.get(str(guild_id), {})
        if not isinstance(guild_data, dict):  
            log_message("System", f"⚠️ ERROR: Invalid `guild_data` for `{guild_id}`! Initializing empty.")
            guild_data = {}

        data_list = [{"name": key, "count": value.get("count", 0)} for key, value in guild_data.items()]
        self.total_bones = sum(item["count"] for item in data_list)

        sorted_data = sorted(data_list, key=lambda x: (-x["count"], x["name"].lower()))
        self.data_pages = paginate_data(sorted_data, 10)
        self.current_page = 0
        self.sorting_mode = "count"

        self.add_buttons()
        self.update_buttons()

    def add_buttons(self):    
        self.previous_button = discord.ui.Button(label="⬅️", style=discord.ButtonStyle.primary, custom_id="prev_page")
        self.next_button = discord.ui.Button(label="➡️", style=discord.ButtonStyle.primary, custom_id="next_page")
        self.sort_alpha = discord.ui.Button(label="A-Z", style=discord.ButtonStyle.danger, custom_id="sort_alpha")
        self.sort_desc = discord.ui.Button(label="Count", style=discord.ButtonStyle.danger, custom_id="sort_desc")

        self.previous_button.callback = self.previous_page
        self.next_button.callback = self.next_page
        self.sort_alpha.callback = self.sort_by_alpha
        self.sort_desc.callback = self.sort_by_count

        self.add_item(self.previous_button)
        self.add_item(self.sort_alpha)
        self.add_item(self.sort_desc)
        self.add_item(self.next_button)

    async def previous_page(self, interaction: discord.Interaction):
        log_message(interaction, f"⬅️ User requested previous page ({self.current_page})")
        if self.current_page > 0:
            self.current_page -= 1
        await self.update_view(interaction)

    async def next_page(self, interaction: discord.Interaction):
        log_message(interaction, f"➡️ User requested next page ({self.current_page})")
        if self.current_page < len(self.data_pages) - 1:
            self.current_page += 1
        await self.update_view(interaction)

    async def sort_by_alpha(self, interaction: discord.Interaction):
        log_message(interaction, "🔤 Sorting by name (A-Z)")
        self.sorting_mode = "alpha"
        sorted_data = sorted(sum(self.data_pages, []), key=lambda x: x["name"].lower())
        self.data_pages = paginate_data(sorted_data, 10)
        self.current_page = 0  
        await self.update_view(interaction)

    async def sort_by_count(self, interaction: discord.Interaction):
        log_message(interaction, "🔢 Sorting by count (highest first)")
        self.sorting_mode = "count"
        sorted_data = sorted(sum(self.data_pages, []), key=lambda x: -x["count"])
        self.data_pages = paginate_data(sorted_data, 10)
        self.current_page = 0  
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        log_message(interaction, f"🔄 Updating view to Page {self.current_page+1}")
        self.update_buttons()
        await interaction.response.edit_message(
            embed=create_embed(self.data_pages[self.current_page], self.current_page, len(self.data_pages), self.total_bones),
            view=self
        )

    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= len(self.data_pages) - 1
        self.sort_alpha.disabled = self.sorting_mode == "alpha"
        self.sort_desc.disabled = self.sorting_mode == "count"


@bot.tree.command(name="showbones", description="Show Bone list")
async def showbones(interaction: discord.Interaction):
    log_message(interaction, "🔹 Command initiated: `showbones`")
    
    if not interaction.guild:  
        log_message(interaction, "⚠️ Command aborted: Not in a server")
        await interaction.response.send_message("⚠️ This command can only be used in a server.", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)  
    data = load_json()

    if not isinstance(data, dict) or guild_id not in data or not isinstance(data[guild_id], dict):
        log_message(interaction, f"⚠️ No valid bone data found for `{interaction.guild.name}`")
        await interaction.response.send_message(f"⚠️ No valid bone data found for `{interaction.guild.name}`!", ephemeral=True)
        return

    view = PaginationView(data, guild_id)  
    log_message(interaction, f"✅ Sending Page 1 of `{guild_id}`'s bones list.")
    
    await interaction.response.send_message(
        embed=create_embed(view.data_pages[0], 0, len(view.data_pages), view.total_bones),
        view=view
    )


@bot.tree.command(name="addname", description="Add a name to the Bones List")
async def addname(interaction: discord.Interaction, name: str):
    log_message(interaction, "🔹 Command initiated: `addname`")  # ✅ Log command execution
    
    if not interaction.guild:  
        log_message(interaction, "⚠️ Command aborted: Not in a server")  # ✅ Log failure case
        await interaction.response.send_message("⚠️ This command can only be used in a server.", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)  
    data = load_json()

    if not isinstance(data, dict):
        log_message(interaction, "⚠️ Data format error detected!")  # ✅ Log issue
        await interaction.response.send_message("⚠️ Data format error!", ephemeral=True)
        return

    name = name.strip()
    if not name:
        log_message(interaction, "⚠️ Invalid name input detected (empty string)")  # ✅ Log empty name attempt
        await interaction.response.send_message("⚠️ Invalid name! Please enter a valid name.", ephemeral=True)
        return

    if len(name) > 12:  
        log_message(interaction, f"⚠️ Name `{name}` exceeds 12 characters!")  # ✅ Log length error
        await interaction.response.send_message(f"⚠️ Name too long! Please enter a name with **12 characters or fewer**.", ephemeral=True)
        return

    if not re.match(r"^[a-zA-Z0-9]+$", name):  
        log_message(interaction, f"⚠️ Invalid characters detected in `{name}`!")  # ✅ Log invalid format
        await interaction.response.send_message("⚠️ Invalid characters detected! Only **letters and numbers** are allowed.", ephemeral=True)
        return

    title_case_name = name.title()

    if guild_id not in data:
        data[guild_id] = {}

    if title_case_name in data[guild_id]:
        log_message(interaction, f"⚠️ Duplicate name `{title_case_name}` found in `{interaction.guild.name}`")  # ✅ Log duplicate detection
        embed = discord.Embed(title="⚠️ Duplicate Name", description=f"`{title_case_name}` is already in the list for `{interaction.guild.name}`.", color=discord.Color.red())
    else:
        log_message(interaction, f"✅ Adding `{title_case_name}` to `{interaction.guild.name}`")  # ✅ Log successful addition
        data[guild_id][title_case_name] = {"count": 1}
        save_json(guild_id, title_case_name, {"count": 1})  

        updated_data = load_json()
        embed = discord.Embed(title="✅ Name Added", description=f"`{title_case_name}` has been added to `{interaction.guild.name}` with count `{updated_data[guild_id][title_case_name]['count']}`!", color=discord.Color(0x7eff00))

    await interaction.response.send_message(embed=embed)


class BoneDropdown(discord.ui.Select):
    def __init__(self, guild_id, names):
        log_message("System", f"🔹 Initializing BoneDropdown for `{guild_id}`")
        try:
            if not isinstance(names, dict):
                log_message("System", f"⚠️ ERROR: Expected dictionary for `{guild_id}`, got `{type(names)}`")
                names = {}

            sorted_names = sorted(names.keys())
            options = [discord.SelectOption(label=name, value=name) for name in sorted_names]

            if not options:
                log_message("System", f"⚠️ ERROR: Dropdown options were empty for `{guild_id}`")

            super().__init__(placeholder="Select a name to add a bone", min_values=1, max_values=1, options=options)

        except Exception as e:
            log_message("System", f"⚠️ ERROR in BoneDropdown for `{guild_id}`: {e}")

    async def callback(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        selected_name = self.values[0]
        log_message(interaction, f"🦴 User selected `{selected_name}` for `{guild_id}`")  # ✅ Log selection

        data = load_json()

        if guild_id not in data:
            data[guild_id] = {}

        if selected_name in data[guild_id]:
            data[guild_id][selected_name]["count"] += 1  # ✅ Increment count
        else:
            data[guild_id][selected_name] = {"count": 1}  # ✅ First-time entry

        save_json(guild_id, selected_name, data[guild_id][selected_name])  

        embed = discord.Embed(
            title="🦴 Bone Added!", 
            description=f"`{selected_name}` now has `{data[guild_id][selected_name]['count']}` bones!", 
            color=discord.Color(0x7eff00)
        )

        log_message(interaction, f"✅ `{selected_name}` bone count updated for `{guild_id}`")
        await interaction.response.edit_message(embed=embed, view=None)


class BoneView(discord.ui.View):
    def __init__(self, guild_id, names):
        log_message("System", f"🔹 Initializing BoneView for `{guild_id}`")  # ✅ Log View creation
        super().__init__()
        self.add_item(BoneDropdown(guild_id, names))
        self.add_item(CancelButton())  # ✅ Include Cancel button


@bot.tree.command(name="bone", description="Add +1 bone to a name's count")
async def bone(interaction: discord.Interaction):
    log_message(interaction, "🔹 Command initiated: `bone`")  # ✅ Log command execution

    if not interaction.guild:
        log_message(interaction, "⚠️ Command aborted: Not in a server")  # ✅ Log failure case
        await interaction.response.send_message("⚠️ This command can only be used in a server.", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    data = load_json()

    if not isinstance(data, dict) or guild_id not in data:
        log_message(interaction, f"⚠️ No valid bone data found for `{interaction.guild.name}`")  # ✅ Log missing data
        await interaction.response.send_message(f"⚠️ No valid bone data found for `{interaction.guild.name}`!", ephemeral=True)
        return

    view = BoneView(guild_id, data[guild_id])  
    log_message(interaction, f"✅ Sending Bone selection menu for `{guild_id}`")
    
    await interaction.response.send_message("Select a name to add a bone:", view=view, ephemeral=True)


class RemoveNameView(discord.ui.View):
    def __init__(self, guild_id, names):
        log_message("System", f"🔹 Initializing RemoveNameView for `{guild_id}`")  # ✅ Log initialization
        super().__init__()
        self.add_item(RemoveDropdown(guild_id, names))
        self.add_item(CancelButton())  # ✅ Include Cancel button

class RemoveDropdown(discord.ui.Select):
    def __init__(self, guild_id, names):
        self.guild_id = str(guild_id)  

        if not names:
            log_message("System", f"⚠️ ERROR: No names found in `{self.guild_id}`! Adding placeholder.")
            names = ["No names available"]

        options = [discord.SelectOption(label=name, value=name) for name in names]
        super().__init__(placeholder="Select a name to remove", min_values=1, max_values=1, options=options, disabled=False)
        self.selected_name = None  

    async def callback(self, interaction: discord.Interaction):
        self.selected_name = self.values[0]  

        log_message(interaction, f"⚠️ User selected `{self.selected_name}` for removal in `{self.guild_id}`")  # ✅ Log selection

        embed = discord.Embed(
            title="⚠️ Confirm Removal",
            description=f"Are you sure you want to remove `{self.selected_name}`?",
            color=discord.Color.orange(),
        )

        confirmation_view = discord.ui.View()
        confirmation_view.add_item(ConfirmButton(self.guild_id, self))  
        confirmation_view.add_item(UndoButton(self))  

        await interaction.response.edit_message(embed=embed, view=confirmation_view)

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        log_message(interaction, "❌ User cancelled removal process.")  # ✅ Log cancellation
        embed = discord.Embed(title="❌ Action Cancelled", description="No name was removed.", color=discord.Color(0x7eff00))
        await interaction.response.edit_message(embed=embed, view=None)  

class UndoButton(discord.ui.Button):
    def __init__(self, dropdown: RemoveDropdown):
        super().__init__(label="Undo Removal", style=discord.ButtonStyle.secondary)
        self.dropdown = dropdown  

    async def callback(self, interaction: discord.Interaction):
        log_message(interaction, f"❌ User undid removal of `{self.dropdown.selected_name}`")  # ✅ Log undo action
        embed = discord.Embed(title="❌ Action Cancelled", description=f"`{self.dropdown.selected_name}` was **not** removed.", color=discord.Color(0x7eff00))
        await interaction.response.edit_message(embed=embed, view=None)  

class ConfirmButton(discord.ui.Button):
    def __init__(self, guild_id, dropdown: RemoveDropdown):
        super().__init__(label="Confirm Removal", style=discord.ButtonStyle.danger)
        self.guild_id = str(guild_id)
        self.dropdown = dropdown  

    async def callback(self, interaction: discord.Interaction):
        selected_name = self.dropdown.selected_name
        log_message(interaction, f"⚠️ User confirmed removal of `{selected_name}` in `{self.guild_id}`")  # ✅ Log confirmation

        data = load_json()

        if self.guild_id not in data or selected_name not in data[self.guild_id]:
            log_message(interaction, f"⚠️ Name `{selected_name}` not found in `{interaction.guild.name}`")  # ✅ Log failure case
            embed = discord.Embed(
                title="⚠️ Name Not Found",
                description=f"`{selected_name}` was not found in `{interaction.guild.name}`.",
                color=discord.Color.orange(),
            )
        else:
            del data[self.guild_id][selected_name]  

            if not data[self.guild_id]:  
                del data[self.guild_id]
                log_message(interaction, f"🗑 Removed empty guild entry for `{interaction.guild.name}`")

            save_json(data)  

            log_message(interaction, f"✅ `{selected_name}` successfully removed from `{interaction.guild.name}`!")  # ✅ Log successful removal
            embed = discord.Embed(
                title="✅ Name Removed",
                description=f"`{selected_name}` has been permanently removed from `{interaction.guild.name}`!",
                color=discord.Color.red(),
            )

        await interaction.response.edit_message(embed=embed, view=None)  

@bot.tree.command(name="removename", description="Remove a name from the list")
async def removename(interaction: discord.Interaction):
    log_message(interaction, "🔹 Command initiated: `removename`")  # ✅ Log command execution
    
    if not interaction.guild:  
        log_message(interaction, "⚠️ Command aborted: Not in a server")  # ✅ Log failure case
        await interaction.response.send_message("⚠️ This command can only be used in a server.", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)  
    data = load_json()

    if not isinstance(data, dict) or guild_id not in data:
        log_message(interaction, f"⚠️ No valid bone data found for `{interaction.guild.name}`")  # ✅ Log missing data
        await interaction.response.send_message(f"⚠️ The list is empty for `{interaction.guild.name}`!", ephemeral=True)
        return

    name_list = list(data[guild_id].keys())

    log_message(interaction, f"✅ Showing removal menu for `{guild_id}`")  # ✅ Log menu display
    view = RemoveNameView(guild_id, name_list[::-1])  
    await interaction.response.send_message("Select a name to remove:", view=view, ephemeral=True)


# Buttons for Adjusting Count
class AdjustCountView(discord.ui.View):
    def __init__(self, guild_id, names, data):
        log_message("System", f"🔹 Initializing AdjustCountView for `{guild_id}`")  
        super().__init__()
        self.guild_id = str(guild_id)
        self.data = data  # ✅ Store bones.json data once

        reversed_names = list(reversed(names))
        self.add_item(CountDropdown(self.guild_id, reversed_names, self.data))  
        self.add_item(CancelButton())

class AdjustButtonView(discord.ui.View):
    def __init__(self, guild_id, entry, data):
        log_message("System", f"🔹 Initializing AdjustButtonView for `{guild_id}` and `{entry['name']}`")  
        super().__init__()
        self.guild_id = str(guild_id)
        self.entry = entry
        self.data = data  # ✅ Store JSON data once and reuse it

        self.add_item(IncreaseCountButton(self.guild_id, self.entry, self.data))
        self.add_item(DecreaseCountButton(self.guild_id, self.entry, self.data))  
        self.add_item(SaveButton(self.guild_id, self.entry, self.data)) 

class SaveButton(discord.ui.Button):
    def __init__(self, guild_id, entry, data):
        super().__init__(label="💾 Save", style=discord.ButtonStyle.primary)
        self.guild_id = str(guild_id)
        self.entry = entry
        self.data = data  # ✅ Store already-loaded data instead of reloading

    async def callback(self, interaction: discord.Interaction):
        log_message(interaction, f"✅ Saving `{self.entry['name']}` count in `{self.guild_id}`")

        if self.guild_id not in self.data or self.entry["name"] not in self.data[self.guild_id]:
            log_message(interaction, f"⚠️ Save failed: `{self.entry['name']}` not found in `{self.guild_id}`")  
            await interaction.response.send_message("⚠️ Name not found in this server's list.", ephemeral=True)
            return

        updated_count = self.entry["count"]
        save_json(self.guild_id, self.entry["name"], {"count": updated_count})  # ✅ Save without reloading json

        log_message(interaction, f"✅ `{self.entry['name']}` count updated to `{updated_count}` in `{self.guild_id}`")  
        embed = discord.Embed(
            title=f"✅ Changes Saved for `{self.entry['name']}`",
            description=f"Final count: `{updated_count}`",
            color=discord.Color(0x7eff00)
        )
        await interaction.response.edit_message(embed=embed, view=None)

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        log_message(interaction, "❌ User cancelled count adjustment.")  # ✅ Log cancel action
        embed = discord.Embed(title="❌ Action Cancelled", description="No changes were made.", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=None)

class IncreaseCountButton(discord.ui.Button):
    def __init__(self, guild_id, entry, data):
        super().__init__(label="➕ Increase Count", style=discord.ButtonStyle.green)
        self.guild_id = str(guild_id)
        self.entry = entry
        self.data = data  # ✅ Use the passed data instead of calling `load_json()`

    async def callback(self, interaction: discord.Interaction):
        log_message(interaction, f"✅ Increasing count for `{self.entry['name']}` in `{self.guild_id}`")  

        if self.entry["name"] in self.data.get(self.guild_id, {}):
            self.data[self.guild_id][self.entry["name"]]["count"] += 1
            save_json(self.guild_id, self.entry["name"], self.data[self.guild_id][self.entry["name"]])
            updated_count = self.data[self.guild_id][self.entry["name"]]["count"]

        embed = discord.Embed(title=f"Adjust Count for `{self.entry['name']}`",
                            description=f"Current count: `{updated_count}`",
                            color=discord.Color.green())

        new_view = AdjustButtonView(self.guild_id, {"name": self.entry["name"], "count": updated_count}, self.data)  
        await interaction.response.edit_message(embed=embed, view=new_view)

class DecreaseCountButton(discord.ui.Button):
    def __init__(self, guild_id, entry, data):
        super().__init__(label="➖ Decrease Count", style=discord.ButtonStyle.red)
        self.guild_id = str(guild_id)
        self.entry = entry
        self.data = data  # ✅ Use the passed data instead of calling `load_json()`

    async def callback(self, interaction: discord.Interaction):
        log_message(interaction, f"✅ Decreasing count for `{self.entry['name']}` in `{self.guild_id}`")  

        if self.guild_id not in self.data or self.entry["name"] not in self.data[self.guild_id]:
            log_message(interaction, f"⚠️ Decrease failed: `{self.entry['name']}` not found in `{self.guild_id}`")  
            await interaction.response.send_message("⚠️ Name not found in this server's list.", ephemeral=True)
            return

        updated_count = self.data[self.guild_id][self.entry["name"]]["count"]

        if updated_count <= 1:
            log_message(interaction, f"⚠️ Cannot decrease `{self.entry['name']}` below `1` in `{self.guild_id}`")  
            await interaction.response.send_message("⚠️ Count cannot go below 1.", ephemeral=True)
            return

        self.data[self.guild_id][self.entry["name"]]["count"] -= 1
        save_json(self.guild_id, self.entry["name"], self.data[self.guild_id][self.entry["name"]])  

        updated_count = self.data[self.guild_id][self.entry["name"]]["count"]

        embed = discord.Embed(
            title=f"Adjust Count for `{self.entry['name']}`",
            description=f"Current count: `{updated_count}`",
            color=discord.Color.red()
        )

        new_view = AdjustButtonView(self.guild_id, {"name": self.entry["name"], "count": updated_count}, self.data)  
        await interaction.response.edit_message(embed=embed, view=new_view)

class CountDropdown(discord.ui.Select):
    def __init__(self, guild_id, names, data):
        self.guild_id = str(guild_id)
        self.data = data  # ✅ Use the passed data

        reversed_names = names[::-1]
        options = [discord.SelectOption(label=name["name"], value=name["name"]) for name in reversed_names]

        log_message("System", f"🔹 Initializing CountDropdown for `{guild_id}` with `{len(options)}` options.")  
        super().__init__(placeholder="Select a name to adjust count", min_values=1, max_values=1, options=options)

    async def callback(self, interaction):
        selected_name = self.values[0]
        log_message(interaction, f"✅ `{selected_name}` selected for adjustment in `{self.guild_id}`")  

        entry = {"name": selected_name, "count": self.data[self.guild_id][selected_name]["count"]} if selected_name in self.data.get(self.guild_id, {}) else None

        if entry:
            view = AdjustButtonView(self.guild_id, entry, self.data)  
            embed = discord.Embed(title=f"Adjust Count for `{selected_name}`", description=f"Current count: `{entry['count']}`", color=discord.Color.green())
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.edit_message(embed=discord.Embed(title="⚠️ Name Not Found", description="Could not find selected name.", color=discord.Color.red()), view=None)

@bot.tree.command(name="adjustcount", description="Manually adjust the count for a name")
async def adjustcount(interaction: discord.Interaction):
    log_message(interaction, "🔹 Command initiated: `adjustcount`")  

    if not interaction.guild:  
        log_message(interaction, "⚠️ Command aborted: Not in a server")  
        await interaction.response.send_message("⚠️ This command can only be used in a server.", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)  
    data = load_json()  # ✅ Load once

    if not isinstance(data, dict) or guild_id not in data:
        log_message(interaction, f"⚠️ No valid data found for `{interaction.guild.name}`!")  
        await interaction.response.send_message(f"⚠️ The list is empty for `{interaction.guild.name}`!", ephemeral=True)
        return

    name_list = [{"name": key, "count": value["count"]} for key, value in data[guild_id].items()]  
    view = AdjustCountView(guild_id, name_list[::-1], data)  

    log_message(interaction, f"✅ Sending adjustment menu for `{guild_id}` with `{len(name_list)}` entries.")  
    await interaction.response.send_message("Select a name to adjust count:", view=view, ephemeral=True)


# Load help data
def load_help_data():
    try:
        with open(HELP_FILE, "r") as file:
            data = json.load(file)

            if not isinstance(data, dict):  
                log_message("System", "⚠️ ERROR: Invalid format detected in `help.json`! Expected dictionary.")
                return {}

            log_message("System", f"✅ Successfully loaded help data ({len(data)} commands).")
            return data  
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log_message("System", f"⚠️ ERROR loading `help.json`: {e}")
        return {}  

async def send_paginated_help(interaction, help_data):
    log_message(interaction, "🔹 Sending paginated help menu via DM.")  
    pages = []
    embed = discord.Embed(title="📖 Bot Commands", color=discord.Color(0x7eff00))

    for i, (command, details) in enumerate(help_data.items()):
        embed.add_field(
            name=f"/{command}",
            value=f"{details.get('description', '⚠️ No description available.')}\n**Usage:** `{details.get('usage', '⚠️ No usage provided.')}`",
            inline=False
        )

        if len(embed.fields) >= 7 or i == len(help_data) - 1:  
            pages.append(embed)
            embed = discord.Embed(title="📖 Bot Commands (Continued)", color=discord.Color(0x7eff00))

    for page in pages:
        try:
            await interaction.user.send(embed=page)
        except discord.Forbidden:
            log_message(interaction, "⚠️ ERROR: Unable to send DM (User has DMs disabled).")  
            await interaction.followup.send("⚠️ I couldn't send you a DM. Sending help here instead:", ephemeral=True)
            return

    log_message(interaction, "✅ Help menu successfully sent via DM.")  

@bot.tree.command(name="help", description="Displays available commands and sends a detailed help menu via DM")
async def help(interaction: discord.Interaction):
    log_message(interaction, "🔹 Command initiated: `help`")  
    await interaction.response.defer(ephemeral=True)  

    help_data = load_help_data()

    if not help_data:
        log_message(interaction, "⚠️ ERROR: No help data available!")  
        await interaction.followup.send("⚠️ Help data is missing or unavailable.", ephemeral=True)
        return

    try:
        await send_paginated_help(interaction, help_data)  
        await interaction.followup.send("✅ Help menu sent to your DMs!", ephemeral=True)  
    except discord.Forbidden:
        log_message(interaction, "⚠️ DM error: Sending help in-channel instead.")  
        await interaction.followup.send("⚠️ I couldn't send you a DM. Sending help here instead:", ephemeral=True)


bot.run(TOKEN)