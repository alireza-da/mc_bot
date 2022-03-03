import threading

import discord
import asyncio

from functools import partial
from credentials import bot_token, sunset_sv_status_msg_link
from discord.ext import commands
from utils import retrieve_sv_status
from concurrent.futures import ProcessPoolExecutor
from discord.utils import get

intents = discord.Intents.all()
intents.members = True
client = commands.Bot(command_prefix='$', intents=intents)
# loop = asyncio.get_event_loop()
pool_executor = ProcessPoolExecutor(2)

bot_test_channel = None
sv_status_msg = None


@client.event
async def on_ready():
    print(f"Logged In as {client.user}")
    emojis = client.emojis
    emojis = {e.name: str(e) for e in emojis}
    # print(emojis)
    mhkn_guild = client.get_guild(869221659733807125)
    mc_guild = client.get_guild(798587846859423744)
    # print(mc_guild.roles)
    # print(mhkn_guild.roles)
    sv_status_channel = await get_server_status_channel(mc_guild)

    global bot_test_channel
    bot_test_channel = mhkn_guild.get_channel(936566301994942464)
    # creating a reactive sunset server status message
    embed_args = retrieve_sv_status()
    embed_sv_status = discord.Embed(type='rich', description=embed_args['description']
                                    .replace("<:SSMD:830878795602591774>", emojis["SSMD"])
                                    .replace("<:SSSD:830877171924336650>", emojis["SSSD"])
                                    .replace("<:SSMC:831502019537534997>", emojis["SSMC"])
                                    .replace(":SSTD:", emojis["SSTD"])
                                    .replace("<a:SSverify_black:807340739721166919>", emojis["SSverify_black"])
                                    .replace("<a:SSload:794664822607970324>", emojis["SSload"])
                                    , color=embed_args['color'])
    embed_sv_status.set_footer(text=embed_args['footer']['text'], icon_url=embed_args['footer']['icon_url'])
    await sv_status_channel.purge(limit=10)
    # await sv_status_msg.edit(embed=embed_sv_status)
    global sv_status_msg
    sv_status_msg = await sv_status_channel.send(embed=embed_sv_status)

    def between_callback():
        asyncio.run_coroutine_threadsafe(update_sv_status_message(emojis, bot_test_channel, sv_status_msg), client.loop)

    _thread = threading.Thread(target=between_callback)
    _thread.start()

    # creating a reactive mechanic department message
    mc_dept_embed = discord.Embed(type='rich', description="Mechanic Department Staff Status",
                                  color=discord.Colour(0xFFFF00))
    counter = count_employees(mc_guild)

    mc_dept_embed.add_field(name=f":Chief: Chief: {counter['chief_cnt']}".replace(":Chief:", emojis["Chief"]),
                            value=f":green_circle:  Online: {counter['on_chief_cnt']} "
                                  f"| :red_circle:  Offline: {counter['off_chief_cnt']}", inline=False)
    mc_dept_embed.add_field(
        name=f":Deputy: Deputy Chief: {counter['dep_chief_cnt']}".replace(":Deputy:", emojis["Deputy"]),
        value=f":green_circle:  Online: {counter['on_dep_chief_cnt']} "
              f"| :red_circle:  Offline: {counter['off_dep_chief_cnt']}", inline=False)
    mc_dept_embed.add_field(
        name=f":Managment: Management: {counter['mng_cnt']}".replace(":Managment:", emojis["Managment"]),
        value=f":green_circle:  Online: {counter['mng_on_cnt']} "
              f"| :red_circle:  Offline: {counter['mng_off_cnt']}", inline=False)
    mc_dept_embed.add_field(
        name=f":supervisor: Supervisor: {counter['supervisor_cnt']}".replace(":supervisor:", emojis["supervisor"]),
        value=f":green_circle:  Online: {counter['supervisor_on_cnt']} "
              f"| :red_circle:  Offline: {counter['supervisor_off_cnt']}", inline=False)
    mc_dept_embed.add_field(name=f":FT: Field Training: {counter['ft_cnt']}".replace(":FT:", emojis["FT"]),
                            value=f":green_circle:  Online: {counter['ft_on_cnt']} "
                                  f"| :red_circle:  Offline: {counter['ft_off_cnt']}", inline=False)
    mc_dept_embed.add_field(name=f":HR: Human Resource: {counter['hr_cnt']}".replace(":HR:", emojis["HR"]),
                            value=f":green_circle:  Online: {counter['hr_on_cnt']} "
                                  f"| :red_circle:  Offline: {counter['hr_off_cnt']}", inline=False)
    mc_dept_embed.add_field(name=f":Pilot: Pilot Team: {counter['pt_cnt']}".replace(":Pilot:", emojis["Pilot"]),
                            value=f":green_circle:  Online: {counter['pt_on_cnt']} "
                                  f"| :red_circle:  Offline: {counter['pt_off_cnt']}", inline=False)

    mc_dept_embed.add_field(
        name=f":SSMC: Total number of employees : {counter['emp_counter']}".replace(":SSMC:", emojis['SSMC']),
        value=f":green_circle: Online: {counter['emp_on_counter']} | "
              f":red_circle:  Offline: {counter['emp_off_counter']} | "
              f":zzz: Away(AFK): {counter['emp_counter'] - counter['emp_on_counter'] - counter['emp_off_counter']}")
    mc_status_msg = await sv_status_channel.send(embed=mc_dept_embed)

    def between_callback2():
        asyncio.run_coroutine_threadsafe(update_mc_status_message(emojis, mc_guild, mc_status_msg), client.loop)

    _thread2 = threading.Thread(target=between_callback2)
    _thread2.start()


