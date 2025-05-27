import json
import datetime
import re
import os
import pytz
from datetime import datetime
from dateutil import parser
import dateparser
import parsedatetime
import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = discord.Object(id=1143725025350930432)
SETTINGS_FILE = "settings.json"
HELP_FILE = "help.json"
BONES_FILE = "bones.json"

script_dir = os.path.dirname(os.path.abspath(__file__))  # Gets correct Linux path
bot_file = os.path.join(script_dir, "main.py")  # Builds a platform-independent path

print(f"Loading bot from {bot_file}")  # ✅ Debugging

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.voice_states = True  # Ensure you have voice intents enabled
bot = commands.Bot(command_prefix="!", intents=intents)

cal = parsedatetime.Calendar()

# Load settings from file
def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = f.read()
            if not data.strip():
                return {"LOBBY_CHANNEL_ID": None, "CATEGORY_ID": None}
            return json.loads(data)
    except FileNotFoundError:
        default_settings = {"LOBBY_CHANNEL_ID": None, "CATEGORY_ID": None}
        with open(SETTINGS_FILE, "w") as f:
            json.dump(default_settings, f, indent=4)
        return default_settings

# Save settings to file
def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# Load settings when bot starts
settings = load_settings()
LOBBY_CHANNEL_ID = settings["LOBBY_CHANNEL_ID"]
CATEGORY_ID = settings["CATEGORY_ID"]
temporary_channels = {} # Dictionary to track temporary channels

TRIGGER_WORD = "`"  # Change this to the desired trigger word
channel_id = None  # Stores the selected channel's ID

def convert_to_timestamp(extracted_time, format_style, user_timezone="America/New_York"):
    try:
        parsed_time = dateparser.parse(extracted_time)  # ✅ Converts "Next Tuesday at 6am" automatically
        
        if parsed_time is None:
            print(f"⚠️ Failed to parse time from: {extracted_time}")
            return None
        
        tz = pytz.timezone(user_timezone)  # ✅ Convert to user's timezone
        local_time = tz.localize(parsed_time)
        
        return f"<t:{int(local_time.timestamp())}:{format_style}>"  # ✅ Discord-friendly timestamp
    except Exception as e:
        print(f"⚠️ Timestamp conversion error: {e}")
        return None

