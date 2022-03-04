class MechanicEmployee:
    def __init__(self, ic_name, roster_id):
        self.roster_id = roster_id
        self.ic_name = ic_name
        self.rank = 1
        self.warns = 0
        self.strikes = 0
