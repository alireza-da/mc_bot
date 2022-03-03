from datetime import datetime, timedelta
from dateutil import tz

from_zone = tz.tzutc()
to_zone = tz.tzlocal()


async def read_off_duties(channel):
    messages = await channel.history(limit=200).flatten()
    for message in messages:
        if message.author.id == 765915730171920465:
            messages.remove(message)
    return messages


async def delete_old_messages(messages):
    current_dt = datetime.now(tz=to_zone)
    three_hrs = timedelta(hours=3)
    for message in messages:
        utc = message.created_at.replace(tzinfo=from_zone)
        central = utc.astimezone(to_zone)

        diff = current_dt - central
        if diff > three_hrs:
            await message.delete()