def load_json():
    try:
        with open(BONES_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

            if not isinstance(data, dict):  # ✅ Ensure it remains a dictionary
                print(f"⚠️ ERROR: Expected dictionary, got {type(data)}! Fixing...")
                return {}

            return data  # ✅ Keep data as a dictionary instead of a list

    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ ERROR: Failed to load bones.json!")
        return {}  

# Save JSON data
def save_json(data):
    if not isinstance(data, dict):
        print(f"⚠️ ERROR: Expected dictionary, got {type(data)} instead. Fixing...")
        return  

    try:
        with open(BONES_FILE, "w", encoding="utf-8") as file:  # ✅ Explicit absolute path
            json.dump(data, file, indent=4)  # ✅ Writes formatted JSON
    except IOError as e:
        print(f"⚠️ ERROR: Failed to write to bones.json! {e}")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        # await bot.tree.sync(guild=GUILD_ID)  # Corrected guild sync
        await bot.tree.sync()  # Sync slash commands globally
                        
    except Exception as e:
        print(f"⚠️ Slash command sync failed: {e}")
    

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    # Debugging output
    # print(f"DEBUG: Raw Message: {message.content}")

    # Improved regex to detect timestamps or natural language inputs
    match = re.search(r"\b(?:\d{1,2}:\d{2}(?:\s?[APap][Mm])?)\b", message.content) or \
            re.search(r"'([\w\d\-/: ]+)'", message.content) or \
            re.search(r"\b(?:tomorrow|next|in|on|this|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b[\w\d\s:-]+", message.content, re.I)

    # Verify match object exists before processing
    if match:
        extracted_time = match.group() if match else None
        # print(f"DEBUG: Extracted Time: {extracted_time}")  # Debugging

        if extracted_time:
            user_timezone = "America/New_York"  # Replace with actual user data retrieval
            formatted_timestamp = convert_to_timestamp(extracted_time, "F", user_timezone)

            if formatted_timestamp:
                await message.channel.send(f"📅 Converted Time: {formatted_timestamp}")
            else:
                await message.channel.send("⚠️ Invalid time format! Try 'tomorrow at 5pm' or 'next Friday at noon'.")
        else:
            await message.channel.send("⚠️ No valid timestamp detected.")
    

@bot.tree.command(name="set_lobby", description="Set the lobby voice channel")
@app_commands.describe(channel="Select the voice channel to set as the lobby")
async def set_lobby(interaction: discord.Interaction, channel: discord.VoiceChannel):
    # Sets the lobby voice channel for auto-creating temp channels.
    LOBBY_CHANNEL_ID = channel.id

    settings["LOBBY_CHANNEL_ID"] = channel.id
    save_settings(settings)

    await interaction.response.send_message(f"Lobby voice channel set to: **{channel.name}**", ephemeral=True)

@bot.tree.command(name="set_category", description="Set the category for temp voice channels")
@app_commands.describe(category="Select the category where temp voice channels will be created")
async def set_category(interaction: discord.Interaction, category: discord.CategoryChannel):
    # Sets the category for dynamically created voice channels.
    global CATEGORY_ID
    CATEGORY_ID = category.id

    settings["CATEGORY_ID"] = category.id
    save_settings(settings)

    await interaction.response.send_message(f"Category set to: **{category.name}**", ephemeral=True)

@bot.event
async def on_voice_state_update(member, before, after):
    # Handles voice channel creation and deletion dynamically.
    guild = member.guild

    # Ensure lobby and category IDs are set
    if not LOBBY_CHANNEL_ID or not CATEGORY_ID:
        return  # Ignore if they aren't configured

    # If a user joins the lobby channel, create a temporary voice channel
    if after.channel and after.channel.id == LOBBY_CHANNEL_ID:
        category = guild.get_channel(CATEGORY_ID)
        if not category:
            return  # Ensure category exists

        # Create a temporary voice channel
        temp_channel = await guild.create_voice_channel(
            name=f"{member.display_name}'s Lobby",
            category=category,
            reason="Temporary voice channel for lobby."
        )

        # Store reference to the created channel
        temporary_channels[temp_channel.id] = temp_channel

        # Move user to the new channel
        await member.move_to(temp_channel)

    # If a user leaves a temporary voice channel, check if it's empty and delete
    if before.channel and before.channel.id in temporary_channels:
        temp_channel = temporary_channels.get(before.channel.id)

        # Check if it's empty, then delete it
        if temp_channel and len(temp_channel.members) == 0:
            await temp_channel.delete(reason="Temporary channel emptied.")
            del temporary_channels[before.channel.id]

    
class MemberListTransform(app_commands.Transformer):
    # Transforms a string list into actual Discord Member objects.
    async def transform(self, interaction: discord.Interaction, value: str):
        member_ids = value.split(",")  # Expect comma-separated user IDs
        members = [interaction.guild.get_member(int(member_id.strip())) for member_id in member_ids]
        return [m for m in members if m]  # Remove None values (invalid members)
    
@bot.tree.command(name="join", description="Bot joins your voice channel")
async def join(interaction: discord.Interaction):
    # Slash command for the bot to join the voice channel.
    if interaction.user.voice:  # Check if the user is in a voice channel
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message(f"Joined {channel.name}!")
    else:
        await interaction.response.send_message("You need to be in a voice channel for me to join!", ephemeral=True)

@bot.tree.command(name="leave", description="Bot leaves the voice channel")
async def leave(interaction: discord.Interaction):
    # Slash command for the bot to leave the voice channel.
    if interaction.guild.voice_client:  # Check if bot is in a voice channel
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Left the voice channel.")
    else:
        await interaction.response.send_message("I'm not in a voice channel!", ephemeral=True)
          
# Dropdown selection class
class MemberSelectDropdown(discord.ui.Select):
    def __init__(self, members, target_channel):
        options = [
            discord.SelectOption(label=member.display_name, value=str(member.id))
            for member in members  # Only add valid members
        ]

        super().__init__(placeholder="Select members to move...", options=options, min_values=1, max_values=min(len(members), 10))
        self.target_channel = target_channel

    async def callback(self, interaction: discord.Interaction):
        selected_member_ids = self.values
        selected_members = [interaction.guild.get_member(int(member_id)) for member_id in selected_member_ids if member_id.isdigit()]

        moved_members = []
        for member in selected_members:
            print(f"Attempting to move: {member.name}")
            if member.voice and member.voice.channel:
                await member.move_to(self.target_channel)
                moved_members.append(member.display_name)

        await interaction.response.edit_message(content=f"Moved {', '.join(moved_members)} to {self.target_channel.name}!", view=None)

# View for handling dropdown
class MemberSelectView(discord.ui.View):
    def __init__(self, members, target_channel):
        super().__init__()
        self.add_item(MemberSelectDropdown(members, target_channel))

@bot.tree.command(name="move", description="Move selected users to another voice channel")
@app_commands.describe(channel="Voice channel to move members to")
async def move(interaction: discord.Interaction, channel: discord.VoiceChannel):
    # Creates a dropdown menu for selecting members to move.
    voice_channel = interaction.user.voice.channel if interaction.user.voice else None

    if not voice_channel or not voice_channel.members:
        await interaction.response.send_message("You're not in a voice channel or no members to move.", ephemeral=True)
        return

    view = MemberSelectView(voice_channel.members, channel)
    await interaction.response.send_message("Select members to move:", view=view)


@bot.tree.command(name="moveall", description="Move all users from one voice channel to another")
@app_commands.describe(source_channel="Source voice channel", target_channel="Destination voice channel")
async def moveall(interaction: discord.Interaction, source_channel: discord.VoiceChannel, target_channel: discord.VoiceChannel):
    # Moves all users in the source voice channel to the target voice channel.
    if not source_channel.members:
        await interaction.response.send_message("No users found in the source channel!", ephemeral=True)
        return

    moved_members = []
    for member in source_channel.members:
        try:
            await member.move_to(target_channel)
            moved_members.append(member.name)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to move members!", ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.response.send_message("Something went wrong while moving members.", ephemeral=True)
            return

    # Move bot if it's in the source channel
    if interaction.guild.voice_client and interaction.guild.voice_client.channel == source_channel:
        await interaction.guild.voice_client.move_to(target_channel)

    if moved_members:
        await interaction.response.send_message(f"Moved {', '.join(moved_members)} to {target_channel.name}!")
    else:
        await interaction.response.send_message("No members were successfully moved.", ephemeral=True)

                  
# Split data into pages (10 items per page)
def paginate_data(data, items_per_page=10):
    return [data[i:i + items_per_page] for i in range(0, len(data), items_per_page)]

# Create Embed for a specific page
def create_embed(data, page, total_pages, total_bones):
    embed = discord.Embed(
        title=f"**__Bones List__** (Total: {total_bones} bones) [Page {page+1}/{total_pages}]",
        color=discord.Color(0x7eff00)
    )
    
    for item in data:
        percentage = (item['count'] / total_bones) * 100 if total_bones > 0 else 0  # ✅ Avoid division by zero
        embed.add_field(name=f"{item['name']} - {item['count']} bones ({percentage:.2f}%)", value="", inline=False)

    return embed

# View for pagination buttons
class PaginationView(discord.ui.View):
    def __init__(self, data):
        super().__init__()  # ✅ Call parent class first

        # ✅ Ensure data is structured correctly
        data_list = [{"name": key, "count": value.get("count", 0)} for key, value in data.items()]

        # ✅ Assign total bones LAST
        self.total_bones = sum(item["count"] for item in data_list)  

        sorted_data = sorted(data_list, key=lambda x: (-x["count"], x["name"].lower()))
        self.data_pages = [sorted_data[i : i + 10] for i in range(0, len(sorted_data), 10)]
        self.current_page = 0
        self.sorting_mode = "count"

        self.add_buttons()
        self.update_buttons()

    # Adds navigation and sorting buttons.
    def add_buttons(self):    
        self.previous_button = discord.ui.Button(label="⬅️", style=discord.ButtonStyle.primary, custom_id="prev_page")
        self.next_button = discord.ui.Button(label="➡️", style=discord.ButtonStyle.primary, custom_id="next_page")
        self.sort_alpha = discord.ui.Button(label="A-Z", style=discord.ButtonStyle.danger, custom_id="sort_alpha")
        self.sort_desc = discord.ui.Button(label="Count", style=discord.ButtonStyle.danger, custom_id="sort_desc")

        # Assign callbacks to handle interactions
        self.previous_button.callback = self.previous_page
        self.next_button.callback = self.next_page
        self.sort_alpha.callback = self.sort_by_alpha
        self.sort_desc.callback = self.sort_by_count

        # self.add_item(self.first_page)
        self.add_item(self.previous_button)
        self.add_item(self.sort_alpha)
        self.add_item(self.sort_desc)
        self.add_item(self.next_button)
        # self.add_item(self.last_page)

    async def previous_page(self, interaction: discord.Interaction):
        # Navigate to the previous page.
        if self.current_page > 0:
            self.current_page -= 1
        await self.update_view(interaction)

    async def next_page(self, interaction: discord.Interaction):
        # Navigate to the next page.
        if self.current_page < len(self.data_pages) - 1:
            self.current_page += 1
        await self.update_view(interaction)

    async def sort_by_alpha(self, interaction: discord.Interaction):
        # Sort by alphabetical order.
        self.sorting_mode = "alpha"
        sorted_data = sorted(sum(self.data_pages, []), key=lambda x: x["name"].lower())  # ✅ Sorts all entries
        self.data_pages = [sorted_data[i : i + 10] for i in range(0, len(sorted_data), 10)]  # ✅ Re-chunks into pages
        self.current_page = 0  # ✅ Reset to first page
        await self.update_view(interaction)

    async def sort_by_count(self, interaction: discord.Interaction):
        # Sort by count.
        self.sorting_mode = "count"
        sorted_data = sorted(sum(self.data_pages, []), key=lambda x: -x["count"])  # ✅ Sorts all entries
        self.data_pages = [sorted_data[i : i + 10] for i in range(0, len(sorted_data), 10)]  # ✅ Re-chunks into pages
        self.current_page = 0  # ✅ Reset to first page
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        # Refresh the view after an interaction
        self.update_buttons()
        
        await interaction.response.edit_message(
            embed=create_embed(self.data_pages[self.current_page], self.current_page, len(self.data_pages), self.total_bones),  # ✅ Added total_bones
            view=self
        )

    # Disables sorting and navigation buttons based on the current state.
    def update_buttons(self):
        if hasattr(self, "previous_button"):  # ✅ Prevents errors if buttons aren't initialized
            self.previous_button.disabled = self.current_page == 0
        if hasattr(self, "next_button"):
            self.next_button.disabled = self.current_page >= len(self.data_pages) - 1
        if hasattr(self, "sort_alpha"):
            self.sort_alpha.disabled = self.sorting_mode == "alpha"
        if hasattr(self, "sort_desc"):
            self.sort_desc.disabled = self.sorting_mode == "count" 


@bot.tree.command(name="showbones", description="Show Bone list")
async def showbones(interaction: discord.Interaction):
    data = load_json()

    if not data:
        await interaction.response.send_message("⚠️ No bone data found!", ephemeral=True)
        return

    view = PaginationView(data)

    if not hasattr(view, "total_bones"):  
        print("⚠️ ERROR: `total_bones` is STILL missing in PaginationView!")
        await interaction.response.send_message("⚠️ Unable to retrieve total bones!", ephemeral=True)
        return

    await interaction.response.send_message(
        embed=create_embed(view.data_pages[0], 0, len(view.data_pages), view.total_bones),
        view=view
    )


@bot.tree.command(name="addname", description="Add a name to the Bones List")
async def addname(interaction: discord.Interaction, name: str):
    data = load_json()

    if not isinstance(data, dict):
        await interaction.response.send_message("⚠️ Data format error!", ephemeral=True)
        return

    name = name.strip()

    if not name:
        await interaction.response.send_message("⚠️ Invalid name! Please enter a valid name.", ephemeral=True)
        return

    if len(name) > 12:  # ✅ Enforce max character limit
        await interaction.response.send_message(f"⚠️ Name too long! Please enter a name with **12 characters or fewer**.", ephemeral=True)
        return

    # ✅ Convert name to Title Case before saving
    title_case_name = name.title()  # Capitalizes first letter of each word, preserving spaces

    if title_case_name in data:
        embed = discord.Embed(title="⚠️ Duplicate Name", description=f"`{title_case_name}` is already in the list.", color=discord.Color.red())
    else:
        data[title_case_name] = {"count": 1}
        save_json(data)

        # ✅ Reload JSON to verify persistence
        updated_data = load_json()
        embed = discord.Embed(title="✅ Name Added", description=f"`{title_case_name}` has been added with count `{updated_data[title_case_name]['count']}`!", color=discord.Color(0x7eff00))

    await interaction.response.send_message(embed=embed)


class BoneDropdown(discord.ui.Select):
    def __init__(self, names):
        try:
            if not isinstance(names, dict):
                print("⚠️ ERROR: Expected dictionary, got:", type(names))
                names = {}

            sorted_names = sorted(names.keys())
            options = [discord.SelectOption(label=name, value=name) for name in sorted_names]

            if not options:
                print("⚠️ ERROR: Dropdown options were empty!")
                
            super().__init__(placeholder="Select a name to add a bone", min_values=1, max_values=1, options=options)

        except Exception as e:
            print(f"⚠️ ERROR in BoneDropdown: {e}")

    async def callback(self, interaction: discord.Interaction):
        # Handles selection and increments the count.
        selected_name = self.values[0]
        data = load_json()

        if selected_name in data:
            data[selected_name]["count"] += 1  # Increase count
        else:
            data[selected_name] = {"count": 1}  # First-time entry

        save_json(data)

        embed = discord.Embed(title="🦴 Bone Added!", description=f"`{selected_name}` now has `{data[selected_name]['count']}` bones!", color=discord.Color((0x7eff00)))
        await interaction.response.edit_message(embed=embed, view=None)

class BoneView(discord.ui.View):
    def __init__(self, names):
        super().__init__()
        self.add_item(BoneDropdown(names))
        self.add_item(CancelButton())  # ✅ Add Cancel button

@bot.tree.command(name="bone", description="Add +1 bone to a name's count")
async def bone(interaction: discord.Interaction):
    data = load_json()

    if not isinstance(data, dict) or not data:
        print("⚠️ No valid bone data found!")  # ✅ Debugging output
        await interaction.response.send_message("⚠️ No valid bone data found!", ephemeral=True)
        return

    view = BoneView(data)
    await interaction.response.send_message("Select a name to add a bone:", view=view, ephemeral=True)


# Dropdown Select View for Removal
class RemoveNameView(discord.ui.View):
    def __init__(self, names):
        super().__init__()

        dropdown = RemoveDropdown(names)  # ✅ Create dropdown

        self.add_item(dropdown)  
        # self.add_item(ConfirmButton(dropdown))  # ✅ Pass dropdown instance correctly
        self.add_item(CancelButton())  
 
class RemoveDropdown(discord.ui.Select):
    def __init__(self, names):
        if not names:
            print("⚠️ ERROR: No names received inside dropdown! Adding placeholder.")
            names = ["No names available"]

        options = [discord.SelectOption(label=name, value=name) for name in names]

        super().__init__(placeholder="Select a name to remove", min_values=1, max_values=1, options=options, disabled=False)
        self.selected_name = None  # ✅ Store the selected name temporarily

    async def callback(self, interaction: discord.Interaction):
        self.selected_name = self.values[0]  # ✅ Store name instead of deleting immediately

        embed = discord.Embed(
            title="⚠️ Confirm Removal",
            description=f"Are you sure you want to remove `{self.selected_name}`?",
            color=discord.Color.orange(),
        )

        confirmation_view = discord.ui.View()
        confirmation_view.add_item(ConfirmButton(self))  # ✅ Only add confirmation after selection
        confirmation_view.add_item(UndoButton(self))  # ✅ Allow undo option at the same time

        await interaction.response.edit_message(embed=embed, view=confirmation_view)  # ✅ Display buttons after selection

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        # Handles cancel button interaction.
        embed = discord.Embed(title="❌ Action Cancelled", description="No name was removed.", color=discord.Color((0x7eff00)))
        await interaction.response.edit_message(embed=embed, view=None)  # Remove dropdown & buttons

class UndoButton(discord.ui.Button):
    def __init__(self, dropdown: RemoveDropdown):
        super().__init__(label="Undo Removal", style=discord.ButtonStyle.secondary)
        self.dropdown = dropdown  # ✅ Store the dropdown instance

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="❌ Action Cancelled", description=f"`{self.dropdown.selected_name}` was **not** removed.", color=discord.Color((0x7eff00)))

        await interaction.response.edit_message(embed=embed, view=None)  # ✅ Simply update the UI

