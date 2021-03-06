import asyncio
import functools
import threading
import typing
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta

import discord
import discord_slash
from discord.ext import commands
from discord.utils import get
from discord_slash import SlashCommand, SlashContext

from backend import keep_alive
from credentials import bot_token, mc_bot_id, three_stars_role_id, two_stars_role_id, one_star_role_id, management_role_id, supervisor_role_id, warn_role_id
from model import MechanicEmployee, Punishment
from notification_handler import read_off_duties, delete_old_messages, create_embed_template, delete_warn_2_weeks, \
    send_lobby_dm, on_star_role_add, get_rank_up_managers, get_gang_employee, get_chiefs
from setup_db import setup_tables, get_user, update_mc, save_punish, get_punishments, del_punishments
from utils import retrieve_sv_status
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle

intents = discord.Intents.all()
intents.members = True
client = commands.Bot(command_prefix='$', intents=intents)
slash = SlashCommand(client, sync_commands=True)
# loop = asyncio.get_event_loop()
pool_executor = ProcessPoolExecutor(2)

bot_test_channel = None
sv_status_msg = None
guild_ids = [869221659733807125, 798587846859423744]


async def non_blocking_data_insertion(blocking_func: typing.Callable, *args, **kwargs) -> typing.Any:
    func = functools.partial(blocking_func, *args, **kwargs)
    return await client.loop.run_in_executor(None, func)


@client.event
async def on_ready():
    print(f"Logged In as {client.user}")

    # try:
    #     ids = "https: // discord.com / channels / 747051409400397894 / 926148025007607908 / 926230250088697867".split(
    #         "/")
    #     sv_msg = await client.get_guild(int(ids[-3])).get_channel(int(ids[-2])).history().flatten()
    # except Exception as e:
    #     print(e)
    # print(sv_msg)
    emojis = client.emojis
    emojis = {e.name: str(e) for e in emojis}
    # print(emojis)
    mhkn_guild = client.get_guild(869221659733807125)
    mc_guild = client.get_guild(798587846859423744)

    # deksy = get(mc_guild.members, id=583223852641812499)
    # channel = await deksy.create_dm()
    # await channel.send("Bot is alive!")
    # punishes = mc_guild.get_channel(866287973627985920)
    # punishes = await punishes.history().flatten()
    # for punish in punishes:
    #     # print(punish.content)
    #     if "remove" in punish.content and "strike" in punish.content:
    #         if len(get_punishments(punish.mentions[0].id)) > 0:
    #             last_punish = get_punishments(punish.mentions[0].id)[0]
    #             del_punishments(last_punish.em_id, last_punish.date, Punishment.STRIKE)
    #         continue
    #     elif "remove" in punish.content and "warn" in punish.content:
    #         if len(get_punishments(punish.mentions[0].id)) > 0:
    #             last_punish = get_punishments(punish.mentions[0].id)[0]
    #             del_punishments(last_punish.em_id, last_punish.date, Punishment.WARN)
    #         continue
    #     if "strike" in punish.content:
    #         save_punish(Punishment(Punishment.STRIKE, punish.created_at, punish.mentions[0].id))
    #         continue
    #     elif "warn" in punish.content:
    #         save_punish(Punishment(Punishment.WARN, punish.created_at, punish.mentions[0].id))

    # print(mc_guild.roles)
    sv_status_channel = await get_server_status_channel(mc_guild)

    global bot_test_channel
    bot_test_channel = mhkn_guild.get_channel(936566301994942464)
    # creating a reactive sunset server status message`
    embed_args = retrieve_sv_status()
    embed_sv_status = discord.Embed(type='rich', description=embed_args['description']
                                    .replace("<:SSMD:830878795602591774>", emojis["SSMD"])
                                    .replace("<:SSSD:830877171924336650>", emojis["SSSD"])
                                    .replace("<:SSMC:831502019537534997>", emojis["SSMC"])
                                    .replace("<:SSTX:943853533466349628>", emojis["SSTD"])
                                    .replace("<a:SSverify_black:807340739721166919>", emojis["SSverify_black"])
                                    .replace("<a:SSload:794664822607970324>", emojis["SSload"])
                                    , color=embed_args['color'])
    embed_sv_status.set_footer(text=embed_args['footer']['text'], icon_url=embed_args['footer']['icon_url'])
    await sv_status_channel.purge(limit=10)
    # await sv_status_msg.edit(embed=embed_sv_status)
    global sv_status_msg
    sv_status_msg = await sv_status_channel.send(embed=embed_sv_status)

    def between_callback():
        asyncio.run_coroutine_threadsafe(update_sv_status_message(emojis, sv_status_msg), client.loop)

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

    def between_callback_off_notif():
        asyncio.run_coroutine_threadsafe(send_off_duty_notifs(mc_guild), client.loop)

    _thread3 = threading.Thread(target=between_callback_off_notif)
    _thread3.start()

    # def between_callback_old_warns():
    #     asyncio.run_coroutine_threadsafe(delete_warn_2_weeks(mc_guild.get_channel(866287973627985920)), client.loop)
    #
    # _thread4 = threading.Thread(target=between_callback_old_warns())
    # _thread4.start()

    await non_blocking_data_insertion(setup_tables, await create_mc_from_discord(mc_guild))


