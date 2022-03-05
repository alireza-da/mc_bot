class MechanicEmployee:
    def __init__(self, ic_name, roster_id, discord_id, steam_hex):
        self.roster_id = roster_id
        self.ic_name = ic_name
        self.discord_id = discord_id
        self.rank = 1
        self.warns = 0
        self.strikes = 0
        self.steam_hex = steam_hex

    @staticmethod
    def decoder_static(obj):
        mc = MechanicEmployee(obj[1], obj[0], obj[2], obj[6])
        mc.rank = obj[3]
        mc.warns = obj[4]
        mc.strikes = obj[5]
        return mc