def find_emoji(emojies, name):
    for emoji in emojies:
        if emoji.name == name:
            return emoji


async def get_server_status_channel(guild):
    sv_status_ch = guild.get_channel(948744917075787816)
    # print(sv_status_ch)
    # await sv_status_ch.delete()
    # sv_status_ch = None
    if sv_status_ch:
        return sv_status_ch
    # else:
    #     channel = await guild.create_text_channel(":bar_chart:|Server-Status")
    #     await channel.set_permissions(guild.default_role, send_messages=False)
    #     # chief_role = get(guild.roles, id=798587846868860965)
    #     # await channel.set_permissions(chief_role, send_messages=True)
    #     mc_bot_role = get(guild.roles, id=948398272790294631)
    #     await channel.set_permissions(mc_bot_role, send_messages=True)
    #     print(channel.id)
    #     return channel


def count_employees(guild):
    counter = {"emp_counter": 0, "emp_off_counter": 0, "emp_on_counter": 0,
               "chief_cnt": 0, "on_chief_cnt": 0, "off_chief_cnt": 0,
               "dep_chief_cnt": 0, "off_dep_chief_cnt": 0, 'on_dep_chief_cnt': 0,
               "ft_cnt": 0, "ft_off_cnt": 0, "ft_on_cnt": 0,
               "hr_cnt": 0, "hr_off_cnt": 0, "hr_on_cnt": 0,
               "pt_cnt": 0, "pt_off_cnt": 0, "pt_on_cnt": 0,
               "mng_cnt": 0, "mng_off_cnt": 0, "mng_on_cnt": 0,
               "supervisor_cnt": 0, "supervisor_off_cnt": 0, "supervisor_on_cnt": 0,
               }
    role_ids = [r.id for r in guild.roles]
    # print(role_ids)
    # 903912198064177154 "employee role id"
    for member in guild.members:
        role_ids = [r.id for r in member.roles]
        # employees
        # if 903912198064177154 in role_ids:
        #     counter["emp_counter"] += 1
        #     if member.status == discord.Status.offline:
        #         counter["emp_off_counter"] += 1
        #     elif member.status != discord.Status.idle:
        #         counter["emp_on_counter"] += 1
        # chiefs
        if 798587846868860965 in role_ids:
            counter["chief_cnt"] += 1
            if member.status == discord.Status.offline:
                counter["off_chief_cnt"] += 1
            elif member.status != discord.Status.idle:
                counter["on_chief_cnt"] += 1
        # deputy chief
        if 903940304749600768 in role_ids:
            counter["dep_chief_cnt"] += 1
            if member.status == discord.Status.offline:
                counter["off_dep_chief_cnt"] += 1
            elif member.status != discord.Status.idle:
                counter["on_dep_chief_cnt"] += 1
        # management
        if 798587846868860960 in role_ids:
            counter["mng_cnt"] += 1
            if member.status == discord.Status.offline:
                counter["mng_off_cnt"] += 1
            elif member.status != discord.Status.idle:
                counter["mng_on_cnt"] += 1
        # supervisor
        if 922137155134955530 in role_ids:
            counter["ft_cnt"] += 1
            if member.status == discord.Status.offline:
                counter["ft_off_cnt"] += 1
            elif member.status != discord.Status.idle:
                counter["ft_on_cnt"] += 1
        if 922146024275992617 in role_ids:
            counter["hr_cnt"] += 1
            if member.status == discord.Status.offline:
                counter["hr_off_cnt"] += 1
            elif member.status != discord.Status.idle:
                counter["hr_on_cnt"] += 1
        if 864950920051425351 in role_ids:
            counter["pt_cnt"] += 1
            if member.status == discord.Status.offline:
                counter["pt_off_cnt"] += 1
            elif member.status != discord.Status.idle:
                counter["pt_on_cnt"] += 1

        # employees deleted , mechanic department 842695874668003328
        if 842695874668003328 in role_ids:
            counter["emp_counter"] += 1
            if member.status == discord.Status.offline:
                counter["emp_off_counter"] += 1
            elif member.status != discord.Status.idle:
                counter["emp_on_counter"] += 1

        if 903913968979038209 in role_ids:
            counter["supervisor_cnt"] += 1
            if member.status == discord.Status.offline:
                counter["supervisor_off_cnt"] += 1
            elif member.status != discord.Status.idle:
                counter["supervisor_on_cnt"] += 1

    return counter