def find_emoji(emojis, name):
    for emoji in emojis:
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
    # role_ids = [r.id for r in guild.roles]
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


async def update_sv_status_message(emojis, message):
    while True:
        await asyncio.sleep(30)
        embed_args = retrieve_sv_status()
        embed_sv_status = discord.Embed(type='rich', description=embed_args['description'], color=embed_args['color'])
        embed_sv_status.set_footer(text=embed_args['footer']['text'], icon_url=embed_args['footer']['icon_url'])
        # if channel.last_message.embeds[0].description == embed_sv_status.description:
        #     continue
        try:
            # print(channel.last_message.embeds[0].description, message)

            embed_args = retrieve_sv_status()
            embed_sv_status = discord.Embed(type='rich', description=embed_args['description']
                                            .replace("<:SSMD:830878795602591774>", emojis["SSMD"])
                                            .replace("<:SSSD:830877171924336650>", emojis["SSSD"])
                                            .replace("<:SSMC:831502019537534997>", emojis["SSMC"])
                                            .replace("<:SSTX:943853533466349628>", emojis["SSTD"])
                                            .replace("<a:SSverify_black:807340739721166919>", emojis["SSverify_black"])
                                            .replace("<a:SSload:794664822607970324>", emojis["SSload"]),

                                            color=embed_args['color'])
            embed_sv_status.set_footer(text=embed_args['footer']['text'], icon_url=embed_args['footer']['icon_url'])
            # await channel.purge(limit=1)
            await message.edit(embed=embed_sv_status)
        except Exception as e:
            print(f"Error while retrieving message: {e}")


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
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f" "
                                                                                                        f"{counter['emp_on_counter']} Mechanics"))


async def send_off_duty_notifs(guild):
    # off duty channel link : https://discord.com/channels/798587846859423744/921891073700274269
    off_duty_channel = guild.get_channel(921891073700274269)
    punish_channel = guild.get_channel(866287973627985920)

    while True:
        await asyncio.sleep(5)
        messages = await read_off_duties(off_duty_channel)
        await create_embed_template(off_duty_channel)
        await delete_old_messages(messages)
        await delete_non_bot_messages(punish_channel)
        await send_lobby_dm(guild)
        await delete_warn_2_weeks(punish_channel)
        # await on_star_role_add(guild)
        # await send_interview_dm(guild)
        # await read_off_on_duty_notifs(guild)


@client.event
async def on_message(message: discord.Message):
    try:
        channel = message.guild.get_channel(921891073700274269)
        messages = await read_off_duties(channel)
        await delete_old_messages(messages)
    except Exception as e:
        print(e)

    if message.author != client.user:
        # off duty channel
        if message.channel.id == 921891073700274269:
            if "ic name" in message.content.lower():
                emojis = client.emojis
                emojis = {e.name: str(e) for e in emojis}
                await message.add_reaction(":Accept:".replace(":Accept:", emojis["Accept"]))
                await message.add_reaction(":Decline:".replace(":Decline:", emojis["Decline"]))
        await client.process_commands(message)