class ConfirmButton(discord.ui.Button):
    def __init__(self, dropdown: RemoveDropdown):
        super().__init__(label="Confirm Removal", style=discord.ButtonStyle.danger)
        self.dropdown = dropdown  # ✅ Store the dropdown instance

    async def callback(self, interaction: discord.Interaction):
        selected_name = self.dropdown.selected_name  # ✅ Retrieve stored selection
        data = load_json()

        if selected_name in data:
            del data[selected_name]  # ✅ Remove only after confirmation
            save_json(data)

            embed = discord.Embed(
                title="✅ Name Removed",
                description=f"`{selected_name}` has been permanently removed!",
                color=discord.Color.red(),
            )
        else:
            embed = discord.Embed(
                title="⚠️ Name Not Found",
                description=f"`{selected_name}` was not in the list.",
                color=discord.Color.orange(),
            )

        await interaction.response.edit_message(embed=embed, view=None)  # ✅ Update UI after confirmation

# Slash Command to Remove Name
@bot.tree.command(name="removename", description="Remove a name from the list")
async def removename(interaction: discord.Interaction):
    data = load_json()

    if not isinstance(data, dict) or not data:
        await interaction.response.send_message("⚠️ The list is empty!", ephemeral=True)
        return

    name_list = list(data.keys())

    view = RemoveNameView(name_list[::-1])
    await interaction.response.send_message("Select a name to remove:", view=view, ephemeral=True) # Use ephemeral for initial interaction


