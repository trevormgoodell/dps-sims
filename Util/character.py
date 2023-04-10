import requests

class Character:
    def __init__(self, server, name) -> None:
        self.name = name
        self.server = server
        url = "https://us.api.blizzard.com/profile/wow/character/" + server + "/" + name + "/statistics?namespace=profile-us&locale=en_US&access_token=USFp5KQHACuUql4WHcUCt6mKOs4m1lZppb"
        
        response = requests.get(url)
        
        if response.status_code != 200:
            print("Something went wrong... Make sure character name and server name are spelt correctly.")
            return

        data = response.json()

        # All important character stats, could be wrong if not a caster

        self.power = max(data['agility']['effective'], data['intellect']['effective'])
        self.haste = data['spell_haste']['value'] / 100
        self.mastery = data['mastery']['value'] / 100
        self.critical_strike = data['spell_crit']['value'] / 100
        self.versatility = data['versatility_damage_done_bonus'] / 100

        # Getting covenant data
        url = "https://us.api.blizzard.com/profile/wow/character/" + server + "/" + name + "/soulbinds?namespace=profile-us&locale=en_US&access_token=USFp5KQHACuUql4WHcUCt6mKOs4m1lZppb"
        response = requests.get(url)
        
        if response.status_code != 200:
            print("Something went wrong... Make sure character name and server name are spelt corerctly.")
            return

        data = response.json()

        self.covenant = data['chosen_covenant']['name']

        for soulbind in data['soulbinds']:
            if not ('is_active' in soulbind.keys() and soulbind['is_active']):
                continue

            for trait in soulbind['traits']:
                z = 3

            y =2






        x = 1

    @staticmethod
    def DiminishSecondaryStat():
        pass
        

my_char = Character("illidan", "agaruoth")