@client.event
async def on_reaction_add(reaction, user):
    emojis = client.emojis
    emojis = {e.name: str(e) for e in emojis}
    role_ids = [r.id for r in user.roles]
    if user != client.user:
        if str(reaction.emoji) == emojis["Accept"] and reaction.message.channel.id == 921891073700274269:
            # management supervisor rank6 chief deputy
            if 798587846868860960 in role_ids or 922137155134955530 in role_ids or 812998810397442109 in role_ids \
                    or 798587846868860965 in role_ids or 903940304749600768 in role_ids \
                    or role_ids.__contains__(903913968979038209):
                await reaction.message.reply(
                    f"<@{reaction.message.author.id}> Your off duty permission granted by <@{user.id}>")
                return
            else:
                await reaction.remove(user)
        elif str(reaction.emoji) == emojis["Decline"] and reaction.message.channel.id == 921891073700274269:
            if 798587846868860960 in role_ids or 922137155134955530 in role_ids or 812998810397442109 in role_ids \
                    or 798587846868860965 in role_ids or 903940304749600768 in role_ids or role_ids.__contains__(
                903913968979038209):
                await reaction.message.reply(
                    f"<@{reaction.message.author.id}> Your off duty permission declined by <@{user.id}>")
                return
            else:
                await reaction.remove(user)


@slash.slash(name="warn",
             description="This is a warn command.",
             guild_ids=guild_ids,
             )
async def warn(ctx: SlashContext, employee, reason):
    role_ids = [r.id for r in ctx.author.roles]
    emojis = client.emojis
    emojis = {e.name: str(e) for e in emojis}
    _id = int(employee.split("!")[1].replace(">", ""))
    mc_guild = client.get_guild(798587846859423744)
    roles = get_ranks_roles_by_id(mc_guild)
    strike_roles = {1: roles[798587846859423749], 2: roles[798587846859423750], 3: roles[798587846859423751]}
    # supervisor and management
    if 922137155134955530 in role_ids or 798587846868860960 in role_ids or 812998810397442109 in role_ids \
            or 798587846868860965 in role_ids or 903940304749600768 in role_ids or \
            role_ids.__contains__(903913968979038209) or 903913968979038209 in role_ids:
        await ctx.send(
            content=f"{employee}. Shoma be dalile: {reason}, warn gereftid :warn:".replace(":warn:", emojis["warn"]))
        mc = get_user(_id)
        mc.warns += 1
        if mc.warns == 2:
            mc.warns = 0
            punishes = get_punishments(_id)

            for p in punishes:
                if mc.warns == 0:
                    break
                if p.punish_type == Punishment.WARN:
                    del_punishments(_id, p.date, p.punish_type)
                    mc.warns -= 1

            if mc.strikes < 3:
                mc.strikes += 1
                await ctx.send(
                    content=f"**{employee}. Shoma be dalile: gereftan 2 warn, strike gereftid** :strike:".replace(
                        ":strike:",
                        emojis["strikes"]))

                ps = Punishment(Punishment.STRIKE, datetime.now(), _id)
                save_punish(ps)
                user = get(client.get_all_members(), id=_id)
                await user.add_roles(strike_roles[mc.strikes])
                await user.remove_roles(roles[warn_role_id])
                update_mc(mc)
            if mc.strikes == 3:
                await ctx.send(
                    content=f"**{employee}. Shoma be dalile dashtan 3 strike fire shodid,"
                            f" dar soorat dashtan har goone eteraz be Management payam bedahid**")
                # ps = Punishment(Punishment.STRIKE, datetime.now(), _id)
                # save_punish(ps)
                #
                # user = get(client.get_all_members(), id=_id)
                # await user.add_roles(strike_roles[mc.strikes])
                return
            update_mc(mc)
            return

        ps = Punishment(Punishment.WARN, datetime.now(), _id)
        user = get(client.get_all_members(), id=_id)
        await user.add_roles(roles[warn_role_id])
        save_punish(ps)
        update_mc(mc)


@client.command(name="sm")
async def sm(ctx, channel_id, title, mentions, *, description):
    channel = ctx.guild.get_channel(int(channel_id))
    embed_var = discord.Embed(title=title, description=description, color=discord.Colour(0xFFFF00))
    await channel.send(embed=embed_var, content=mentions)


@slash.slash(name="send-message",
             description="This is a message sender command.",
             guild_ids=guild_ids,
             )
async def send_message_embed(ctx: SlashContext, channel_id, title, *, description):
    channel = ctx.guild.get_channel(int(channel_id))
    embed_var = discord.Embed(title=title, description=description.replace('\-n', "\n"), color=discord.Colour(0xFFFF00))
    await channel.send(embed=embed_var)


@slash.slash(name="send-message-url",
             description="This is a message sender command.",
             guild_ids=guild_ids,
             )