async def update_sv_status_message(emojis, channel, message):
    while True:
        embed_args = retrieve_sv_status()
        embed_sv_status = discord.Embed(type='rich', description=embed_args['description'], color=embed_args['color'])
        embed_sv_status.set_footer(text=embed_args['footer']['text'], icon_url=embed_args['footer']['icon_url'])
        # if channel.last_message.embeds[0].description == embed_sv_status.description:
        #     continue
        try:
            # print(channel.last_message.embeds[0].description, message)
            await asyncio.sleep(5)
            embed_args = retrieve_sv_status()
            embed_sv_status = discord.Embed(type='rich', description=embed_args['description']
                                            .replace("<:SSMD:830878795602591774>", emojis["SSMD"])
                                            .replace("<:SSSD:830877171924336650>", emojis["SSSD"])
                                            .replace("<:SSMC:831502019537534997>", emojis["SSMC"])
                                            .replace(":SSTD:", emojis["SSTD"])
                                            .replace("<a:SSverify_black:807340739721166919>", emojis["SSverify_black"])
                                            .replace("<a:SSload:794664822607970324>", emojis["SSload"]),

                                            color=embed_args['color'])
            embed_sv_status.set_footer(text=embed_args['footer']['text'], icon_url=embed_args['footer']['icon_url'])
            # await channel.purge(limit=1)
            await message.edit(embed=embed_sv_status)
        except Exception as e:
            print(f"Error: {e}")


async def update_mc_status_message(emojis, guild, message):
    while True:
        await asyncio.sleep(5)
        mc_dept_embed = discord.Embed(type='rich', description="Mechanic Department Staff Status",
                                      color=discord.Colour(0xFFFF00))
        counter = count_employees(guild)

        mc_dept_embed.add_field(name=f":Chief: Chief: {counter['chief_cnt']}".replace(":Chief:", emojis["Chief"]),
                                value=f":green_circle:  Online: {counter['on_chief_cnt']} "
                                      f"| :red_circle:  Offline: {counter['off_chief_cnt']}", inline=False)
        mc_dept_embed.add_field(
            name=f":Deputy: Deputy Chief: {counter['dep_chief_cnt']}".replace(":Deputy:", emojis["Deputy"]),
            value=f":green_circle:  Online: {counter['on_dep_chief_cnt']} "
                  f"| :red_circle:  Offline: {counter['off_dep_chief_cnt']}", inline=False)
        mc_dept_embed.add_field(
            name=f":Managment: Management: {counter['mng_cnt']}".replace(":Managment:", emojis["Managment"]),
            value=f":green_circle:  Online: {counter['mng_on_cnt']} "
                  f"| :red_circle:  Offline: {counter['mng_off_cnt']}", inline=False)
        mc_dept_embed.add_field(
            name=f":supervisor: Supervisor: {counter['supervisor_cnt']}".replace(":supervisor:", emojis["supervisor"]),
            value=f":green_circle:  Online: {counter['supervisor_on_cnt']} "
                  f"| :red_circle:  Offline: {counter['supervisor_off_cnt']}", inline=False)
        mc_dept_embed.add_field(name=f":FT: Field Training: {counter['ft_cnt']}".replace(":FT:", emojis["FT"]),
                                value=f":green_circle:  Online: {counter['ft_on_cnt']} "
                                      f"| :red_circle:  Offline: {counter['ft_off_cnt']}", inline=False)
        mc_dept_embed.add_field(name=f":HR: Human Resource: {counter['hr_cnt']}".replace(":HR:", emojis["HR"]),
                                value=f":green_circle:  Online: {counter['hr_on_cnt']} "
                                      f"| :red_circle:  Offline: {counter['hr_off_cnt']}", inline=False)
        mc_dept_embed.add_field(name=f":Pilot: Pilot Team: {counter['pt_cnt']}".replace(":Pilot:", emojis["Pilot"]),
                                value=f":green_circle:  Online: {counter['pt_on_cnt']} "
                                      f"| :red_circle:  Offline: {counter['pt_off_cnt']}", inline=False)

        mc_dept_embed.add_field(
            name=f":SSMC: Total number of employees : {counter['emp_counter']}".replace(":SSMC:", emojis['SSMC']),
            value=f":green_circle: Online: {counter['emp_on_counter']} | "
                  f":red_circle:  Offline: {counter['emp_off_counter']} | "
                  f":zzz: Away(AFK): {counter['emp_counter'] - counter['emp_on_counter'] - counter['emp_off_counter']}")
        await message.edit(embed=mc_dept_embed)


client.run(bot_token)
