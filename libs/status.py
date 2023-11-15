import discord
import asyncio
import libs.database as mydb

async def status_task(bot):
    while True:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"/eco leaderboard"), status=discord.Status.dnd)
        await asyncio.sleep(20)

        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"with bingcoin"), status=discord.Status.dnd)
        await asyncio.sleep(20)

        user = bot.get_user(mydb.format_data("economy", mydb.db_interact("economy", """SELECT * FROM userdata ORDER BY spent DESC LIMIT 1;""", False))['userID'])
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{user.name} win big"), status=discord.Status.dnd)
        await asyncio.sleep(20)
        