# Buttons for Adjusting Count
class AdjustCountView(discord.ui.View):
    def __init__(self, names):
        super().__init__()
        reversed_names = list(reversed(names))  # Reverse order to show newest first
        self.add_item(CountDropdown(reversed_names))  # Add dropdown menu
        self.add_item(CancelButton())  # Add cancel button

class AdjustButtonView(discord.ui.View):
    def __init__(self, entry):
        super().__init__()
        self.entry = entry
        self.add_item(IncreaseCountButton(entry))
        self.add_item(DecreaseCountButton(entry))
        self.add_item(SaveButton(entry))  # ✅ Add Save button instead of Cancel

class SaveButton(discord.ui.Button):
    def __init__(self, entry):
        super().__init__(label="💾 Save", style=discord.ButtonStyle.primary)
        self.entry = entry

    async def callback(self, interaction: discord.Interaction):
        # Saves the count changes and confirms the update.
        embed = discord.Embed(title=f"✅ Changes Saved for `{self.entry['name']}`", description=f"Final count: `{self.entry['count']}`", color=discord.Color((0x7eff00)))
        await interaction.response.edit_message(embed=embed, view=None)  # Remove buttons after saving

class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        # Handles cancel button interaction.
        embed = discord.Embed(title="❌ Action Cancelled", description="No changes were made.", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=None)  # Remove dropdown & buttons

