import discord
import time
from datetime import datetime
import random
from libs.myvariables import Static
import libs.database as mydb

def static_response():
    vars = Static()
    return vars

def change_giveawayData(msgID, condition, newData, change):
      if change:
          mydb.update_row_data(newColumn=condition, newValue=newData, conditionColumn="msgID", conditionValue=msgID)
      mydb.insert_query(newData)
      return

async def get_message(bot, channelID, msgID):
    channel = bot.get_channel(channelID)
    return await channel.fetch_message(msgID)

def remove_list(oldList, removeList):
    return [i for i in oldList if i not in removeList]

async def winner_format(bot, userData):
    amountWinners = userData["winners"]
    possibleWinners = userData["entries"]
    if amountWinners > 1:
        winnersList = random.choices(userData["entries"], k=userData["winners"])
        possibleWinners = remove_list(possibleWinners, winnersList)
        finishedList = []

        for i in winnersList:
            finishedList.append(f"<@{i}>")

        allWinners = ', '.join(finishedList)
    else:
        user = random.choice(userData['entries'])
        winnersList = [user]
        possibleWinners = remove_list(possibleWinners, winnersList)
        allWinners = f"<@{user}>"

    updateEmbed = discord.Embed(title=userData['prize'], color=0x2c2d31)
    updateEmbed.add_field(name="", value=f"\n{userData['description']}\n\nEnded: <t:{int(userData['end'])}:R> (<t:{int(userData['end'])}:f>)\nHosted by: {bot.get_user(userData['creator']).mention}\nEntries: **{len(userData['entries'])}**\nWinners: **{allWinners}**")
    updateEmbed.timestamp = datetime.now()
    view = discord.ui.View()
    view.clear_items()
    message = await get_message(bot, userData["channelID"], userData["msgID"])
    changeData = {"entries": possibleWinners, "completed": "True"}
    change_giveawayData(msgID=userData['msgID'], newData=changeData['entries'], condition="entries", change=True)
    await message.edit(embed=updateEmbed, view=view)
    await message.reply(f"Congratulations {allWinners}! You won the **{userData['prize']}**!")

async def update_embed(bot, interaction: discord.Interaction, update=False):
    data = mydb.format_data("giveaway", mydb.return_row_data(condition="msgID", value=interaction.message.id))
    for i, v in enumerate(data):
        if interaction.message.id == v['msgID']:
            userData = v
    messageData = await get_message(bot, userData['channelID'], userData['msgID'])

    if update:
        entriesList = userData["entries"]
        if interaction.user.id in entriesList:
            await interaction.response.send_message("You have already entered this giveaway!", ephemeral=True)
            return
        entriesList.append(interaction.user.id)
        change_giveawayData(newData=entriesList, condition="entries", msgID=userData['msgID'], change=True)
    updateEmbed = discord.Embed(title=userData['prize'], color=static_response().defaultColor)
    updateEmbed.add_field(name="", value=f"\n{userData['description']}\n\nEnds: <t:{int(userData['end'])}:R> (<t:{int(userData['end'])}:f>)\nHosted by: {bot.get_user(userData['creator']).mention}\nEntries: **{len(entriesList)}**\nWinners: **{userData['winners']}**")
    updateEmbed.timestamp = datetime.now()
    await messageData.edit(embed=updateEmbed)

    await interaction.response.send_message("You have entered the giveaway!", ephemeral=True)

def rerolling(winners, dataInfo):
    
        if winners > 1:
            winnersList = random.choices(dataInfo["entries"], k=dataInfo["winners"])
            possibleWinners = remove_list(possibleWinners, winnersList)
            finishedList = []

            for i in winnersList:
                finishedList.append(f"<@{i}>")

            allWinners = ', '.join(finishedList)
        else:
            possibleWinners = remove_list(possibleWinners, winnersList)
            allWinners = f"<@{random.choice(dataInfo['entries'])}>"

        change_giveawayData(newData=possibleWinners, condition="entries", msgID=dataInfo['msgID'], change=True)

        return allWinners

def return_giveaway(bot, unix):
    class giveawayModal(discord.ui.Modal):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.add_item(discord.ui.InputText(label="Prize", placeholder="Discord Nitro", style=discord.InputTextStyle.short, required=True))
            self.add_item(discord.ui.InputText(label="Winners", placeholder="1", value="1", style=discord.InputTextStyle.short, required=True))
            self.add_item(discord.ui.InputText(label="Description", style=discord.InputTextStyle.long, required=True))
            
        async def callback(self, interaction: discord.Interaction):
            giveawayEnd = time.time() + unix
            creationEmbed = discord.Embed(title=self.children[0].value, color=static_response().defaultColor)
            creationEmbed.add_field(name="", value=f"\n{self.children[2].value}\n\nEnds: <t:{int(giveawayEnd)}:R> (<t:{int(giveawayEnd)}:f>)\nHosted by: {interaction.user.mention}\nEntries: **0**\nWinners: **{int(self.children[1].value)}**")
            embedTimestamp = datetime.now()
            creationEmbed.timestamp = embedTimestamp
            view = discord.ui.View(timeout=None)
            button = discord.ui.Button(emoji="🎉", style=discord.ButtonStyle.blurple)
            view.add_item(button)

            message = await interaction.channel.send(embed=creationEmbed, view=view)
            newData = f"msgID={int(message.id)}, channelID={int(interaction.channel.id)}, prize={self.children[0].value}, description={self.children[2].value}, creator={int(interaction.user.id)}, winners={int(self.children[1].value)}, end={giveawayEnd}, completed=False"
            mydb.insert_query(values=newData)

            async def button_pressed(interaction):
                await update_embed(bot, interaction, update=True)

            await interaction.response.send_message(content=f"Created Giveaway with ID: {message.id}", ephemeral=True)

            button.callback = button_pressed

    return giveawayModal(title="Create Giveaway")