from model import MechanicEmployee
from credentials import db_url
import json
import psycopg2
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger(__name__)

db = dict()


def add_mcs_to_db(mechanics_list: list[MechanicEmployee]):
    # users = db["users"]
    con, cursor = create_connection()

    insert_query = """INSERT INTO mechanics(roster_id, ic_name, discord_id, rank, warns, strikes) """ \
                   """VALUES(%s, %s, %s, %s, %s, %s)"""
    values = []
    mcs = {mc.discord_id: mc for mc in get_all_mechanics()}

    for mechanic in mechanics_list:
        try:
            mc = mcs[mechanic.discord_id]

            if mc and (
                    mc.ic_name != mechanic.ic_name or mc.roster_id != mechanic.roster_id or mc.rank != mechanic.rank):
                update_mc(mechanic)
                continue
        except Exception as e:
            value = (
                mechanic.roster_id, mechanic.ic_name, str(mechanic.discord_id), str(mechanic.rank), str(mechanic.warns),
                str(mechanic.strikes))
            values.append(value)
            print(e)

        # if not get_user(_user.id):
        #     users.append(json.dumps(_user.__dict__))

    cursor.executemany(insert_query, values)
    con.commit()
    cursor.close()
    con.close()
    # print_tables()


# def add_admins(list_users):
#     con, cursor = create_connection()
#     insertion_sql = """INSERT INTO admins(username, social_credits, id, level) """ \
#                     """VALUES(%s, %s, %s, %s)"""
#     values = []
#     admins = get_all_admins()
#     print(admins)
#     for user in list_users:
#         if user.id in admins_id:
#             value = (user.name, "0", str(user.id), "0")
#             if value not in values and (user.name, 0, user.id, 0) not in admins:
#                 values.append(value)
#
#     cursor.executemany(insertion_sql, values)
#     con.commit()
#     cursor.close()
#     con.close()


def setup_tables(list_users):
    # print(f"[INFO]: user detail: {[user for user in list_users]}")
    con, cursor = create_connection()
    try:
        cursor.execute("""SELECT table_name FROM information_schema.tables
               """)
        tables = cursor.fetchall()
        if ("mechanics",) not in tables:
            print("[INFO]: Creating Tables")
            cursor.execute(
                """CREATE TABLE mechanics (
                    roster_id INTEGER,
                    ic_name VARCHAR(255),
                    discord_id BIGINT PRIMARY KEY,
                    rank INTEGER,
                    warns INTEGER,
                    strikes INTEGER,
                    steam_hex VARCHAR(255)
                )""")

        cursor.close()
        con.commit()
        con.close()
    except Exception as e:
        print(f"[Error][Setup Tables]: {e}")
    add_mcs_to_db(list_users)
    # add_admins(list_users)
    # print_tables()


def print_tables():
    print("[INFO]: Printing mechanics Table")
    con, cursor = create_connection()
    cursor.execute("SELECT * FROM mechanics")
    result = cursor.fetchall()
    for r in result:
        print(r)
    cursor.close()
    con.commit()


def get_user(id):
    user_ret = "SELECT * FROM mechanics WHERE discord_id = %s"
    con, cursor = create_connection()
    try:
        cursor.execute(user_ret, (id,))
        _user = cursor.fetchall()
        # print(f"[INFO]: Retrieving database user : {_user[0]}")
        user = MechanicEmployee.decoder_static(_user[0])
        # print(f"[INFO]: Retrieving object user : {user}")
        con.commit()
        cursor.close()
        con.close()
        return user

    except Exception as e:
        print(f"[Error][get_user]: {e}")
        return None


def get_all_mechanics():
    sql = "SELECT * FROM mechanics"
    con, cursor = create_connection()
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        con.commit()
        cursor.close()
        con.close()
        result = [MechanicEmployee.decoder_static(mc) for mc in result]
        return result
    except Exception as e:
        print(f"[Error]: {e}")


def get_all_admins():
    sql = "SELECT * FROM admins"
    con, cursor = create_connection()
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        con.commit()
        cursor.close()
        con.close()
        return result
    except Exception as e:
        print(f"[Error]: {e}")


def get_user_id(id):
    users = db["users"]
    index = 0
    for user in users:
        _user = User.user_decoder(json.loads(user))
        if _user.id == id:
            return index
        index += 1
    return index


def get_user_occurance(id):
    users = db["users"]
    index = 0
    for user in users:
        _user = User.user_decoder(json.loads(user))
        if _user.id == id:
            index += 1
    return index


def set_user(user):
    d = json.dumps(user.__dict__)
    del db["users"][get_user_id(user.id)]
    print("[INFO]: Saving user: " + d)
    db["users"].append(d)


def update_mc(mc: MechanicEmployee):
    update_query = "UPDATE mechanics SET roster_id = %s, ic_name = %s, discord_id = %s, rank = %s, warns = %s, " \
                   "strikes = %s, steam_hex = %s WHERE discord_id = %s "
    con, cursor = create_connection()
    try:
        print(f"[INFO]: Saving mechanic: {mc.ic_name}")
        cursor.execute(update_query, (mc.roster_id, mc.ic_name, mc.discord_id, mc.rank, mc.warns, mc.strikes,
                                      mc.steam_hex, mc.discord_id))
        con.commit()
        cursor.close()
        con.close()
        print("Done")
    except Exception as e:
        print(f"[Error][update_mc]: {e}")


# def get_admin(user):
#     admin_ret = "SELECT * FROM admins WHERE id = %s"
#     con, cursor = create_connection()
#     try:
#         cursor.execute(admin_ret, (user.id,))
#         _user = cursor.fetchall()
#         print(f"[INFO]: Retrieving database admin : {_user[0]}")
#         admin = Admin.user_decoder_static(_user[0])
#         print(f"[INFO]: Retrieving object admin : {admin}")
#         con.commit()
#         cursor.close()
#         con.close()
#         return admin
#     except Exception as e:
#         print(f"[Error]: {e}")
#         return None


def delete_db():
    update_query = "DROP TABLE mechanics"
    con, cursor = create_connection()
    try:
        cursor.execute(update_query)
        con.commit()
        cursor.close()
        con.close()
    except Exception as e:
        print(f"[Error][setup_db.py]: {e}")


def create_connection():
    try:
        con = psycopg2.connect(db_url)
        #  print(f"[INFO]: Connected to DB {con}")
        return con, con.cursor()
    except Exception as e:
        logger.error(f"{e}")

# delete_db()``