class IncreaseCountButton(discord.ui.Button):
    def __init__(self, entry):
        super().__init__(label="➕ Increase Count", style=discord.ButtonStyle.green)
        self.entry = entry

    async def callback(self, interaction: discord.Interaction):
        # Increase count and update embed dynamically.
        data = load_json()

        updated_count = self.entry.get("count", 0)  # ✅ Default to entry's count (or 0)
        
        if self.entry["name"] in data:
            data[self.entry["name"]]["count"] += 1
            save_json(data)  # ✅ Save changes
            updated_count = data[self.entry["name"]]["count"]  # ✅ Reload latest count

        embed = discord.Embed(title=f"Adjust Count for `{self.entry['name']}`",
                            description=f"Current count: `{updated_count}`",
                            color=discord.Color.green())

        new_view = AdjustButtonView({"name": self.entry["name"], "count": updated_count})  
        await interaction.response.edit_message(embed=embed, view=new_view)


class DecreaseCountButton(discord.ui.Button):
    def __init__(self, entry):
        super().__init__(label="➖ Decrease Count", style=discord.ButtonStyle.red)
        self.entry = entry

    async def callback(self, interaction: discord.Interaction):
        # Decrease count and update embed.
        data = load_json()
        updated_count = self.entry["count"]  # ✅ Default value in case modification fails
        if updated_count == 1:
            await interaction.response.send_message("Count cannot go below 1.", ephemeral=True)
            return

        if self.entry["name"] in data:
            data[self.entry["name"]]["count"] = max(1, data[self.entry["name"]]["count"] - 1)  # ✅ Prevent negatives
            # print("💾 Attempting to save data:", data)
            save_json(data)  # ✅ Save changes
            updated_count = data[self.entry["name"]]["count"]  # ✅ Reload latest count

        embed = discord.Embed(title=f"Adjust Count for `{self.entry['name']}`",
                              description=f"Current count: `{updated_count}`",
                              color=discord.Color.red())

        new_view = AdjustButtonView({"name": self.entry["name"], "count": updated_count})  # ✅ Sync entry
        await interaction.response.edit_message(embed=embed, view=new_view)


