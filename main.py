import discord
from discord.ext import tasks
from discord import Option
from discord.ui import View, Button, Select
import requests

from libs.status import status_task as status_task
import libs.giveaway as giveaway
from libs.myvariables import Static
import libs.database as mydb
import libs.economy as economy
import time
import datetime
import random
import asyncio

intents = discord.Intents.all()

bot = discord.Bot(command_prefix="slash", intents=intents)

giveaw = discord.SlashCommandGroup("giveaway", "giveaways")
hibp = discord.SlashCommandGroup("breach", "check databreach data")
econ = discord.SlashCommandGroup("eco", "bingbot economy")

def static_response():
    vars = Static()
    return vars
            
def get_giveawayData(message):
    return mydb.return_row_data("msgID", message)

async def setup_economy(ctx):
    dbData = mydb.get_db_data("economy")
    conn = dbData[0]
    cursor = dbData[1]

    cursor.execute("""INSERT INTO userdata VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (int(ctx.author.id), int(1000), "United Financial Inc.", int(0), int(0), int(time.time()), int(12), int(time.time()), int(20), int(20), int(time.time())))
    conn.commit()

    cursor.close()
    conn.close()

    embed = discord.Embed(title="Account Created", color=static_response().defaultColor)
    embed.set_thumbnail(url=ctx.author.display_avatar)
    embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
    await ctx.respond(embed=embed)

def no_profile(user):
    embed = discord.Embed(title=f"Invalid User: {user.name}", color=0xFCC03D)
    embed.set_thumbnail(url=user.display_avatar)
    embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
    return embed

def add_spent(userID, amount):
    data = mydb.format_data("economy", mydb.return_row_data("economy", "userID", userID))
    newSpent = data['spent'] + amount
    mydb.update_row_data("economy", "spent", newSpent, "userID", userID)

intents = discord.Intents.default()
intents.members=True
bot = discord.Bot(intents=intents)

@tasks.loop(seconds=15)
async def giveaway_loader():
    data = mydb.return_table_data("giveaway")
    
    for i, v in enumerate(data):
        dictData = giveaway.format_data("giveaway", v)
        if v['end'] <= time.time() and v['completed'] == "False":

            await giveaway.winner_format(bot=bot, userData=v)
            return
        
@bot.event
async def on_ready():
    if not giveaway_loader.is_running():
        giveaway_loader.start()

    bot.loop.create_task(status_task(bot))

@bot.event
async def on_guild_join(guild):
    print("help")
        
@giveaw.command(description="Start a giveaway")
async def start(ctx: discord.Interaction, length: Option(str, "Amount of Time", required=True, choices=["1 Minute", "5 Minutes", "10 Minutes", "30 Minutes", "1 Hour", "3 Hours", "12 Hours", "1 Day", "2 Days", "3 Days", "10 Days", "1 Week", "2 Weeks", "3 Weeks", "1 Month"])):
    time = {"1 Minute": 60, "5 Minutes": 300, "10 Minutes": 600, "30 Minutes": 1800, "1 Hour": 3600, "3 Hours": 10800, "12 Hours": 43200, "1 Day": 86400,
            "2 Days": 172800, "3 Days": 259200, "10 Days": 864000, "1 Week": 604800, "2 Weeks": 1209600, "3 Weeks": 1814400, "1 Month": 2629743}
    await ctx.response.send_modal(giveaway.return_giveaway(bot, time[length]))

@giveaw.command(description="Reroll a giveaway")
async def reroll(ctx, winners: Option(int, "Amount to reroll", required=True), message_id: Option(str, "Message ID for the giveaway", required=True)):
    data = mydb.return_row_data("msgID", message_id)
    dictData = giveaway.format_data("giveaway", data)
    
    if dictData["completed"] == "True":
      newWinners = giveaway.rerolling(guild=ctx.guild.id, winners=winners, dataInfo=dictData)
      await ctx.respond(f"Congratulations {newWinners}! You won the **{dictData['prize']}**!")
    else:
        await ctx.respond(f"Invalid Message ID", ephemeral=True)

@hibp.command(name="check", description="Check if company has been in a data breach")
async def breach_check(ctx, company:Option(str, "Breached Company", required=True)):
    re = requests.get(f"https://haveibeenpwned.com/api/v3/breach/{company}")
    if re.status_code == 200:
        data = re.json()
        date = data['BreachDate'].split('-')
        newDate = f"{date[2]}/{date[1]}/{date[0]}"

        dateInt = int(time.mktime(datetime.datetime.strptime(newDate, "%d/%m/%Y").timetuple()))
        embed = discord.Embed(title=data['Name'], description=data['Domain'], color=static_response().defaultColor  )
        embed.set_thumbnail(url=data['LogoPath'])
        embed.add_field(name="Breach Date", value=f"<t:{dateInt}:D>", inline=False)
        embed.add_field(name="Data", value='\n'.join(data['DataClasses']), inline=False)
        embed.add_field(name="Accounts Breached", value=f"{int(data['PwnCount']):,}", inline=False)
    else:
        embed = discord.Embed(title="Company is not in the breach database", color=0xFC8C8C)
    embed.set_footer(text="Powered by itsb1ng.dev", icon_url=static_response().logo)
    await ctx.respond(embed=embed)

@hibp.command(name="latest", description="Latest breach added to the database")
async def latest_breach(ctx):
    re = requests.get("https://haveibeenpwned.com/api/v3/latestbreach")
    if re.status_code == 200:
        data = re.json()
        date = data['AddedDate'].split('T')[0].split('-')
        newDate = f"{date[2]}/{date[1]}/{date[0]}"

        dateInt = int(time.mktime(datetime.datetime.strptime(newDate, "%d/%m/%Y").timetuple()))

        embed = discord.Embed(title=data['Name'], description=data['Domain'], color=static_response().defaultColor)
        embed.set_thumbnail(url=data['LogoPath'])
        embed.add_field(name="Added Date", value=f"<t:{dateInt}:D>", inline=False)

        date = data['BreachDate'].split('-')
        newDate = f"{date[2]}/{date[1]}/{date[0]}"

        dateInt = int(time.mktime(datetime.datetime.strptime(newDate, "%d/%m/%Y").timetuple()))
        embed.add_field(name="Breach Date", value=f"<t:{dateInt}:D>", inline=False)
        embed.add_field(name="Data", value='\n'.join(data['DataClasses']), inline=False)
        embed.add_field(name="Accounts Breached", value=f"{int(data['PwnCount']):,}", inline=False)
    else:
        embed = discord.Embed(title="Cannot reach latest breach", color=0xFC8C8C)
    embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
    await ctx.respond(embed=embed)

@econ.command(name="claim", description="Claim last login reward")
async def claim(ctx):
    try:
        amount = economy.claim(userID=ctx.author.id)
        embed = discord.Embed(title=f"Claimed ⌬{amount['money']:,.0f}", description=f"Hours: {amount['afk']:.0f}\nWallet: `⌬{amount['money']+amount['wallet']:,}`", color=static_response().defaultColor)
        embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
        await ctx.respond(embed=embed)
    except:
        await setup_economy(ctx)

@econ.command(name="coinflip", description="coinflip the bot")
async def coinflip(ctx, amount:Option(int, "bingcoin to flip", required=True), choice:Option(str, "heads or tails", required=True, choices=["heads", "tails"])):
    botChoice = random.choice(['heads', 'tails'])
    try:
        if choice.lower() == "heads" or choice.lower() == "tails":
            formattedData = mydb.format_data("economy", mydb.return_row_data("economy", "userID", ctx.author.id))
            if formattedData['wallet'] >= amount:
                if choice.lower() == botChoice:
                    newWalletAmount = formattedData['wallet'] + amount
                    mydb.update_row_data("economy", newColumn="wallet", newValue=newWalletAmount, conditionColumn="userID", conditionValue=ctx.author.id)
                    embed = discord.Embed(title="Coinflip Won", description=f"You wagered `⌬{amount:,}` and won", color=0x00C11A)
                else:
                    newWalletAmount = formattedData['wallet'] - amount
                    mydb.update_row_data("economy", newColumn="wallet", newValue=newWalletAmount, conditionColumn="userID", conditionValue=ctx.author.id)
                    embed = discord.Embed(title="Coinflip Lost", description=f"You wagered `⌬{amount:,}` and lost", color=0xC10000)
                if botChoice == "heads":
                    embed.set_thumbnail(url='https://i.imgur.com/mdmtX2T.png')
                else:
                    embed.set_thumbnail(url="https://i.imgur.com/loisPPU.png")
                embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
                await ctx.respond(embed=embed)

                add_spent(ctx.author.id, amount)

            else:  
                await ctx.respond(f"You do not have enough bingcoin to coinflip. Check wallet balance")
        else:
            await ctx.respond("Please type a valid input")

    except:
        await setup_economy(ctx) 
    
@econ.command(name="dice", description="roll higher than the bot")
async def dice_roll(ctx, amount:Option(int, "bingcoin to wager", required=True)):
    try:
        formattedData = mydb.format_data("economy", mydb.return_row_data("economy", "userID", ctx.author.id))
        if formattedData['wallet'] >= amount:
            dice = economy.roll_dice(bot)
            
            if dice[1] == dice[2]:
                result = "tied"
                color = 0xFCC03D
                winnerTB = ctx.author.display_avatar
                newWalletAmount = formattedData['wallet']

            elif dice[1] > dice[2]:
                result = "won!"
                color = 0x00C11A
                winnerTB = ctx.author.display_avatar
                newWalletAmount = formattedData['wallet'] + amount
            else:
                result = "lost :("
                color = 0xC10000
                winnerTB = static_response().logo
                newWalletAmount = formattedData['wallet'] - amount
            
            mydb.update_row_data("economy", newColumn="wallet", newValue=newWalletAmount, conditionColumn="userID", conditionValue=ctx.author.id)

            embed = discord.Embed(title=f"{dice[0][0][0]}{dice[0][1][0]} vs {dice[0][2][0]}{dice[0][3][0]}", description=f"You {result} and wagered `⌬{amount:,}`", color=color)
            embed.set_thumbnail(url=winnerTB)
            embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
            await ctx.respond(embed=embed)

            add_spent(ctx.author.id, amount)

        else:  
            await ctx.respond(f"You do not have enough bingcoin to roll the die. Check wallet balance")

    except:
        await setup_economy(ctx) 

@econ.command(name="profile", description="view player profile")
async def profile(ctx, user:Option(discord.Member, "profile", required=True)):        
    try:
        data = mydb.format_data("economy", mydb.return_row_data("economy", "userID", user.id))
    except:
        await ctx.respond(embed=no_profile(user))
        return

    embed = discord.Embed(title=user.name, description=f"Level {economy.current_level(data['spent'])}: {economy.bar_progress(data['spent'])}", color=static_response().defaultColor)
    embed.add_field(name="〉 bingcoin", value=f"Wallet: `⌬{'*****' if ctx.author.id != data['userID'] else '{:,}'.format(data['wallet'])}`\nSpent: `⌬{data['spent']:,}`", inline=False)
    embed.add_field(name="〉 bank", value=f"Deposited: `⌬{data['balance']:,}`/`⌬{economy.bank_balance(data['bank']):,}`\nBank: `{data['bank']}`", inline=False)
    embed.add_field(name="〉 afk", value=f"Last Claim: <t:{int(data['lastAFK'])}:R>\nMax Claim Hours: `{data['maxAFK']}`", inline=False)

    embed.set_thumbnail(url=user.display_avatar)
    embed.set_footer(text="Powered by itsb1ng.dev", icon_url=static_response().logo)
    await ctx.respond(embed=embed)

@econ.command(name="balance", description="bingcoin balance")
async def eco_bal(ctx):
    try:
        data = mydb.format_data("economy", mydb.return_row_data("economy", "userID", ctx.author.id))
        embed = discord.Embed(title=ctx.author.name, description=f"Level {economy.current_level(data['spent'])}: {economy.bar_progress(data['spent'])}\n\n**Wallet:** `⌬{data['wallet']:,}`\n**Deposited:** `⌬{data['balance']:,}`/`⌬{economy.bank_balance(data['bank']):,}`", color=static_response().defaultColor)
        embed.set_thumbnail(url=ctx.author.display_avatar)
        embed.set_footer(text="Powered by itsb1ng.dev", icon_url=static_response().logo)
        await ctx.respond(embed=embed)
    except:
        await setup_economy(ctx) 

@econ.command(name="deposit", description="deposit bingcoin into your bank")
async def deposit(ctx, amount:Option(int, "bingcoin to deposit", required=True)):
    try:
        response = economy.depos(ctx.author.id, amount)
        if response['message'] == "success":
            embed = discord.Embed(title=f"{ctx.author.name} deposited ⌬{amount:,}", description=f"Level {economy.current_level(response['spent'])}: {economy.bar_progress(response['spent'])}\n\n**Wallet:** `⌬{response['wallet']:,}`\n**Deposited:** `⌬{response['balance']:,}`/`⌬{economy.bank_balance(response['bank'])}`", color=static_response().defaultColor)
            embed.set_thumbnail(url=ctx.author.display_avatar)
        elif response['message'] == "wait":
            embed = discord.Embed(title=f"Could Not Deposit", description=f"Please Wait: {response['time']}", color=0xC10000)
        elif response['message'] == "invalid amount":
            embed = discord.Embed(title=f"Could Not Deposit", description=f"Invalid Deposit Amount", color=0xC10000)
        embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
        await ctx.respond(embed=embed)
    except:
        await setup_economy(ctx) 

@econ.command(name="withdraw", description="withdraw bingcoin from your bank")
async def withdraw(ctx, amount:Option(int, "bingcoin to withdraw", required=True)):
    try:
        response = economy.withdraw(ctx.author.id, amount)
        if response['message'] == "success":
            embed = discord.Embed(title=f"{ctx.author.name} withdrew ⌬{amount:,}", description=f"Level {economy.current_level(response['spent'])}: {economy.bar_progress(response['spent'])}\n\n**Wallet:** `⌬{response['wallet']:,}`\n**Deposited:** `⌬{response['balance']:,}`/`⌬{economy.bank_balance(response['bank']):,}`", color=static_response().defaultColor)
            embed.set_thumbnail(url=ctx.author.display_avatar)
        elif response['message'] == "invalid amount":
            embed = discord.Embed(title=f"Could Not Withdraw", description=f"Invalid Withdraw Amount", color=0xC10000)
        embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
        await ctx.respond(embed=embed)
    except:
        await setup_economy(ctx)

def sim_embed(ctx, trialsDone, trialsAttempted, totalWagered, finishedMoney, amountper, jp):
    embed = discord.Embed(title=f"{trialsDone:,}/{trialsAttempted:,} Trials", description=f"Outcome: `⌬{int(finishedMoney):,}`/`⌬{int(totalWagered):,}`\nRTP: `{(finishedMoney/totalWagered)*100:.2f}%`\nJackpot: `{(jp/trialsAttempted)*100:.2f}%`", color=static_response().defaultColor)
    embed.set_thumbnail(url=ctx.author.display_avatar)
    embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
    return embed

@econ.command(name="simslot", description="simulate slot odds")
async def simslot(ctx, total_wager:Option(int, "total bingcoin to wager", required=True), trials:Option(int, "amount of trials", required=True), amount_per_trial:Option(int, "amount per trial", required=True)):
    if ctx.channel.id == 1172766197423550474:
        trialsDone = 0
        currentMoney = total_wager
        jp=0
        for i in range(trials):
            if currentMoney <= 0:
                await ctx.respond(embed=sim_embed(ctx, trialsDone, trials, total_wager, currentMoney, amount_per_trial, jp))
                return
            else:
                currentMoney -= amount_per_trial
                slot_result = economy.generate_slot_result()
                checkWin = economy.check_winner(slot_result, amount_per_trial)
                if checkWin[0]:
                    currentMoney += checkWin[1]
                    if checkWin[2] == "100x":
                        jp+=1

                trialsDone += 1

        await ctx.respond(embed=sim_embed(ctx, trialsDone, trials, total_wager, currentMoney, amount_per_trial, jp))
    else:
        await ctx.respond("You cannot execute this command here!")

@econ.command(name="slots", description="roll slots")
async def slot_machine(ctx, amount:Option(int, "bingcoin to wager", required=True)):
    try:
        data = mydb.format_data("economy", mydb.return_row_data("economy", "userID", ctx.author.id))
        if data['wallet'] >= amount:
            mydb.update_row_data("economy", "wallet", data['wallet']-amount, "userID", ctx.author.id)
            await ctx.respond("Rolling...")

            for _ in range(10): 
                rolling_result = economy.generate_slot_result()
                await ctx.edit(content=economy.display_slot_result(rolling_result))
                await asyncio.sleep(0.2)

            slot_result = economy.generate_slot_result()
            await ctx.edit(content=economy.display_slot_result(slot_result))
            checkWin = economy.check_winner(slot_result, amount)
            
            if checkWin[0]:
                mydb.update_row_data("economy", "wallet", data['wallet']+checkWin[0], "userID", ctx.author.id)
                newData = mydb.format_data("economy", mydb.return_row_data("economy", "userID", ctx.author.id))
                embed = discord.Embed(title=f"You won ⌬{int(checkWin[1]):,}", description=f"Level {economy.current_level(newData['spent'])}: {economy.bar_progress(newData['spent'])}\n\n**Wallet:** `⌬{newData['wallet']:,}`", color=static_response().defaultColor)
                embed.set_thumbnail(url=ctx.author.display_avatar)
                embed.set_footer(text="Powered by itsb1ng.dev", icon_url=static_response().logo)
                
            else:
                embed = discord.Embed(title=f"Lost ⌬{amount:,}", color=0xFCC03D)
                embed.set_thumbnail(url=ctx.author.display_avatar)
                embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
            
            await ctx.send_followup(embed=embed)

            add_spent(ctx.author.id, amount)
        else:  
            await ctx.respond(f"You do not have enough bingcoin to spin the slot machine. Check wallet balance")
    except:
        await setup_economy(ctx)

@econ.command(name="leaderboard", description="bingcoin level leaderboard")
async def leaderboard(ctx):
    leaderboardList = []
    unformatted = mydb.db_interact("economy", """SELECT * FROM userdata ORDER BY spent DESC LIMIT 5;""", False)
    for i,v in enumerate(unformatted):
        tempList = []
        tempList.append(v)
        leaderboardList.append(mydb.format_data("economy", tempList))
    embed = discord.Embed(title="bingcoin leaderboard", color=static_response().defaultColor)
    topUser = bot.get_user(leaderboardList[0]['userID'])
    for i, v in enumerate(leaderboardList):
        embed.add_field(name=bot.get_user(v['userID']).name, value=f"Level {economy.current_level(v['spent'])}: {economy.bar_progress(v['spent'])}", inline=False)
    embed.set_thumbnail(url=topUser.display_avatar)
    embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
    await ctx.respond(embed=embed)

@econ.command(name="shop", description="bingcoin shop")
async def econ_shop(ctx):
    
    def embed_response(interaction, selection):
        if selection == "banks":
            bankNum = next((index + 1 for index, (key, value) in enumerate(economy.bank_balance().items()) if key == mydb.format_data("economy", mydb.return_row_data("economy", "userID", interaction.user.id))['bank']), None)
            embed = discord.Embed(title=f"bingcoin shop - bank", description='\n'.join([f'{key} - `⌬{value:,}`' for key, value in list(economy.bank_balance().items())[bankNum:]]) + f"\n\n</eco purchase:1171600418887975033>", color=static_response().defaultColor)
            embed.set_thumbnail(url="https://i.imgur.com/Yxbw92r.png")
            return embed
        elif selection == "upgrades":
            data = mydb.format_data("economy", mydb.return_row_data("economy", "userID", interaction.user.id))
            embed = discord.Embed(title=f"bingcoin shop - upgrades", description=f"+1 Claim Hour: `⌬{economy.next_hour_purchase(data['maxAFK']):,}`\n+5% Robbery Success Rate: `⌬{economy.next_rob_success_purchase(data['robSuccess']):,}`\n+5% Robbery Winnings Rate: `⌬{economy.next_rob_winnings_purchase(data['stealPercent']):,}`\n\n</eco purchase:1171600418887975033>", color=static_response().defaultColor)
            embed.set_thumbnail(url="https://i.imgur.com/vfTjbEG.png")
            return embed

    async def menu_callback(interaction:discord.Interaction):
        if ctx.author.id == interaction.user.id:
            embed = embed_response(interaction, select.values[0])
            embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
            await interaction.response.edit_message(embed=embed)
    
    select = Select(max_values=1, options=[discord.SelectOption(label="banks", emoji="🏦", description="bincoin banks"), discord.SelectOption(label="upgrades", emoji="⬆️", description="bingcoin upgrades")])
    view = View(timeout=20)

    view.add_item(select)
    
    await ctx.respond(view=view)

    select.callback = menu_callback

@econ.command(name="purchase", description="purchase bincoin items")
async def econ_purchase(ctx, bank:Option(str, "bingcoin banks", choices=["Omega Trust", "Azure Bank", "Apex Financial Corp.", "Obelisk Banks Inc.", "Zion Credit Union", "Aegis Banks Inc.", "Caliber Bancorp"])=None, upgrade:Option(str, "bingcoin upgrade", choices=['+1 Claim Hour', '+5% Robbery Success', '+5% Robbery Winnings'])=None):
    if upgrade or bank:
        try:
            data = mydb.format_data("economy", mydb.return_row_data("economy", "userID", ctx.author.id))
            if bank:
                bankPrice = economy.bank_balance(bank)
                if bankPrice <= economy.bank_balance(data['bank']):
                    await ctx.respond(f"You cannot purchase `{bank}`")
                else:
                    if data['wallet'] >= bankPrice:
                        mydb.update_row_data("economy", "wallet", data['wallet']-bankPrice, "userID", ctx.author.id)
                        mydb.update_row_data("economy", "bank", bank, "userID", ctx.author.id)
                        mydb.update_row_data("economy", "spent", bankPrice, "userID", ctx.author.id)
                        newData = mydb.format_data("economy", mydb.return_row_data("economy", "userID", ctx.author.id))
                        embed = discord.Embed(title=f"Successfully purchased {bank} for `⌬{bankPrice:,}`", description=f"Level {economy.current_level(newData['spent'])}: {economy.bar_progress(newData['spent'])}\n\n**Wallet:** `⌬{newData['wallet']:,}`", color=static_response().defaultColor)
                        embed.set_thumbnail(url=ctx.author.display_avatar)
                        embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
                        await ctx.respond(embed=embed)
                    else:  
                        await ctx.respond(f"You do not have enough bingcoin to purchase `{bank}`. Check wallet balance")
            elif upgrade:
                if upgrade == '+1 Claim Hour':
                    upgradeCost = economy.next_hour_purchase(data['maxAFK'])
                    addition = 1
                    whatAdded = "maxAFK"
                    name = "Claim Hours"
                    
                elif upgrade == '+5% Robbery Success':
                    upgradeCost = economy.next_rob_success_purchase(data['robSuccess'])
                    addition = 5
                    whatAdded = "robSuccess"
                    name = "Robbery Success"

                elif upgrade == "+5% Robbery Winnings":
                    upgradeCost = economy.next_rob_winnings_purchase(data['stealPercent'])
                    addition = 5
                    whatAdded = "stealPercent"
                    name = "Robbery Winnings"

                if data['wallet'] >= upgradeCost:
                    mydb.update_row_data("economy", "wallet", data['wallet']-upgradeCost, "userID", ctx.author.id)
                    mydb.update_row_data("economy", whatAdded, data[whatAdded]+addition, "userID", ctx.author.id)
                    mydb.update_row_data("economy", "spent", upgradeCost, "userID", ctx.author.id)
                    newData = mydb.format_data("economy", mydb.return_row_data("economy", "userID", ctx.author.id))
                    embed = discord.Embed(title=f"Successfully added +{addition}{'%' if addition > 1 else ''} for `⌬{upgradeCost:,}`", description=f"Level {economy.current_level(newData['spent'])}: {economy.bar_progress(newData['spent'])}\n\n**Wallet:** `⌬{newData['wallet']:,}`\n{name}: `{newData[whatAdded]}{'%' if addition > 1 else ''}`", color=static_response().defaultColor)
                    embed.set_thumbnail(url=ctx.author.display_avatar)
                    embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
                else:  
                    await ctx.respond(f"You do not have enough bingcoin to purchase `{upgrade}`. Check wallet balance")
        except:
            await setup_economy(ctx)
    else:
        await ctx.respond("Please provide a parameter")

@econ.command(name="rob", description="rob a user from bingcoin")
async def rob_user(ctx, user:Option(discord.Member, "user to rob bingcoin from", required=True)):
    try:
        data = mydb.format_data("economy", mydb.return_row_data("economy", "userID", ctx.author.id))
        victimData = mydb.format_data("economy", mydb.return_row_data("economy", "userID", user.id))

        if data['userID'] == victimData['userID']:
            await ctx.respond(f"You cannot rob yourself")
        else:
            afkTime = time.time() - data['lastRob']

            timeSince = afkTime / 3600
            if timeSince >= 3:
                if random.randint(1,100) <= data['robSuccess']:
                    winnings = int(victimData['stealPercent'] * victimData['wallet'])
                    mydb.update_row_data("economy", "wallet", data['wallet']-winnings, "userID", user.id)
                    mydb.update_row_data("economy", "wallet", data['wallet']+winnings, "userID", ctx.author.id)

                    embed = discord.Embed(title="Successful Robbery", description=f"Level {economy.current_level(data['spent'])}: {economy.bar_progress(data['spent'])}\n\nWallet: `⌬{winnings+data['wallet']:,}`\nWinnings: `⌬{winnings:,}`\nTarget: {user.mention}\nPercent Chance: `{data['robSuccess']}%`", color=static_response().defaultColor)
                else:
                    embed = discord.Embed(title="Failed to Rob", description=f"Target: {user.mention}\nPercent Chance: `{data['robSuccess']}%`", color=0xC10000)
                
                mydb.update_row_data("economy", "lastRob", time.time(), "userID", ctx.author.id)
            else:
                timeTil = f"<t:{int(data['lastRob']+10800)}:R>"
                embed = discord.Embed(title=f"Could Not Rob", description=f"Please Wait: {timeTil}", color=0xFCC03D)

            embed.set_footer(text=static_response().sponsor, icon_url=static_response().logo)
            await ctx.respond(embed=embed)
    except:
        await setup_economy(ctx)

bot.add_application_command(giveaw) 
bot.add_application_command(hibp)
bot.add_application_command(econ)

bot.run(static_response().token)