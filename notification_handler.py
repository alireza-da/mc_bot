from datetime import datetime, timedelta
from dateutil import tz
from setup_db import del_punishments, get_user, update_mc
from model import Punishment
from credentials import interviewer_role_id, lobby_vc_id, management_role_id, mc_chief_id, mc_deputy_id
from discord.utils import get

import asyncio
import discord

from_zone = tz.tzutc()
to_zone = tz.tzlocal()
interview_cool_down_list = {}
ticket_cd_list = []


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

    return messages[0:len(messages) - 1]


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
    embed_var = discord.Embed(title="Off Duty Submission Form",
                              description=":capital_abcd: IC Name:\n:tools: MC Rank:\n:watch: "
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


async def delete_warn_2_weeks(channel: discord.TextChannel):
    while True:
        await asyncio.sleep(5)
        messages = await channel.history().flatten()
        current_dt = datetime.now(tz=to_zone)
        two_weeks = timedelta(weeks=2)
        for message in messages:
            utc = message.created_at.replace(tzinfo=from_zone)
            central = utc.astimezone(to_zone)
            diff = current_dt - central
            if diff > two_weeks and "strike" not in message.content:
                try:
                    print(f"Removing warn of{message.mentions[0].id}")
                    del_punishments(message.mentions[0].id, message.created_at, Punishment.WARN)
                    mc = get_user(message.mentions[0].id)
                    print(f"Removing warn of{mc.ic_name}")
                    mc.warns -= 1
                    update_mc(mc)
                    await message.delete()
                except Exception as e:
                    print(e)


async def send_interview_dm(mc_guild: discord.Guild):
    interviewers = get_interviewers(mc_guild)
    for tc in mc_guild.text_channels:
        if "ticket-" in tc.name.lower() and tc.category.id == 852876928187629578 and tc not in ticket_cd_list:
            for iv in interviewers:
                # pv channel
                channel = await iv.create_dm()
                invite_link = f"https://discord.com/channels/798587846859423744/{tc.id}"
                ticket_id = tc.name.split("-")[1]
                ticket_cd_list.append(tc)
                embed_var = discord.Embed(title=tc.name, description=f"Yek ticket be id **{ticket_id}** dar channel **{tc.name}** "
                                                                     f"server discord mechanici dar "
                                   f"vaziat open qarar dararad lotfan residegi konid",
                                          url=invite_link, color=discord.Colour(0xFFFF00))

                await channel.send(embed=embed_var)

    for tc in ticket_cd_list:
        if tc not in mc_guild.text_channels:
            ticket_cd_list.remove(tc)


async def send_lobby_dm(mc_guild: discord.Guild):
    interviewers = get_interviewers(mc_guild)
    lobby_vc = None
    for vc in mc_guild.voice_channels:
        if vc.id == lobby_vc_id:
            lobby_vc = vc
            break

    # lobby_vc = await mc_guild.get_channel(lobby_vc_id)
    for member in lobby_vc.members:
        # 24/7 bot
        if member.id == 369208607126061057 or member in interview_cool_down_list.keys():
            continue
        interview_cool_down_list[member] = datetime.now()
        for interviewer in interviewers:
            if interviewer.status != discord.Status.offline:
                channel = await interviewer.create_dm()
                # name = member.name
                # if member.nick:
                #     name = member.nick
                invite_link = await lobby_vc.create_invite(max_uses=1, unique=True)
                embed_var = discord.Embed(title="Interview Lobby", description=f"<@!{member.id}> - dar lobby discord "
                                                                           f"mechanici montazer interviewer mibas"
                                                                           f"had lotfan "
                               f"peygiri konid \n", color=discord.Colour(0xFFFF00), url=invite_link)
                await channel.send(embed=embed_var, content=invite_link)
        # deksy = get(mc_guild.members, id=583223852641812499)
        # channel = await deksy.create_dm()
        # # name = member.name
        # # if member.nick:
        # #     name = member.nick
        # invite_link = await lobby_vc.create_invite(max_uses=1, unique=True)
        # embed_var = discord.Embed(title="Interview Lobby", description=f"<@!{deksy.id}> - dar lobby discord "
        #                                                                f"mechanici montazer interviewer mibas"
        #                                                                f"had lotfan "
        #                                                                f"peygiri konid \n",
        #                           color=discord.Colour(0xFFFF00), url=invite_link)
        # await channel.send(embed=embed_var, content=invite_link)
    remove_cd_lobby()


def get_interviewers(mc_guild: discord.Guild):
    res = []
    for mc in mc_guild.members:
        role_ids = [r.id for r in mc.roles]
        if role_ids.__contains__(interviewer_role_id) or role_ids.__contains__(management_role_id)\
                or role_ids.__contains__(mc_chief_id) or role_ids.__contains__(mc_deputy_id):
            res.append(mc)
        # if mc.id == 583223852641812499:
        #     res.append(mc)

    return res


def remove_cd_lobby():
    # print(interview_cool_down_list)
    half_hour = timedelta(minutes=30)
    current_dt = datetime.now(tz=to_zone)
    for key in interview_cool_down_list:
        utc = interview_cool_down_list[key].replace(tzinfo=from_zone)
        central = utc.astimezone(to_zone)
        diff = current_dt - central
        if diff > half_hour:
            print(f"[INFO]: Removing cool down of {key}")
            del interview_cool_down_list[key]