class CountDropdown(discord.ui.Select):
    def __init__(self, names):
        # Ensure at least one valid option exists
        if not names or len(names) == 0:
            names = [{"name": "No names available", "count": 0}]  # Placeholder to prevent errors
        
        reversed_names = names[::-1]  # Reverse order to show newest first
        options = [discord.SelectOption(label=name["name"], value=name["name"]) for name in reversed_names if isinstance(name, dict) and "name" in name]

        if len(options) == 0:  # Final check before passing options
            options = [discord.SelectOption(label="No names available", value="none")]

        super().__init__(placeholder="Select a name to adjust count", min_values=1, max_values=1, options=options)

    async def callback(self, interaction):
        # Shows adjustment buttons when a name is selected.
        selected_name = self.values[0]
        data = load_json()

        # Find entry
        entry = {"name": selected_name, "count": data[selected_name]["count"]} if selected_name in data else None  # ✅ Correct lookup

        if entry:
            view = AdjustButtonView(entry)  # ✅ Correct view for adjusting count
            embed = discord.Embed(title=f"Adjust Count for `{selected_name}`", description=f"Current count: `{entry['count']}`", color=discord.Color((0x7eff00)))
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.edit_message(embed=discord.Embed(title="⚠️ Name Not Found", description="Could not find selected name.", color=discord.Color.red()), view=None)