async def send_message_embed_url(ctx: SlashContext, channel_id, title, description, url):
    channel = ctx.guild.get_channel(int(channel_id))
    embed_var = discord.Embed(title=title, description=description, color=discord.Colour(0xFFFF00), url=url)
    await channel.send(embed=embed_var)


@slash.slash(name="strike",
             description="This is a strike command.",
             guild_ids=guild_ids,
             )
async def strike(ctx: SlashContext, employee, reason):
    role_ids = [r.id for r in ctx.author.roles]
    emojis = client.emojis
    emojis = {e.name: str(e) for e in emojis}
    mc_guild = client.get_guild(798587846859423744)
    roles = get_ranks_roles_by_id(mc_guild)
    _id = int(employee.split("!")[1].replace(">", ""))
    strike_roles = {1: roles[798587846859423749], 2: roles[798587846859423750], 3: roles[798587846859423751]}
    # supervisor and management
    if 798587846868860960 in role_ids or 812998810397442109 in role_ids \
            or 798587846868860965 in role_ids or 903940304749600768 in role_ids:

        mc = get_user(_id)
        if mc.strikes < 2:
            await ctx.send(
                content=f"**{employee}. Shoma be dalile: {reason}, strike gereftid** :strikes:".replace(":strikes:",
                                                                                                        emojis[
                                                                                                            "strikes"]))
            mc.strikes += 1
            ps = Punishment(Punishment.STRIKE, datetime.now(), _id)
            save_punish(ps)
            update_mc(mc)
            user = get(client.get_all_members(), id=_id)
            await user.add_roles(strike_roles[mc.strikes])
            if supervisor_role_id in role_ids or management_role_id in role_ids:
                channel = await user.create_dm()
                await channel.send(content=f"**{employee}. Shoma be dalile: {reason}, strike gereftid** :strikes:".replace(":strikes:",
                                                                                                        emojis[
                                                                                                            "strikes"]))
            return
        elif mc.strikes == 2:
            await ctx.send(
                content=f"**{employee}. Shoma be dalile: {reason}, strike gereftid** :strikes:".replace(":strikes:",
                                                                                                        emojis[
                                                                                                            "strikes"]))
            await ctx.send(
                content=f"**{employee}. Shoma be dalile dashtan 3 strike fire shodid,"
                        f" dar soorat dashtan har goone eteraz be Management payam bedahid**")

            user = get(client.get_all_members(), id=_id)
            print(user.roles)
            user_role_ids = [r.id for r in user.roles]
            if supervisor_role_id in user_role_ids or management_role_id in user_role_ids:
                print("Sending DM")
                channel = await user.create_dm()
                await channel.send(content=f"**{employee}. Shoma be dalile: {reason}, strike gereftid** :strikes:".replace(":strikes:",
                                                                                                        emojis[
                                                                                                            "strikes"]))
                await channel.send(
                    content=f"**{employee}. Shoma be dalile dashtan 3 strike fire shodid,"
                            f" dar soorat dashtan har goone eteraz be Management payam bedahid**")
            mc.strikes += 1
            ps = Punishment(Punishment.STRIKE, datetime.now(), _id)
            save_punish(ps)
            update_mc(mc)
            user = get(client.get_all_members(), id=_id)
            await user.add_roles(strike_roles[mc.strikes])
            return


@slash.slash(name="remove-strike",
             description="This is a strike removal command.",
             guild_ids=guild_ids,
             )
async def remove_strike(ctx: SlashContext, employee):
    role_ids = [r.id for r in ctx.author.roles]

    mc_guild = client.get_guild(798587846859423744)
    roles = get_ranks_roles_by_id(mc_guild)
    strike_roles = {1: roles[798587846859423749], 2: roles[798587846859423750], 3: roles[798587846859423751]}
    _id = int(employee.split("!")[1].replace(">", ""))
    # supervisor and management
    if 798587846868860960 in role_ids or 812998810397442109 in role_ids \
            or 798587846868860965 in role_ids or 903940304749600768 in role_ids:

        mc = get_user(_id)
        if mc.strikes > 0:
            try:
                user = get(client.get_all_members(), id=_id)
                await user.remove_roles(strike_roles[mc.strikes])
            except Exception as e:
                print("Cant remove role")
            for p in get_punishments(_id):
                if p.punish_type == Punishment.STRIKE:
                    del_punishments(_id, p.date, Punishment.STRIKE)
                    mc.strikes -= 1
                    await ctx.send(
                        content=f"**{employee}. One of your strikes has been removed now you have {mc.strikes} strikes**")
                    update_mc(mc)
                    break


