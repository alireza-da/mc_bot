import functools
import threading
import typing

import discord
import asyncio

from credentials import bot_token, mc_bot_id
from discord.ext import commands
from utils import retrieve_sv_status
from concurrent.futures import ProcessPoolExecutor
from discord_slash import SlashCommand, SlashContext
from backend import keep_alive
from notification_handler import read_off_duties, delete_old_messages, create_embed_template, read_off_on_duty_notifs
from model import MechanicEmployee
from setup_db import setup_tables, get_user, update_mc

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
    emojis = client.emojis
    emojis = {e.name: str(e) for e in emojis}
    # print(emojis)
    mhkn_guild = client.get_guild(869221659733807125)
    mc_guild = client.get_guild(798587846859423744)
    # print(mc_guild.roles)
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

    def between_callback_off_notif():
        asyncio.run_coroutine_threadsafe(send_off_duty_notifs(mc_guild), client.loop)

    _thread3 = threading.Thread(target=between_callback_off_notif)
    _thread3.start()
    # setup_tables(create_mc_from_discord(mc_guild.members))

    await non_blocking_data_insertion(setup_tables, create_mc_from_discord(mc_guild.members))


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
            await asyncio.sleep(10)
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


async def send_off_duty_notifs(guild):
    # off duty channel link : https://discord.com/channels/798587846859423744/921891073700274269
    while True:
        await asyncio.sleep(5)
        channel = guild.get_channel(921891073700274269)
        messages = await read_off_duties(channel)
        await create_embed_template(channel)
        await delete_old_messages(messages)
        punish_channel = guild.get_channel(866287973627985920)
        # await delete_non_bot_messages(punish_channel)
        # await read_off_on_duty_notifs(guild)


@client.event
async def on_message(message):
    if message.author != client.user:
        # off duty channel
        if message.channel.id == 921891073700274269:
            if "ic name" in message.content.lower():
                emojis = client.emojis
                emojis = {e.name: str(e) for e in emojis}
                await message.add_reaction(":Accept:".replace(":Accept:", emojis["Accept"]))
                await message.add_reaction(":Decline:".replace(":Decline:", emojis["Decline"]))


@client.event
async def on_reaction_add(reaction, user):
    emojis = client.emojis
    emojis = {e.name: str(e) for e in emojis}
    role_ids = [r.id for r in user.roles]
    if user != client.user:
        if str(reaction.emoji) == emojis["Accept"] and reaction.message.channel.id == 921891073700274269:
            # management supervisor rank6 chief deputy
            if 798587846868860960 in role_ids or 922137155134955530 in role_ids or 812998810397442109 in role_ids \
                    or 798587846868860965 in role_ids or 903940304749600768 in role_ids:
                await reaction.message.reply(
                    f"<@{reaction.message.author.id}> Your off duty permission granted by <@{user.id}>")
                return
            else:
                await reaction.remove(user)
        elif str(reaction.emoji) == emojis["Decline"] and reaction.message.channel.id == 921891073700274269:
            if 798587846868860960 in role_ids or 922137155134955530 in role_ids or 812998810397442109 in role_ids \
                    or 798587846868860965 in role_ids or 903940304749600768 in role_ids:
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
    # supervisor and management
    if 922137155134955530 in role_ids or 798587846868860960 in role_ids or 812998810397442109 in role_ids \
            or 798587846868860965 in role_ids or 903940304749600768 in role_ids:
        await ctx.send(
            content=f"{employee}. Shoma be dalile: {reason}, warn gereftid :warn:".replace(":warn:", emojis["warn"]))
        mc = get_user(_id)
        mc.warns += 1
        if mc.warns % 2 == 0:
            mc.strikes += 1
            await ctx.send(
                content=f"{employee}. Shoma be dalile: gereftan 2 warn, strike gereftid :strike:".replace(":strike:",
                                                                                                 emojis["strikes"]))
        update_mc(mc)


@slash.slash(name="strike",
             description="This is a strike command.",
             guild_ids=guild_ids,
             )
async def strike(ctx: SlashContext, employee, reason):
    role_ids = [r.id for r in ctx.author.roles]
    emojis = client.emojis
    emojis = {e.name: str(e) for e in emojis}

    _id = int(employee.split("!")[1].replace(">", ""))
    # supervisor and management
    if 798587846868860960 in role_ids or 812998810397442109 in role_ids \
            or 798587846868860965 in role_ids or 903940304749600768 in role_ids:
        await ctx.send(
            content=f"**{employee}. Shoma be dalile: {reason}, strike gereftid** :strikes:".replace(":strikes:",
                                                                                                    emojis["strikes"]))
        mc = get_user(_id)
        update_mc(mc)


@slash.slash(name="profile",
             description="This is a profiling command.",
             guild_ids=guild_ids,
             )
async def strike(ctx: SlashContext, employee):
    role_ids = [r.id for r in ctx.author.roles]
    emojis = client.emojis
    emojis = {e.name: str(e) for e in emojis}

    _id = int(employee.split("!")[1].replace(">", ""))
    # supervisor and management
    if 798587846868860960 in role_ids or 812998810397442109 in role_ids \
            or 798587846868860965 in role_ids or 903940304749600768 in role_ids:
        pass
    mc = get_user(_id)
    await ctx.send(
        content=f"{employee}\nIC Name : {mc.ic_name} \nRoster ID : {mc.roster_id} \nRank : {mc.rank} \nWarns : {mc.warns} \nStrikes : {mc.strikes}")


async def delete_non_bot_messages(channel):
    # warn channel id : 866287973627985920
    # channel = guild.get_channel(807366748118319224)
    messages = await channel.history().flatten()
    for message in messages:
        if message.author.id != mc_bot_id:
            await message.delete()


def create_mc_from_discord(members):
    temp = []
    for member in members:
        role_ids = [r.id for r in member.roles]
        if 842695874668003328 in role_ids or role_ids.__contains__(842695874668003328):
            # print(member, member.roles, role_ids)
            if get_ic_roster(member) is not None:
                ic, roster, rank = get_ic_roster(member)
                mc = MechanicEmployee(ic, roster, member.id, "")
                mc.rank = rank
                temp.append(mc)

    return temp


def get_ic_roster(member: discord.Member):
    if member:
        role_ids = [r.id for r in member.roles]
        if member.nick:
            # 1|trainee
            if "🟫" in member.nick:
                ic = member.nick.split("🟫")[1]
                return ic, -1, 1
            else:
                divided = member.nick.split(")")
                ic = divided[1]
                roster = divided[0].split("-")[1].replace(")", "")
                # 2│Patrol
                if 812998799063515186 in role_ids:
                    return ic, roster, 2
                # 3│Repair Tech
                elif 812998808233443328 in role_ids:
                    return ic, roster, 3
                # 4│Car relief
                elif 812998808811601920 in role_ids:
                    return ic, roster, 4
                # 5│Technician
                elif 812998809420300298 in role_ids:
                    return ic, roster, 5
                elif 812998810397442109 in role_ids:
                    return ic, roster, 6
                elif 881178069241569340 in role_ids:
                    return ic, roster, 7
                elif 812998812943122446 in role_ids:
                    return ic, roster, 8
                elif 812998818328739872 in role_ids:
                    return ic, roster, 9
        else:
            return member.name.split("#")[0], 0, 11


def get_ranks_roles_by_name(guild: discord.Guild):
    res = {}
    for role in guild.roles:
        res[role.name] = role


def get_ranks_roles_by_id(guild: discord.Guild):
    res = {}
    for role in guild.roles:
        res[role.id] = role


keep_alive()
client.run(bot_token)