# Slash Command to Adjust Count
@bot.tree.command(name="adjustcount", description="Manually adjust the count for a name")
async def adjustcount(interaction: discord.Interaction):
    # Displays a dropdown with names for count adjustment.
    data = load_json()

    if not isinstance(data, dict) or not data:  # ✅ Ensure data is a dictionary
        await interaction.response.send_message("⚠️ The list is empty!", ephemeral=True)
        return

    name_list = [{"name": key, "count": value["count"]} for key, value in data.items()]  # ✅ Convert to list
    view = AdjustCountView(name_list[::-1])  # ✅ Reverse correctly before passing
    await interaction.response.send_message("Select a name to adjust count:", view=view)


# Load help data
def load_help_data():
    try:
        with open(HELP_FILE, "r") as file:
            data = json.load(file)
            if isinstance(data, list):  # ❌ Wrong format, auto-correct it
                print("⚠️ ERROR: Expected dictionary, got list! Fix help.json.")
                return {}  # Prevent errors by returning an empty dictionary
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Split help entries into pages of 6 items each
def paginate_help(commands, page, per_page=6):
    """Returns a subset of commands for the given page."""
    start = (page - 1) * per_page
    end = start + per_page

    if isinstance(commands, dict):  # ✅ Ensure commands are a dictionary
        commands = list(commands.items())  # Convert dictionary to list of tuples
    
    return commands[start:end], len(commands) // per_page + (1 if len(commands) % per_page else 0)