@slash.slash(name="remove-warn",
             description="This is a strike removal command.",
             guild_ids=guild_ids,
             )
async def remove_warn(ctx: SlashContext, employee):
    role_ids = [r.id for r in ctx.author.roles]
    roles = get_ranks_roles_by_id(ctx.guild)
    # mc_guild = client.get_guild(798587846859423744)
    _id = int(employee.split("!")[1].replace(">", ""))
    # supervisor and management
    if 903913968979038209 in role_ids or 798587846868860960 in role_ids or 812998810397442109 in role_ids \
            or 798587846868860965 in role_ids or 903940304749600768 in role_ids:

        mc = get_user(_id)
        if mc.warns > 0:
            for p in get_punishments(_id):
                if p.punish_type == Punishment.WARN:
                    del_punishments(_id, p.date, Punishment.WARN)
                    user = get(client.get_all_members(), id=_id)

                    await user.remove_roles(roles[warn_role_id])
                    mc.warns -= 1
                    await ctx.send(
                        content=f"**{employee}. One of your warns has been removed now you have {mc.warns} warns**")
                    update_mc(mc)

                    break


@slash.slash(name="profile",
             description="This is a profiling command.",
             guild_ids=guild_ids,
             )
async def profile(ctx: SlashContext, employee):
    # role_ids = [r.id for r in ctx.author.roles]
    # emojis = client.emojis
    # emojis = {e.name: str(e) for e in emojis}

    _id = int(employee.split("!")[1].replace(">", ""))
    # supervisor and management
    # if 798587846868860960 in role_ids or 812998810397442109 in role_ids \
    #         or 798587846868860965 in role_ids or 903940304749600768 in role_ids:
    #     pass
    mc = get_user(_id)
    stars = 0
    role_ids = [r.id for r in ctx.author.roles]
    if three_stars_role_id in role_ids:
        stars = 3
    elif two_stars_role_id in role_ids:
        stars = 2
    elif one_star_role_id in role_ids:
        stars = 1
    await ctx.send(
        content=f"{employee}\nIC Name : {mc.ic_name} \nRoster ID : {mc.roster_id} \nRank : {mc.rank} \nWarns : {mc.warns} \nStrikes : {mc.strikes}\nStars: {stars}")


@slash.slash(name="star", description="Star dealer", guild_ids=guild_ids)
async def star_store(ctx: SlashContext):
    if ctx.author:
        # roles = get_ranks_roles_by_id(ctx.guild)
        # await ctx.author.add_roles(roles[three_stars_role_id])
        emojis = client.emojis
        emojis = {e.name: str(e) for e in emojis}
        role_ids = [r.id for r in ctx.author.roles]
        if three_stars_role_id in role_ids:
            embed_var = discord.Embed(title=":star: Star Menu :star:", description=f"1-:star: Rent MC VIP cars "
                                                                                   f":race_car:\n2-:star: Remove one "
                                                                                   f"of your strikes {emojis['strikes']}\n3-:star::star::star: One rank "
                                                                                   f" boost :arrow_up:",
                                      color=discord.Colour(0xFFFF00))
            buttons = [
                create_button(
                    custom_id="rent_vip",
                    style=ButtonStyle.blue,
                    label="1"
                ),
                create_button(
                    custom_id="remove_strike",
                    style=ButtonStyle.blue,
                    label="2"
                ),
                create_button(
                    custom_id="rank_boost",
                    style=ButtonStyle.blue,
                    label="3",
                ),
            ]

            action_row = create_actionrow(*buttons)

            return await ctx.channel.send(embed=embed_var, components=[action_row])
        elif two_stars_role_id in role_ids or one_star_role_id in role_ids:
            embed_var = discord.Embed(title=f":star: Star Menu :star:", description=f"1-:star: Remove one "
                                                                                    f"of your strikes {emojis['strikes']}\n2-:star: Rent MC VIP cars "
                                                                                    f":race_car:",
                                      color=discord.Colour(0xFFFF00))
            buttons = [
                create_button(
                    custom_id="remove_strike",
                    style=ButtonStyle.blue,
                    label="1"
                ),
                create_button(
                    custom_id="rent_vip",
                    style=ButtonStyle.blue,
                    label="2"
                ),
            ]

            action_row = create_actionrow(*buttons)

            return await ctx.channel.send(embed=embed_var, components=[action_row])
        else:
            embed_var = discord.Embed(title=":star: Star Menu :star:",
                                      description="?????? ?????????? ???????? ???????? ???????? ????????????",
                                      color=discord.Colour(0xFFFF00))
            return await ctx.channel.send(embed=embed_var)


