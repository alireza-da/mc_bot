from datetime import datetime, timedelta
from dateutil import tz

import discord

from_zone = tz.tzutc()
to_zone = tz.tzlocal()


async def read_off_on_duty_notifs(guild):
    channel = guild.get_channel(807366748118319224)
    messages = await channel.history().flatten()
    for message in messages:
        print(message.content)

    return messages


async def read_off_duties(channel):
    messages = await channel.history(limit=200).flatten()
    for message in messages:
        # print(message)
        if message.author.id == 765915730171920465:
            messages.remove(message)

    return messages[0:len(messages)-1]


async def delete_old_messages(messages):
    current_dt = datetime.now(tz=to_zone)
    three_hrs = timedelta(hours=3)
    for message in messages:
        utc = message.created_at.replace(tzinfo=from_zone)
        central = utc.astimezone(to_zone)

        diff = current_dt - central
        if diff > three_hrs:
            await message.delete()


async def create_embed_template(channel):
    messages = await channel.history(limit=200).flatten()
    if len(messages) > 0 and messages[-1].author.id == 936315743216218203:
        return
    embed_var = discord.Embed(title="Off Duty Submission Form", description=":capital_abcd: IC Name:\n:tools: MC Rank:\n:watch: "
                                                                            "Required Time: ",
                              color=discord.Colour(0xFFFF00))
    await channel.send(embed=embed_var)


async def send_dm(member: discord.Member, *, content):
    channel = await member.create_dm()
    await channel.send(content)


async def get_on_duty_notif(messages, user_id):
    msg_dict = {msg: msg.author.id for msg in messages}
    # print(msg_dict)
    result = []
    for ms in msg_dict:
        if "on duty" in ms.content.lower():
            # print(ms)
            result.append(ms)
    return result
