import time
import random
import libs.database as mydb
import math

def current_level(xp):
    return math.floor(xp**(1./3.))

def xp_for_next_level(level):
    return (level+1)**3-level ** 3

def current_level_xp(level):
    return level ** 3

def prev_level_next_level(level):
    return level ** 3 - (level-1) **3

def next_level_xp(level):
    return (level+1) **3

def level_progress(xp):
    return round((xp - current_level_xp(current_level(xp))) / (next_level_xp(current_level(xp)) - current_level_xp(current_level(xp))), 2)

def bar_progress(xp):
    completionSymbols = []

    empty = "▒"
    full = "█"
    
    bars = int(level_progress(xp) * 10)
    for i in range(bars):
        completionSymbols.append(full)
    for x in range(10-bars):
        completionSymbols.append(empty)

    return ''.join(completionSymbols)

def get_claim(level, hour):
    return math.ceil(((level / 3) **3) * hour)

def next_rob_success_purchase(percent):
    return int(5000 * (1.3*(0.2*((percent-20)//5))) ** ((percent-20)//5))

def next_rob_winnings_purchase(percent):
    return int(9000 * (1.5*(0.25*((percent-20)//5))) ** ((percent-20)//5))

def next_hour_purchase(time):
    return int(7500 * (1 + 1.64) ** (time-12))

def claim(userID):
    userData = mydb.format_data("economy", mydb.return_row_data("economy", "userID", userID))
    afkTime = time.time() - userData['lastAFK']

    afkTime /= 3600

    if afkTime > userData['maxAFK']:
        afkTime = userData['maxAFK']
    else:
        afkTime = afkTime

    newMoney = get_claim(current_level(userData['spent']), afkTime)
    mydb.update_row_data("economy", "wallet", userData['wallet'] + newMoney, "userID", userID)
    mydb.update_row_data("economy", "lastAFK", time.time(), "userID", userID)
    return {"money": newMoney, "wallet": userData['wallet'], "afk": afkTime}

def emoji_choice(bot):
    return random.choice([bot.get_emoji(1171596643532021810), bot.get_emoji(1171596668592996433), bot.get_emoji(1171596805507649546), bot.get_emoji(1171596823249571840), bot.get_emoji(1171596837170454528), bot.get_emoji(1171596837170454528)])

def roll_dice(bot):
    emojiValues = {"dice_one": 1, "dice_two": 2, "dice_three": 3, "dice_four": 4, "dice_five": 5, "dice_six": 6}
    dice = []
    
    for i in range(4):
        emoji = emoji_choice(bot)
        dice.append((emoji, emojiValues[emoji.name]))

    userDice = dice[0][1] + dice[1][1]
    botDice = dice[2][1] + dice[3][1]

    return dice, userDice, botDice

def bank_balance(bank=None):
    banks = {"United Financial Inc.": 750, "Omega Trust": 1750, "Azure Bank": 4000, "Apex Financial Corp.": 10000, "Obelisk Banks Inc.": 25000, "Zion Credit Union": 75000, "Aegis Banks Inc.": 150000, "Caliber Bancorp": 275000}
    if bank:
        return banks[bank]
    else:
        return banks
    
def depos(userID, depo):
    data = mydb.format_data("economy", mydb.return_row_data("economy", "userID", userID))
    if depo < data['wallet']:
        maxBal = bank_balance(data['bank'])
        afkTime = time.time() - data['depoTime']

        timeSince = afkTime / 60

        if timeSince > 5:
            if depo+data['balance'] > maxBal:
                depositAmount = maxBal
                walletAmount = (data['wallet']-depo) + (depo+data['balance']-maxBal)
            else:
                depositAmount = depo+data['balance']
                walletAmount = data['wallet']-depo

            mydb.update_row_data("economy", "balance", depositAmount, "userID", userID)
            mydb.update_row_data("economy", "wallet", walletAmount, "userID", userID)
            mydb.update_row_data("economy", "depoTime", time.time(), "userID", userID)

            return {"message": "success", "wallet": walletAmount, "balance": depositAmount, "maxBal": maxBal, "spent": data['spent'], "bank": data['bank']}
    
        else:
            return {"message": "wait", "time": f"<t:{int(data['depoTime']+300)}:R>"}
    else:
        return {"message": "invalid amount"}
    
def withdraw(userID, withd):
    data = mydb.format_data("economy", mydb.return_row_data("economy", "userID", userID))
    if withd <= data['balance']:
        maxBal = bank_balance(data['bank'])

        mydb.update_row_data("economy", "balance", data['balance']-withd, "userID", userID)
        mydb.update_row_data("economy", "wallet", data['wallet']+withd, "userID", userID)

        return {"message": "success", "wallet": data['wallet']+withd, "balance": data['balance']-withd, "maxBal": maxBal, "spent": data['spent'], "bank": data['bank']}
    else:
        return {"message": "invalid amount"}
    
def generate_slot_result():
    emojis = {'🪙': 30, '💵': 60, '💰': 80, '🎰': 95, '💎': 100}
    choices = []
    for _ in range(9):
        number = random.randint(0,100)
        for item, percent_chance in emojis.items():
            if number <= percent_chance:
                choices.append(item)
                break
    return choices

def return_slot_value(emoji, amount):
    emojiValues = {'🪙': amount*.5, '💵': amount*1.5, '💰': amount*5, '🎰': amount*7, '💎': amount*100}
    multiplier = {'🪙': .5, '💵': 1.5, '💰': 5, '🎰': 7, '💎': 100}
    return emojiValues[emoji], f"{multiplier[emoji]}x"

def display_slot_result(result):
    result_string = ""
    for i in range(0, 9, 3):
        result_string += " ".join(result[i:i+3]) + "\n"
    return result_string

def check_winner(result, amount):
    for i in range(0, 9, 3):
        if result[i] == result[i+1] == result[i+2]:
            value = return_slot_value(result[i], amount)
            return True, value[0], value[1]

    if result[0] == result[4] == result[8]:
        value = return_slot_value(result[0], amount)
        return True, value[0], value[1]
    
    elif result[2] == result[4] == result[6]:
        value = return_slot_value(result[2], amount)
        return True, value[0], value[1]
    
    elif result[0] == result[4] == result[8]:
        value = return_slot_value(result[0], amount)
        return True, value[0], value[1]
        
    return (False, 0)  