@slash.component_callback(components=["remove_strike", "rank_boost", "rent_vip"])
async def star_store_handler(ctx: discord_slash.context.ComponentContext):
    number_of_stars = 0
    roles = get_ranks_roles_by_id(ctx.guild)
    role_ids = [r.id for r in ctx.author.roles]
    star_number = {1: one_star_role_id, 2: two_stars_role_id, 3: three_stars_role_id}
    if three_stars_role_id in role_ids:
        number_of_stars = 3
    elif two_stars_role_id in role_ids:
        number_of_stars = 2
    elif one_star_role_id in role_ids:
        number_of_stars = 1
    if number_of_stars <= 0:
        embed_var = discord.Embed(title=":star: Star Menu :star:", description="?????? ?????????? ???????? ???????? ???????? ????????????",
                                  color=discord.Colour(0xFFFF00))
        await ctx.channel.send(embed=embed_var)
        return
    if ctx.custom_id == "rent_vip":

        if number_of_stars > 1:
            exp_date = datetime.now() + timedelta(weeks=2)
            await ctx.author.remove_roles(roles[star_number[number_of_stars]])
            number_of_stars -= 1
            if number_of_stars > 0:
                await ctx.author.add_roles(roles[star_number[number_of_stars]])
            for gm in get_gang_employee(ctx.guild):
                channel = await gm.create_dm()
                await channel.send(content=f"{ctx.author.mention} ???? ?????????? ?????? ?????????? ?????????? ?????? VIP ?????????????? ??????. ?????????? ??????????**{exp_date.year}.{exp_date.month}.{exp_date.day}** ")

            await ctx.channel.send(
                content=f'{ctx.author.mention} ?????? ???? ?????? ???? ???????? ?????????? ?????????????? ???? ?????????? ?????? VIP ?????? ?????????????? ???? ??????????. ?????????? ?????????? **{exp_date.year}.{exp_date.month}.{exp_date.day}**')

    elif ctx.custom_id == "remove_strike":

        strike_roles = {1: roles[798587846859423749], 2: roles[798587846859423750], 3: roles[798587846859423751]}
        _id = ctx.author_id
        # supervisor and management
        if 798587846868860960 in role_ids or 812998810397442109 in role_ids \
                or 798587846868860965 in role_ids or 903940304749600768 in role_ids:

            mc = get_user(_id)
            if mc.strikes > 0:
                try:
                    user = get(ctx.guild.members, id=_id)
                    await user.remove_roles(strike_roles[mc.strikes])
                except Exception as e:
                    print("Cant remove role")
                removed = False
                for p in get_punishments(_id):
                    if p.punish_type == Punishment.STRIKE:
                        one_week = timedelta(weeks=1)
                        if p.date > one_week:
                            await ctx.author.remove_roles(roles[star_number[number_of_stars]])
                            number_of_stars -= 1
                            if number_of_stars > 0:
                                await ctx.author.add_roles(roles[star_number[number_of_stars]])
                            del_punishments(_id, p.date, Punishment.STRIKE)
                            mc.strikes -= 1
                            embed_var = discord.Embed(title=":star: Star Menu :star:",
                                                      description=f"**{ctx.author.mention}. One of your strikes has been removed now you have {mc.strikes} strikes**",
                                                      color=discord.Colour(0xFFFF00))
                            await ctx.channel.send(embed=embed_var)
                            update_mc(mc)
                            removed = True
                            for c in get_chiefs(ctx.guild):
                                channel = await c.create_dm()
                                await channel.send(
                                    content=f"{ctx.author.mention} ???? ?????????? ?????? ???? ?????? ?????? ???????? ?????????? ?????????????? ??????")
                            break

                if not removed:
                    embed_var = discord.Embed(title=":star: Star Menu :star:",
                                              description=f"**{ctx.author.mention} ???????????????? ?????????? ???? ?????? ???????? ?????????? ?????? ????????????. ???? ???????? ???????? ?????? ?????????? ???????? ???? ???????? ?????????? ???????? **",
                                              color=discord.Colour(0xFF0000))
                    await ctx.channel.send(embed=embed_var)

            else:
                await ctx.send(content="?????????????????? ?????? ?????? ???????????? ????????????")
    elif ctx.custom_id == "rank_boost":
        if number_of_stars < 3:
            embed_var = discord.Embed(title=":star: Star Menu :star:", description="?????? ?????????? ???????? ???????? ???????? ????????????",
                                      color=discord.Colour(0xFFFF00))
            await ctx.channel.send(embed=embed_var)
            return
        number_of_stars -= 3
        await ctx.author.remove_roles(roles[three_stars_role_id])
        for rum in get_rank_up_managers(ctx.guild):
            channel = await rum.create_dm()
            embed_var = discord.Embed(title="Rank Up",
                                      description=f"{ctx.author.mention} ???? ?????????? ?????? ???? ?????? ?????????? ???????? ?????????????? ?????? ???????? ???????????? ???????? ",
                                      color=discord.Colour(0xFFFF00))
            await channel.send(embed=embed_var)
        deksy = get(ctx.guild.members, id=583223852641812499)
        channel = await deksy.create_dm()
        embed_var = discord.Embed(title="Rank Up",
                                  description=f"{ctx.author.mention} used three stars in order to have one bonus rank up "
                                              f"this week, make it done.",
                                  color=discord.Colour(0xFFFF00))
        await channel.send(embed=embed_var)
        await ctx.channel.send(content="?????????????? ?????? ???????? ???????????? ?????????? ????.")
    return