class HelpView(discord.ui.View):
    def __init__(self, page=1):
        super().__init__()
        self.page = page
        self.help_data = load_help_data()
        self.max_pages = len(self.help_data) // 6 + (1 if len(self.help_data) % 6 else 0)
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()  # Remove existing buttons
        if self.page > 1:
            self.add_item(PrevPageButton(self.page - 1))
        if self.page < self.max_pages:
            self.add_item(NextPageButton(self.page + 1))

    async def update_embed(self, interaction):
        """Updates embed when navigating pages."""
        commands, _ = paginate_help(self.help_data, self.page)
        embed = discord.Embed(title="📖 Bot Commands", description=f"Page {self.page}/{self.max_pages}", color=discord.Color(0x7eff00))

        for command, details in commands:
            description = details.get("description", "⚠️ No description available.")  # ✅ Prevent KeyError
            usage = details.get("usage", "⚠️ No usage provided.")  # ✅ Handle missing usage
            embed.add_field(name=f"/{command}", value=f"{description}\n**Usage:** `{usage}`", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)
        # await interaction.response.send_message(embed=embed, view=self)


class PrevPageButton(discord.ui.Button):
    def __init__(self, page):
        super().__init__(label="⬅️ Previous", style=discord.ButtonStyle.secondary)
        self.page = page

    async def callback(self, interaction):
        view = HelpView(self.page)
        await view.update_embed(interaction)

class NextPageButton(discord.ui.Button):
    def __init__(self, page):
        super().__init__(label="➡️ Next", style=discord.ButtonStyle.secondary)
        self.page = page

    async def callback(self, interaction):
        view = HelpView(self.page)
        await view.update_embed(interaction)

@bot.tree.command(name="help", description="Shows available commands")
async def help(interaction: discord.Interaction):
    # Displays paginated help embed.
    help_data = load_help_data()
    page = 1
    commands, max_pages = paginate_help(help_data, page)

    embed = discord.Embed(title="📖 Bot Commands", description=f"Page {page}/{max_pages}", color=discord.Color(0x7eff00))
    for command, details in commands:
        embed.add_field(name=f"/{command}", value=f"{details.get('description', '⚠️ No description available.')}\n**Usage:** `{details.get('usage', '⚠️ No usage provided.')}`", inline=False)

    view = HelpView(page)  # Start at page 1
    await interaction.response.send_message(embed=embed, view=view)


bot.run('MTM3NjI5OTY5MjY1NjE2ODk3MA.G03myl.YJKXS29GNRU0g_3b4zpgmxO7XQpN-m48AXllpE')