async def delete_non_bot_messages(channel):
    # warn channel id : 866287973627985920
    # channel = guild.get_channel(807366748118319224)
    messages = await channel.history().flatten()
    for message in messages:
        if message.author.id != mc_bot_id:
            await message.delete()


async def create_mc_from_discord(guild: discord.Guild):
    members = guild.members

    temp = []
    for member in members:
        role_ids = [r.id for r in member.roles]
        if 842695874668003328 in role_ids or role_ids.__contains__(842695874668003328):
            if get_ic_roster(member) is not None:
                ic, roster, rank = get_ic_roster(member)
                mc = MechanicEmployee(ic, roster, member.id, "")
                punishes = await non_blocking_data_insertion(get_punishments, member.id)
                warns = 0
                strikes = 0
                mc.strikes = 0
                mc.warns = 0
                if punishes is not None:
                    for punish in punishes:
                        if punish.punish_type == Punishment.WARN:
                            warns += 1
                        elif punish.punish_type == Punishment.STRIKE:
                            strikes += 1
                    mc.warns = warns
                    mc.strikes = strikes
                if warns % 2 == 0:
                    mc.warns = 0
                else:
                    mc.warns = 1
                mc.rank = rank
                temp.append(mc)

    return temp


def get_ic_roster(member: discord.Member):
    if member:
        role_ids = [r.id for r in member.roles]
        if member.nick:
            # 1|trainee
            if "????" in member.nick:
                ic = member.nick.split("????")[1]
                return ic, -1, 1
            elif ")" in member.nick:
                divided = member.nick.split(")")
                ic = divided[1]
                roster = divided[0].split("(")[1].replace(")", "")
                print(roster)
                # 2???Patrol
                if 812998799063515186 in role_ids:
                    return ic, roster, 2
                # 3???Repair Tech
                elif 812998808233443328 in role_ids:
                    return ic, roster, 3
                # 4???Car relief
                elif 812998808811601920 in role_ids:
                    return ic, roster, 4
                # 5???Technician
                elif 812998809420300298 in role_ids:
                    return ic, roster, 5
                elif 812998810397442109 in role_ids:
                    return ic, roster, 6
                elif 956697633798365215 in role_ids:
                    return ic, roster, 7
                elif 881178069241569340 in role_ids:
                    return ic, roster, 8
                elif 812998812943122446 in role_ids:
                    return ic, roster, 9
                elif 812998818328739872 in role_ids:
                    return ic, roster, 10
                elif 798587846868860960 in role_ids:
                    return ic, roster, 11

        else:
            return member.name.split("#")[0], 0, 11


def get_ranks_roles_by_name(guild: discord.Guild):
    res = {}
    for role in guild.roles:
        res[role.name] = role
    return res


def get_ranks_roles_by_id(guild: discord.Guild):
    res = {}
    for role in guild.roles:
        res[role.id] = role
    return res


keep_alive()
client.run(bot_token)
