import requests
from pathlib import Path
import json
import os
import time
import pandas as pd


# from https://github.com/paulbilnoski/StarTrekTimelinesSpreadsheet/blob/26fd2f94c151542d0e02c9149a70240b93a9309a/src/api/CONFIG.ts
# ----- START -----
URL_PLATFORM = 'https://thorium.disruptorbeam.com/'
URL_SERVER = 'https://stt.disruptorbeam.com/'
URL_CDN = 'https://stt-cdn-services.s3.amazonaws.com/'

# default client_id of the Facebook client - used for login only
CLIENT_ID = '322613001274224'
CLIENT_API_VERSION = 15
CLIENT_VERSION = '7.5.2'
CLIENT_PLATFORM = 'webgl'
# ----- END -----


SUBFOLDER_NAME = 'Star Trek Timelines'
AUTH_TOKEN_FILENAME = 'STT auth token.txt'
USERPASS_FILENAME = "STT website login.txt"
PLAYER_JSON_FILENAME = 'STT player data.json'
FACTION_EVENT_FILENAME = 'Faction event - {}.csv'
GALAXY_EVENT_FILENAME = 'Galaxy event - {}.csv'
ACCESS_TOKEN = 'access_token'
PLAYER_URL = URL_SERVER + 'player'
AUTH_URL = URL_PLATFORM + 'oauth2/token'
SECONDS_PER_DAY = 60*60*24
KEEP_HIDDEN_TRAITS = True


def read_auth_token_from_file():
    print('Reading auth token from file...')
    authtoken = None
    filepath = Path.home().joinpath(SUBFOLDER_NAME, AUTH_TOKEN_FILENAME)
    if filepath.exists():
        with open(filepath) as f:
            authtoken = f.readline().strip()

    if authtoken is not None and len(authtoken) < 1:
        authtoken = None

    return authtoken


def write_auth_token_to_file(authtoken):
    print('Writing auth token to file...')
    filepath = Path.home().joinpath(SUBFOLDER_NAME, AUTH_TOKEN_FILENAME)
    with open(filepath, 'w') as f:
        f.write(authtoken)


def read_creds_from_file():
    print('Reading creds from file...')
    username = None
    password = None
    home = Path.home()
    filepath = home.joinpath(SUBFOLDER_NAME, USERPASS_FILENAME)
    if filepath.exists():
        with open(filepath) as f:
            username = f.readline().strip()
            password = f.readline().strip()

        if len(username) < 1:
            username = None
        if len(password) < 1:
            password = None

    if username is None or password is None:
        print('\nPlease create a text file named "{}" in folder {}\n'.format(USERPASS_FILENAME,
                home.joinpath(SUBFOLDER_NAME)) +
                'with your username on the first line and your password on the second line, like this:\n' +
                '{}\nContents:\nusername\npassword\n'.format(filepath))

    return username, password


def login(username, password):
    print('Logging in...')
    headers = {'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    form = {'username': username, 'password': password, 'client_id': CLIENT_ID, 'grant_type': 'password'}
    resp = requests.post(AUTH_URL, headers=headers, data=form)
    resp.raise_for_status()
    j = json.loads(resp.content)
    if ACCESS_TOKEN not in j or len(j[ACCESS_TOKEN]) < 10:
        return None
    else:
        return j[ACCESS_TOKEN]


def get_game_data(authtoken):
    print('Getting player data...')
    form = {'client_api': CLIENT_API_VERSION, ACCESS_TOKEN: authtoken}
    resp = requests.get(PLAYER_URL, data=form)
    resp.raise_for_status()
    return json.loads(resp.content)


def write_game_data_to_file(player):
    print('Writing player data to file...')
    filepath = Path.home().joinpath(SUBFOLDER_NAME, PLAYER_JSON_FILENAME)
    with open(filepath, 'w') as f:
        json.dump(player, f, indent=3)


def read_game_data_from_file():
    print('Reading player data from file...')
    player = None
    filepath = Path.home().joinpath(SUBFOLDER_NAME, PLAYER_JSON_FILENAME)
    if filepath.exists():
        with open(filepath) as f:
            player = json.load(f)

    if player is not None and len(player) < 1:
        player = None

    return player


def get_game_data_age():
    filepath = Path.home().joinpath(SUBFOLDER_NAME, PLAYER_JSON_FILENAME)
    if filepath.exists():
        last_modified = os.path.getmtime(filepath)
        return (time.time()-os.path.getmtime(filepath))/SECONDS_PER_DAY
    else:
        return 99999999


class StaticGameData:

    # Item source types
    class __ItemSourceTypes:
        @property
        def AWAY_TEAM(self):
            return 0

        @property
        def FACTION_ONLY(self):
            return 1

        @property
        def SPACE_BATTLE(self):
            return 2

        @property
        def RARE_REWARD(self):
            return 3

    ITEM_SOURCE_TYPES = __ItemSourceTypes()

    SKILL_TO_SHORT_SKILL = { 'command': 'CMD', 'diplomacy': 'DIP', 'security': 'SEC', 'science': 'SCI',
                             'engineering': 'ENG', 'medicine': 'MED' }

    GALAXY_EVENT_RECIPE_NAME_WIKI_CORRECTIONS = {
        4937: 'Listening Device 2',
        'Debate Strategy': 'Debate Strategy 2',
        'Raw Materials': 'Raw Materials 2',
        'Ethical Subroutine': 'Ethical Subroutine 2'
    }

    # this data isn't in the JSON
#    MISSIONS_PER_EPISODE = {'E1': 14, 'E2': 19, 'E3': 5, 'E4': 14, 'E5': 18, 'E6': 4, 'E7': 13, 'E8': 14, 'E9': 4,
#                            'E10': 7, 'DE': 8, 'CT': 8, 'KE': 5, 'IN': 8, '??': 100000}

    # some item sources are missing the dispute value for unclear reasons, so this is a workaround
    __MISSION_INFO_FOR_ID = {
        91:  ('E1', 'M1', 'The Wrong Crowd'),
        93:  ('E1', 'M2', 'His Own Man'),
        94:  ('E1', 'M3', 'The Prodigal Son'),
        85:  ('E1', 'M4', 'Assault and Battery'),
        89:  ('E1', 'M5', 'On Their Heels'),
        90:  ('E1', 'M6', 'A Father Figure'),
        80:  ('E1', 'M7', 'Pillage and Plunder'),
        79:  ('E1', 'M8', 'Beyond the Call'),
        78:  ('E1', 'M9', 'Double Trouble'),
        102: ('E1', 'M10', 'Stolen Honor'),
        105: ('E1', 'M11', 'Behind Closed Doors'),
        104: ('E1', 'M12', 'A Logical Response'),
        101: ('E1', 'M13', 'Right of Conquest'),
        76:  ('E1', 'M14A', 'Cleansing Fire'),
        100: ('E1', 'M14B', 'Hook Or By Crook'),

        53:  ('E2', 'M1', 'Under New Management'),
        58:  ('E2', 'M2', 'The Vedek\'s Trail'),
        59:  ('E2', 'M3', 'The Army of Anaydis'),
        60:  ('E2', 'M4', 'The Mad Vedek'),
        40:  ('E2', 'M5', 'Manna from Heaven'),
        38:  ('E2', 'M6', 'Not A Drop to Drink'),
        39:  ('E2', 'M7', 'Hot Pursuit'),
        42:  ('E2', 'M8', 'Rescue the Val Jean'),
        45:  ('E2', 'M9', 'Maquis Incitement'),
        41:  ('E2', 'M10', 'The Walls Have Ears'),
        68:  ('E2', 'M11', 'Off at the Pass'),
        71:  ('E2', 'M12', 'Internal Dispute'),
        49:  ('E2', 'M13', 'For His Own Good'),
        48:  ('E2', 'M14', 'Cardassian Hospitality'),
        52:  ('E2', 'M15', 'Temporary Hold'),
        30:  ('E2', 'M16', 'Picking the Bones'),
        32:  ('E2', 'M17', 'Pretense of Mercy'),
        31:  ('E2', 'M18', 'A Popular Item'),
        62:  ('E2', 'M19A', 'The Toss'),
        73:  ('E2', 'M19B', 'Man With a Plan'),
        64:  ('E2', 'M19C', 'A New Recruit'),

        227: ('E3', 'M1', 'Family Squabble'),
        233: ('E3', 'M2', 'Cytherian Highway'),
        234: ('E3', 'M3', 'A Singular Occurrence'),
        235: ('E3', 'M4', 'Organian Aid'),
        237: ('E3', 'M5', 'Rockslide'),

        191: ('E4', 'M1', 'Ishka Issues'),
        185: ('E4', 'M2', 'Not Without A Fight'),
        188: ('E4', 'M3', 'A Kazon Scorned'),
        189: ('E4', 'M4', 'Common Ground'),
        179: ('E4', 'M5', 'Going Viral'),
        181: ('E4', 'M6', 'Self Control'),
        183: ('E4', 'M7', 'Mutual Assured Destruction'),
        203: ('E4', 'M8', 'Arms Race'),
        205: ('E4', 'M9', 'Fan Club'),
        204: ('E4', 'M10', 'Trial by Fire'),
        198: ('E4', 'M11', 'He Means Well'),
        199: ('E4', 'M12', 'For the People'),
        200: ('E4', 'M13', 'With Friends Like These'),
        195: ('E4', 'M14A', 'Putting the Free in Freedom'),
        193: ('E4', 'M14B', 'Smiles and Knives'),

        261: ('E5', 'M1', 'Quell the Riots'),
        257: ('E5', 'M2', 'A Bold Move'),
        254: ('E5', 'M3', 'Coursing Hounds'),
        255: ('E5', 'M4', 'Race to the Finish'),
        247: ('E5', 'M5', 'Blunting the Dagger'),
        245: ('E5', 'M6', 'Secure the Chavez'),
        243: ('E5', 'M7', 'Salvage the Chavez'),
        249: ('E5', 'M8', 'Act of Betrayal'),
        269: ('E5', 'M9', 'Control Over Chaos'),
        262: ('E5', 'M10', 'Proof of Concept'),
        267: ('E5', 'M11', 'Saving Smiley O\'Brien'),
        265: ('E5', 'M12', 'Into His Own Hands'),
        276: ('E5', 'M13', 'Instant Intervention'),
        272: ('E5', 'M14', 'Back to School'),
        275: ('E5', 'M15', 'Turncoat Outpost'),
        270: ('E5', 'M16', 'Baited Hook'),
        273: ('E5', 'M17', 'Long Live the King'),
        241: ('E5', 'M18A', 'Thy Enemy\'s Secrets'),
        250: ('E5', 'M18B', 'The Annihilation Syndrome'),

        221: ('E6', 'M1', 'The Rings of Time'),
        225: ('E6', 'M2', 'Ancient Guardians'),
        224: ('E6', 'M3', 'Too Greedily and Too Deep'),
        220: ('E6', 'M4', 'The Time Transporter'),

        310: ('E7', 'M1', 'Improvised Entry'),
        311: ('E7', 'M2', 'Battle Shinzon'),
        309: ('E7', 'M3', 'Material Assistance'),
        297: ('E7', 'M4', 'The Raptors\' Fury'),
        299: ('E7', 'M5', 'Right Place, Wrong Time'),
        300: ('E7', 'M6', 'Striking at Shadows'),
        316: ('E7', 'M7', 'One Future Ends'),
        319: ('E7', 'M8', 'Retroactive Vengeance'),
        322: ('E7', 'M9', 'Researching Future History'),
        313: ('E7', 'M10', 'Trust Issues'),
        314: ('E7', 'M11', 'Hounded'),
        315: ('E7', 'M12', 'Lost Legacy'),
        324: ('E7', 'M13A', 'Garak\'s Gamble'),
        303: ('E7', 'M13B', 'Death\'s Endeavor'),

        146: ('E8', 'M1', 'Evacuation Orders'),
        142: ('E8', 'M2', 'Change of Scenery'),
        144: ('E8', 'M3', 'Field Modifications'),
        145: ('E8', 'M4', 'Shielding the Prey'),
        148: ('E8', 'M5', 'The Verge of Destruction'),
        149: ('E8', 'M6', 'Surveying the Sphere'),
        150: ('E8', 'M7', 'The Vanguard\'s Challenge'),
        159: ('E8', 'M8', 'Boardroom Politics'),
        157: ('E8', 'M9', 'Ostensible Proof'),
        156: ('E8', 'M10', 'Back Into the Fold'),
        161: ('E8', 'M11', 'Uprising'),
        160: ('E8', 'M12', 'Feed A Fever'),
        163: ('E8', 'M13', 'Lashing Out'),
        152: ('E8', 'M14A', 'Proven Toxicity'),
        167: ('E8', 'M14B', 'Going Viral'),

        784: ('E9', 'M1', 'Rapid Response'),
        780: ('E9', 'M2', 'Into the Lion\'s Den'),
        778: ('E9', 'M3', 'Kicking the Nest'),
        782: ('E9', 'M4A', 'Bearing Up'),
        777: ('E9', 'M4B', 'Scatter Thine Enemies'),

        214: ('E10', 'M1', 'Fool Me Twice'),
        216: ('E10', 'M2', 'Highway to Hell'),
        210: ('E10', 'M3', 'Ruinous Staycation'),
        837: ('E10', 'M4', 'Flash of Lightning'),
        843: ('E10', 'M5', 'An Infinite Welcome'),
        842: ('E10', 'M6', 'Into the Cave'),
        838: ('E10', 'M7', 'Our Harshest Critic'),

        132: ('DE', 'M1', 'Long Distance Call'),
        128: ('DE', 'M2', 'A Tale of Forgotten Lore'),
        135: ('DE', 'M3', 'Highwaymen'),
        126: ('DE', 'M4', 'A Time of Morn-ing'),
        133: ('DE', 'M5', 'Indiscriminate Mind'),
        125: ('DE', 'M6', 'Mortals and Mayhem'),
        134: ('DE', 'M7', 'Death in Battle'),
        120: ('DE', 'M8', 'Iconian Insider'),

        139: ('CT', 'M1', 'Warranted Pursuit'),
        129: ('CT', 'M2', 'Rabid Fans'),
        130: ('CT', 'M3', 'Pirate Problems'),
        117: ('CT', 'M4', 'The Professor\'s Deadline'),
        137: ('CT', 'M5', 'Death Throes'),
        121: ('CT', 'M6', 'Serious Business'),
        140: ('CT', 'M7', 'No Returns Accepted'),
        123: ('CT', 'M8', 'Operation Isolate'),

        551: ('KE', 'M1', 'Leverage'),
        550: ('KE', 'M2', 'Stolen Command'),
        548: ('KE', 'M3', 'Dogs of War'),
        549: ('KE', 'M4', 'A Ticking Bomb'),
        552: ('KE', 'M5', 'All Sales Are Final'),

        721: ('IN', 'M1', 'Xahean Invasion'),
        720: ('IN', 'M2', 'The Price of Friendship'),
        739: ('IN', 'M3', 'Empty Vessel'),
        738: ('IN', 'M4', 'Zora\'s Invitation'),
        743: ('IN', 'M5', 'Starved for Attention'),
        744: ('IN', 'M6', 'Bottom Feeders'),
        763: ('IN', 'M7', 'Stealing the Stars'),
        762: ('IN', 'M8', 'Mudd\'s Enterprise'),
    }

    @classmethod
    def get_string_for_mission_id(cls, mission_id):
        return f'{cls.__MISSION_INFO_FOR_ID[mission_id][0]}-{cls.__MISSION_INFO_FOR_ID[mission_id][1]} ' \
               f'{cls.__MISSION_INFO_FOR_ID[mission_id][2]}'


class Utilities:

    @staticmethod
    def get_wiki_text_for_skills(skills, skills_AND):
        if skills_AND is None:
            assert len(skills) == 1, skills
            skill_string = f'{{{{Skill|{StaticGameData.SKILL_TO_SHORT_SKILL[skills[0]]}}}}}'
        elif skills_AND:
            assert len(skills) == 2, skills
            skill_string = f'{{{{SkillMultiple|{StaticGameData.SKILL_TO_SHORT_SKILL[skills[0]]}' \
                                   f'|and|{StaticGameData.SKILL_TO_SHORT_SKILL[skills[1]]}}}}}'
        else:
            assert len(skills) == 2, skills
            skill_string = f'{{{{SkillMultiple|{StaticGameData.SKILL_TO_SHORT_SKILL[skills[0]]}' \
                                   f'|or|{StaticGameData.SKILL_TO_SHORT_SKILL[skills[1]]}}}}}'

        return skill_string


class Faction:

    def __init__(self):
        self.id = -1
        self.name = None
        self.reputation = -1
        self.discovered = -1
        self.completed_shuttle_adventures = -1
        self.shuttle_token_id = -1


class FactionsData:
    '''
    JSON structure (of interest):
    player
        character
            factions
                <list item>
                    id
                    name
                    reputation
                    discovered                          <-- 1 for yes, 0? for no
                    completed_shuttle_adventures
                    shuttle_token_id
                <list item>
                ...
    '''

    __ATTR_OF_INTEREST = set(['id', 'name', 'reputation', 'discovered', 'completed_shuttle_adventures', 'shuttle_token_id'])
    __STATIC_REFERENCE_TO_DATA = None

    def __init__(self, game_data_player, *, debug=False):
        FactionsData.__STATIC_REFERENCE_TO_DATA = self
        self.factions = {}
        self.__shuttle_token_id_to_faction_id = {}
        self._raw_data = game_data_player['character']['factions']
        print(f'Parsing {len(self._raw_data)} factions...')
        for faction_data in self._raw_data:
            fac = Faction()
            for k in faction_data:
                if k in self.__ATTR_OF_INTEREST:
                    fac.__setattr__(k, faction_data[k])
            self.factions[fac.id] = fac
            self.__shuttle_token_id_to_faction_id[fac.shuttle_token_id] = fac.id

    def get_transmission_name_for_shuttle_token_id(self, shuttle_token_id):
        print(sorted(self.factions.keys()))
        return self.factions[self.__shuttle_token_id_to_faction_id[shuttle_token_id]].name + ' Transmission'

    @classmethod
    def get_transmission_name_for_shuttle_token_id_static(cls, shuttle_token_id):
        assert cls.__STATIC_REFERENCE_TO_DATA is not None
        return cls.__STATIC_REFERENCE_TO_DATA.get_transmission_name_for_shuttle_token_id(shuttle_token_id)

    @classmethod
    def get_faction_name_for_id_static(cls, faction_id):
        assert cls.__STATIC_REFERENCE_TO_DATA is not None
        return cls.__STATIC_REFERENCE_TO_DATA.factions[faction_id].name


class ItemSource:

    def __init__(self):
        self.type = -1
        self.id = -1
        self.name = None
        self.energy_quotient = -1
        self.chance_grade = -1
        # I thought mastery: 0 is normal, 1 is elite, 2 is epic but now I'm not sure
        self.mastery = -1

        # I thought the following was the case, but it is not!  I don't know what the JSON mission is!
        # JSON mission is the mission number anti-mod number of missions in the episode.
        # for example, episode 7 has 13 missions, so mission 33 is M7-E7
        # weirdly, sometimes the JSON mission is multiples of the number of missions, but the mod still works
        # for example, E6-M3 is JSON mission 19 even though there are only 4 missions in E6 (but 19%4=3 so it's ok)
#        self.episode = None
#        self.mission = None

        # I'm not sure what dispute is...
#        self.dispute = None

    def is_rare_reward(self):
        return self.type == StaticGameData.ITEM_SOURCE_TYPES.RARE_REWARD

    def is_faction_only(self):
        return self.type == StaticGameData.ITEM_SOURCE_TYPES.FACTION_ONLY

    def __str__(self):
        if self.is_faction_only():
            return FactionsData.get_transmission_name_for_shuttle_token_id_static(self.id)
        else:
            return f'{StaticGameData.get_string_for_mission_id(self.id)}' + \
                   (' (Rare reward)' if self.is_rare_reward() else '')


class Item:

    def __init__(self):
        self.id = -1
        self.symbol = None
        self.type = -1
        self.name = None
        self.rarity = -1
        self.quantity = 0
        # recipe = dict of demands; archetype_id: count
        self.recipe = None
        # sources = list of missions; id, name, energy_quotient, chance_grade
        self.sources = None
        self.bonuses = None

        # Skills and trait bonuses are for galaxy event items
        self.jackpot_skills = None
        self.jackpot_skills_AND = None
        self.jackpot_trait_bonuses = None

    def __str__(self):
        return str(f'{self.rarity}* {self.name}')

    def get_sources_string(self, *, include_rare_rewards=False, tab_count=0):
        if self.sources is None:
            return None

        source_strings = []
        for src in self.sources:
            if src.is_rare_reward() and not include_rare_rewards:
                continue

            mission_string = str(src)
            if not src.is_faction_only():
                assert mission_string.find(src.name) > 0, f'{mission_string}\n{src.name}'
            source_strings.append(f'\t{mission_string}')

        tabs = '\t' * tab_count
        print(f'{len(source_strings)} sources:')
        for s in source_strings:
            print(f'\t{s}')
        return f'{tabs}{len(source_strings)} sources:\n' + f'\n{tabs}'.join(source_strings)

    def get_recipe_data_for_csv(self):
        if self.recipe is None:
            return None

        demands = []
        for item_id, qty_needed in self.recipe.items():
            item = ItemsData.get_item_by_archetype_id_static(item_id)
            demands.append([item_id, str(item), item.quantity, qty_needed])
        return demands

    def get_recipe_string(self, *, tab_count=0):
        if self.recipe is None:
            return None

        tabs = '\t' * tab_count
        demand_strings = []
        for item_id, count in self.recipe.items():
            item = ItemsData.get_item_by_archetype_id_static(item_id)
            demand_strings.append(f'{tabs}{count} of {item}')

        if self.jackpot_skills is not None:
            if self.jackpot_skills_AND is None:
                assert len(self.jackpot_skills) == 1, self.jackpot_skills
                jackpot_skill_string = f'{tabs}Bonus skills: {self.jackpot_skills[0]}\n'
            elif self.jackpot_skills_AND:
                assert len(self.jackpot_skills) == 2, self.jackpot_skills
                jackpot_skill_string = f'{tabs}Bonus skills: {self.jackpot_skills[0]} AND {self.jackpot_skills[1]}\n'
            else:
                assert len(self.jackpot_skills) == 2, self.jackpot_skills
                jackpot_skill_string = f'{tabs}Bonus skills: {self.jackpot_skills[0]} OR {self.jackpot_skills[1]}\n'
        else:
            jackpot_skill_string = ''

        if self.jackpot_trait_bonuses is not None:
            assert len(self.jackpot_trait_bonuses) == 2, self.jackpot_trait_bonuses
            jackpot_trait_bonuses_string = f'{tabs}Bonus traits: {", ".join(self.jackpot_trait_bonuses)}\n'
        else:
            jackpot_trait_bonuses_string = ''

        return jackpot_skill_string + jackpot_trait_bonuses_string + \
               f'{tabs}Recipe of {len(demand_strings)} demands:\n\t' + f'\n\t'.join(demand_strings)

    def get_galaxy_item_wiki_text(self):
        assert self.jackpot_skills is not None, f'{self.id}: {self.name}'
        assert self.jackpot_trait_bonuses is not None, f'{self.id}: {self.name}'
        assert len(self.jackpot_trait_bonuses) == 2, self.jackpot_trait_bonuses

        jackpot_skill_string = Utilities.get_wiki_text_for_skills(self.jackpot_skills, self.jackpot_skills_AND)
        jackpot_trait_bonuses_string = f'trait1 = {self.jackpot_trait_bonuses[0].title()}| ' \
                                       f'trait2 = {self.jackpot_trait_bonuses[1].title()}'.replace('_', ' ')

        if self.id in StaticGameData.GALAXY_EVENT_RECIPE_NAME_WIKI_CORRECTIONS:
            name = StaticGameData.GALAXY_EVENT_RECIPE_NAME_WIKI_CORRECTIONS[self.id]
        elif self.name in StaticGameData.GALAXY_EVENT_RECIPE_NAME_WIKI_CORRECTIONS:
            name = StaticGameData.GALAXY_EVENT_RECIPE_NAME_WIKI_CORRECTIONS[self.name]
            print('--------')
            print('WARNING: Verify and update StaticGameData.GALAXY_EVENT_RECIPE_NAME_WIKI_CORRECTIONS with ')
            print(f'{self.id} for {name}')
            print('--------')
        else:
            name = self.name

        return f'| {{{{Galaxy/Recipe | skill = {{{{{jackpot_skill_string}}}}} | {jackpot_trait_bonuses_string}| ' \
               f'recipename = {name}}}}}'


class ItemsData:
    '''
    JSON structure (of interest):
    player
        character
            items
                <list item>
                    archetype_id
                    quantity
    item_archetype_cache
        archetypes
            <list item>
                id
                symbol
                type
                name
                rarity
                recipe
                    demands
                        <list item>
                            archetype_id
                            count
                        <list item>
                        ...
                    validity_hash
                    jackpot             <-- this section for galaxy event items
                        skills
                            <list item>
                            --> 1 string of 1 skill, if only one skill for the building bonus
                            --> 1 string of 2 skills, if one skill AND another skill for the building bonus
                            --> 2 strings of 2 skills (1 each), if one skill OR another skill for the building bonus
                        trait_bouses
                            <trait>: 0.05 (5% bonus)
                            <trait>: 0.05
                item_sources
                    <list item>
                        challenge_id            <-- ignore; refers to away team mission crit nodes
                        challenge_skill         <-- ignore; refers to away team mission crit nodes
                        challenge_difficulty    <-- ignore; refers to away team mission crit nodes
                        type: 0 (away team) or 2 (space battle)
                        id
                        name
                        energy_quotient
                        chance_grade (1-5? number of pips displayed?)
                        place
                        mission
                        mastery
                    <list item> (faction)
                        type: 1
                        id
                        name: <faction name> Transmission
                        energy_quotient
                        chance_grade
                    <list item>
                    ...
                bonuses (optional?)
                    "<number>":<number> (not sure what these are)
                    "<number>":<number>
                    ...
            <list item>
            ...
    '''

    __ID_KEY = 'id'
    __SYMBOL_KEY = 'symbol'
    __NAME_KEY = 'name'
    __TYPE_KEY = 'type'
    __RARITY_KEY = 'rarity'
    __RECIPE_KEY = 'recipe'
    __DEMANDS_KEY = 'demands'
    __ARCHETYPE_ID_KEY = 'archetype_id'
    __COUNT_KEY = 'count'
    __ITEM_SOURCES_KEY = 'item_sources'
    __ENERGY_QUOTIENT_KEY = 'energy_quotient'
    __CHANCE_GRADE_KEY = 'chance_grade'
    __MISSION_KEY = 'mission'
    __DISPUTE_KEY = 'dispute'
    __MASTERY_KEY = 'mastery'
    __BONUSES_KEY = 'bonuses'
    __JACKPOT_KEY = 'jackpot'
    __JACKPOT_SKILLS_KEY = 'skills'
    __JACKPOT_TRAIT_BONUSES_KEY = 'trait_bonuses'

    __STATIC_REFERENCE_TO_DATA = None

    def __init__(self, game_data_items, game_data_player, *, debug=False):
        ItemsData.__STATIC_REFERENCE_TO_DATA = self
        self._raw_data = game_data_items
        self.items = {}
        print('Parsing {} items...'.format(len(game_data_items)))
        missing_missions = set()
        for item_data in self._raw_data:
            item = Item()
            item.id = item_data[self.__ID_KEY]
            item.symbol = item_data[self.__SYMBOL_KEY]
            item.type = item_data[self.__TYPE_KEY]
            item.name = item_data[self.__NAME_KEY]
            item.rarity = item_data[self.__RARITY_KEY]

            if self.__RECIPE_KEY in item_data and len(item_data[self.__RECIPE_KEY]) > 0:
                item.recipe = {}
                for demand in item_data[self.__RECIPE_KEY][self.__DEMANDS_KEY]:
                    item.recipe[demand[self.__ARCHETYPE_ID_KEY]] = demand[self.__COUNT_KEY]
                if self.__JACKPOT_KEY in item_data[self.__RECIPE_KEY]:
                    jackpot = item_data[self.__RECIPE_KEY][self.__JACKPOT_KEY]
                    assert self.__JACKPOT_SKILLS_KEY in jackpot
                    assert self.__JACKPOT_TRAIT_BONUSES_KEY in jackpot

                    item.jackpot_skills = []
                    jackpot_skills = jackpot[self.__JACKPOT_SKILLS_KEY]
                    if len(jackpot_skills) == 1:
                        # Either one skill, or one skill AND another skill
                        jackpot_skills = jackpot_skills[0]
                        if jackpot_skills.find(',') > 0:
                            # one skill AND another skill
                            item.jackpot_skills.extend([js.split('_')[0] for js in jackpot_skills.split(',')])
                            item.jackpot_skills_AND = True
                        else:
                            # one skill only
                            item.jackpot_skills.append(jackpot_skills.split('_')[0])
                    else:
                        # one skill OR another skill
                        assert len(jackpot_skills) == 2, jackpot_skills
                        item.jackpot_skills.extend([js.split('_')[0] for js in jackpot_skills])
                        item.jackpot_skills_AND = False

                    jackpot_trait_bonuses = jackpot[self.__JACKPOT_TRAIT_BONUSES_KEY]
                    assert len(jackpot_trait_bonuses) == 2, jackpot_trait_bonuses
                    item.jackpot_trait_bonuses = []
                    for jtb, bonus in jackpot_trait_bonuses.items():
                        assert bonus == 0.05, jackpot_trait_bonuses
                        item.jackpot_trait_bonuses.append(jtb)

            if len(item_data[self.__ITEM_SOURCES_KEY]) > 0:
                item.sources = []
                for src in item_data[self.__ITEM_SOURCES_KEY]:
                    item_source = ItemSource()
                    item_source.type = src[self.__TYPE_KEY]
                    item_source.id = src[self.__ID_KEY]
                    item_source.name = src[self.__NAME_KEY]
                    item_source.energy_quotient = src[self.__ENERGY_QUOTIENT_KEY]
                    item_source.chance_grade = src[self.__CHANCE_GRADE_KEY]
                    if self.__DISPUTE_KEY in src:
                        item_source.dispute = src[self.__DISPUTE_KEY]
                    if not item_source.is_faction_only():
                        item_source.mastery = src[self.__MASTERY_KEY]

                    item.sources.append(item_source)

            if self.__BONUSES_KEY in item_data:
                self.bonuses = item_data[self.__BONUSES_KEY]

            self.items[item.id] = item

        for item_data in game_data_player['character']['items']:
            if item_data['archetype_id'] in self.items:
                the_item = self.items[item_data['archetype_id']]
                the_item.quantity = item_data['quantity']
                print(f'Set {the_item.id} {the_item} quantity to {the_item.quantity}')
#                self.items[the_item.id] = the_item
            else:
                print(f'Item {item_data["archetype_id"]} {item_data["rarity"]}* {item_data["name"]} not found in item archetypes')

        print(f'Found {len(self.items)} items')

        for mission_id in sorted(missing_missions):
            print(f'Need episode for mission id {mission_id} added to EPISODE_FOR_MISSION_ID dict')

    @classmethod
    def get_item_by_archetype_id_static(cls, archetype_id):
        assert cls.__STATIC_REFERENCE_TO_DATA is not None
        return cls.__STATIC_REFERENCE_TO_DATA.items[archetype_id]


class GameEvent:
    def __init__(self, event_data_json, *, debug=False):
        self._raw_data = event_data_json
        self.crew_bonuses = None

        print(f'Parsing event "{event_data_json["name"]}"... ')   #, end='')
        self.id = event_data_json['id']
        self.name = event_data_json['name']
        self.description = event_data_json['description']
        # Content type is "gather" for galaxy events and "shuttles" for faction events
        self.content_type = event_data_json['content']['content_type']

        self.featured_crew = []
        for f_crew in event_data_json['featured_crew']:
            self.featured_crew.append(f_crew['id'])
            if debug:
                print(f'Featured crew: {f_crew["id"]} {f_crew["full_name"]}')

    def print_event_crew(self):
        if len(self.featured_crew) == 0:
            print('No featured event crew found')
        else:
            for f_crew in self.featured_crew:
                print(f'Featured crew: {f_crew["id"]} {f_crew["full_name"]}')

        if len(self.crew_bonuses) == 0:
            print('No bonus crew found')
        else:
            for crew_name, bonus in self.crew_bonuses.items():
                print(f'Bonus crew: {crew_name}: {bonus}')


class FactionShuttleSeat:

    def __init__(self, seat_data):
        self.level = seat_data['level']
        self.required_trait = seat_data['required_trait']
        self.trait_bonuses = seat_data['trait_bonuses']

        # 1 string of 1 skill, if only one skill for the building bonus
        # 1 string of 2 skills, if one skill AND another skill for the building bonus
        # 2 strings of 2 skills (1 each), if one skill OR another skill for the building bonus
        if len(seat_data['skills']) == 2:
            self.skills = [skill[:-6] for skill in seat_data['skills']]
            self.skills_AND = False
        else:
            self.skills = [skill[:-6] for skill in seat_data['skills'][0].split(',')]
            if len(self.skills) == 2:
                self.skills_AND = False
            else:
                self.skills_AND = None

    def __str__(self):
        if len(self.skills) == 1:
            s = self.skills[0]
        elif self.skills_AND:
            s = f'{self.skills[0]} AND {self.skills[1]}'
        else:
            s = f'{self.skills[0]} OR {self.skills[1]}'
        if self.trait_bonuses is not None and len(self.trait_bonuses) > 0:
            s += '; bonus traits: ' + ', '.join(self.trait_bonuses)
        return s


class FactionShuttleMission:

    def __init__(self, shuttle_data, *, debug=False):
        assert len(shuttle_data['shuttles']) == 1, len(shuttle_data['shuttles'])

        self.id = shuttle_data['id']
        self.name = shuttle_data['name']
        self.faction_id = shuttle_data['faction_id']
        self.challenge_rating = shuttle_data['challenge_rating']
        self.completes_in_seconds = shuttle_data['completes_in_seconds']
        self.description = shuttle_data['shuttles'][0]['description']
        self.state = shuttle_data['shuttles'][0]['state']
        self.expires_in = shuttle_data['shuttles'][0]['expires_in']
        self.is_rental = shuttle_data['shuttles'][0]['is_rental']
        self.seats = [FactionShuttleSeat(seat) for seat in shuttle_data['shuttles'][0]['slots']]

        if debug:
            print(f'Event shuttle: {FactionsData.get_faction_name_for_id_static(self.faction_id)}, '
                  f'{self.name}, {self.state}')
            for seat in self.seats:
                print(f'\t{seat}')

    def __str__(self):
        return self.name


class FactionEvent(GameEvent):
    '''
    JSON structure (of interest):
    action
    player
        character
            events
                <list item>             <-- presumably only one element in the list
                    id
                    name
                    description
                    featured_crew
                        <list item>
                            id
                            name
                            full_name
                            rarity
                            skills
                                science_skill
                                    core
                                    range_min
                                    range_max
                                diplomacy_skill
                                command_skill
                            traits
                        <list item>
                        ...
                    content
                        content_type: "gather" (for galaxy events), "shuttles" (for faction events)
                        shuttles
                            <list item>         <-- one per faction in the event
                                crew_bonuses    <-- dict
                                    <crew name>: <bonus multiplier: 2 or 3>
                            <list item>
                            ...
            shuttle_adventures
                <list item>             <-- one per (open?) shuttle mission
                    id
                    name
                    challenge_rating: 1500.0    <-- 1500.0 for 4000 point shuttles
                    completes_in_seconds: 10800     <-- 10800 for 3 hour shuttles
                    shuttles
                        <list item>             <-- one list item in shuttles
                            id
                            name
                            description
                            state: 0|1|?            <-- 0 is not started, 1 is in progress (I assume)
                            expires_in: 38258.667170789 (seconds?)
                            faction_id
                            is_rental: false|true
                            slots
                                <list item>
                                    level: null
                                    required_trait: null
                                    skills:
                                        <list item>     <-- one or two skills
                                            skill       <-- e.g., diplomacy_skill
                                    trait_bonuses       <-- dict; no entries?
    '''

    def __init__(self, event_data_json, raw_data_shuttles, *, debug=False):
        super().__init__(event_data_json, debug=debug)
        assert self.content_type == 'shuttles', self.content_type

        self.crew_bonuses = event_data_json['content']['shuttles'][0]['crew_bonuses']
        if debug:
            if len(self.crew_bonuses) == 0:
                print('No bonus crew found')
            else:
                for crew_name, bonus in self.crew_bonuses.items():
                    print(f'Bonus crew: {crew_name}: {bonus}')

        self._raw_data_shuttles = raw_data_shuttles
        self.missions = [FactionShuttleMission(shuttle_data, debug=debug) for shuttle_data in raw_data_shuttles]

        print(f'Got {len(self.missions)} faction event shuttle missions')

    def get_wiki_text(self):
        ''' Wiki format for each shuttle mission:
        | name
        | {{SkillMultiple|ENG|and|SCI}} || {{Skill|DIP}} || {{Skill|MED}} || {{SkillMultiple|DIP|and|SCI}} ||
        | description
        | style="color:lightgreen;" | SUCCESS TEXT
        | style="color:darkorange;" | FAIL TEXT
        |-
        '''

        missions_by_faction = {}
        for mission in self.missions:
            s = f'|-\n| {mission.name}\n| '
            s += ' || '.join([Utilities.get_wiki_text_for_skills(seat.skills, seat.skills_AND) for seat in mission.seats])
            s += ' || ' * (5 - len(mission.seats)) + '\n'
            s += f'| {mission.description}\n'
            s += '| style="color:lightgreen;" | SUCCESS TEXT\n| style="color:darkorange;" | FAIL TEXT'

            if mission.faction_id not in missions_by_faction:
                missions_by_faction[mission.faction_id] = {}
            missions_by_faction[mission.faction_id][mission.name] = s

        s = ''
        for faction_id, missions in missions_by_faction.items():
            s += f'\n-------------\n{FactionsData.get_faction_name_for_id_static(faction_id)} missions:\n'
            s += '\n'.join([missions[mission_name] for mission_name in sorted(missions.keys())]) + '\n'

        return s


class EventData:

    def __init__(self, game_data_player, *, debug=False):
        raw_data = game_data_player['character']['events']
        self.event = None

        if len(raw_data) == 0:
            print('No event data found')
            return

        if len(raw_data) > 1:
            print(f'WARNING: Expected 0 or 1 events, found {len(raw_data)}; ignoring all but the first')
        raw_data = raw_data[0]

        if raw_data['content']['content_type'] == 'shuttles':
            self.event = FactionEvent(raw_data, game_data_player['character']['shuttle_adventures'], debug=debug)
        elif raw_data['content']['content_type'] == 'gather':
            self.event = GalaxyEvent(raw_data, debug=debug)
        else:
            print(f"WARNING: Found unexpected event of expected type: {raw_data['content']['content_type']}")
            return


class Adventure:

    def __init__(self, adventure_data, *, debug=False):
        self.id = adventure_data['id']
        self.name = adventure_data['name']
        self.description = adventure_data['description']
        self.is_golden_octopus = adventure_data['golden_octopus']

        # demands is a list of dicts with keys archetype_id and count
        self.demands = {}
        for demand_data in adventure_data['demands']:
            self.demands[demand_data['archetype_id']] = demand_data['count']

        if debug:
            print(f'\tAdventure: id {self.id}, {len(self.demands)} demands, name "{self.name}"' +
                  (', golden octopus!' if self.is_golden_octopus else ''))
            for item_id, count in self.demands.items():
                event_item = ItemsData.get_item_by_archetype_id_static(item_id)
                print(f'\t\tDemand: {count} of {event_item}')
                recipe_string = event_item.get_recipe_string(tab_count=3)
                if recipe_string is not None:
                    print(recipe_string)

    def get_csv_text(self, *, debug=False):
        '''
        CSV format:
        adv name, demand name, [comp id, comp star & name, qty owned, qty/demand, cost/item, mission,]
        '''
        s = ''
        for item_id, count in self.demands.items():
            event_item = ItemsData.get_item_by_archetype_id_static(item_id)
            s += f'{self.name}, {event_item.name}, '
            for demand_item_id, demand_item_name, qty_owned, qty_needed in event_item.get_recipe_data_for_csv():
                s += f'{demand_item_id}, {demand_item_name}, {qty_owned}, {qty_needed}, , , '
            s += '\n'
        if debug:
            print(s)
        return s

    def get_wiki_text(self):
        '''
        Wiki text format:

        {{Galaxy/Mission
        | title = Breadcrumbs
        | text = Trace the Pakleds' journey to the asteroid.
        | {{Galaxy/Recipe | skill = {{SkillMultiple|DIP|or|SEC}} | trait1 = Maverick| trait2 = Costumed| recipename = Metallurgy}}
        | {{Galaxy/Recipe | skill = {{Skill|DIP}} | trait1 = Diplomat| trait2 = Maverick | recipename = Passenger Manifest}}
        | {{Galaxy/Recipe | skill = {{Skill|SCI}} | trait1 = Thief | trait2 = Prodigy | recipename = Rations}}
        }}
        '''

        s = f'{{{{Galaxy/Mission\n| title = {self.name}\n| text = {self.description}\n'
        for item_id in self.demands.keys():
            s += ItemsData.get_item_by_archetype_id_static(item_id).get_galaxy_item_wiki_text() + '\n'
        return s + '}}'


class GatherPool:

    def __init__(self, gather_pool_data, *, debug=False):
        self.id = gather_pool_data['id']
        self.goal_index = gather_pool_data['goal_index']
        if debug:
            print(f'GatherPool: index {self.goal_index}, id {self.id}')

        self.adventures = {}
        for adventure_data in gather_pool_data['adventures']:
            adv = Adventure(adventure_data, debug=debug)
            self.adventures[adv.id] = adv


class GalaxyEvent(GameEvent):
    '''
    JSON structure (of interest):
    action
    player
        character
            events
                <list item>             <-- presumably only one element in the list
                    id
                    name
                    featured_crew
                        id
                        name
                        full_name
                        rarity
                        skills
                            science_skill
                                core
                                range_min
                                range_max
                            diplomacy_skill
                            command_skill
                        traits
                    content
                        content_type: "gather" (for galaxy events), "shuttles" (for faction events)
                        crew_bonuses
                            <crew name>: <bonus multiplier: 5 or 10>
                        gather_pools
                            <list item>     <-- only one item in the list for phase 1, but in phase 2 there is one for
                                                each of faction to build in.
                                id
                                adventures
                                    <list item>
                                        id
                                        name
                                        description
                                        demands
                                            <list item>
                                                archetype_id
                                                count
                                            <list item>
                                                archetype_id
                                                count
                                        golden_octopus: true|false  (true represents the SR build item count/recipe)
                                    <list item>
                                    ...
                            <list item>
                            ...
    item_archetype_cache
        archetypes
            <list item>
                id
                type: 2
                name
                rarity: 0
                recipe
                    demands
                        <list item>
                            archetype_id
                            count
                        <list item>
                        ...
                    jackpot
                        skills
                            <list item>
                            --> 1 string of 1 skill, if only one skill for the building bonus
                            --> 1 string of 2 skills, if one skill AND another skill for the building bonus
                            --> 2 strings of 2 skills (1 each), if one skill OR another skill for the building bonus
                        trait_bonuses
                            <trait>: 0.05 (5% bonus)
                            <trait>: 0.05
    '''

    def __init__(self, event_data_json, *, debug=False):
        super().__init__(event_data_json, debug=debug)
        assert self.content_type == 'gather', self.content_type
        self.gather_pools = [GatherPool(gp_data, debug=debug) for gp_data in self._raw_data['content']['gather_pools']]

        print(f'Got {len(self.gather_pools)} gather pools of '
              f'{sum([len(gp.adventures) for gp in self.gather_pools])} total adventures')

    def get_wiki_text(self):
        s = ''
        for gp in self.gather_pools:
            for adv in gp.adventures.values():
                if not adv.is_golden_octopus:
                    s += adv.get_wiki_text() + '\n\n'
        return s

    def write_csv(self):
        s = ''
        for gp in self.gather_pools:
            for adv in gp.adventures.values():
                if not adv.is_golden_octopus:
                    s += adv.get_csv_text() + '\n'

        '''
        CSV format:
        adv name, demand name, [comp star & name, qty owned, qty/demand, cost/item, mission,]
        '''
        headers = 'Adventure, Demand, ' \
                  'id1, Item 1, Owned, Qty per Demand, Cost per Item, Mission, ' \
                  'id2, Item 2, Owned, Qty per Demand, Cost per Item, Mission, ' \
                  'id3, Item 3, Owned, Qty per Demand, Cost per Item, Mission, ' \
                  'id4, Item 4, Owned, Qty per Demand, Cost per Item, Mission\n'

        filepath = Path.home().joinpath(SUBFOLDER_NAME, GALAXY_EVENT_FILENAME.format(self.name))
        with open(filepath, 'w') as f:
            f.write(headers)
            f.write(s)


class CrewMember:

    def __init__(self):
        self.name = None
        self.cmd_base = self.cmd_pmin = self.cmd_pmax = self.cmd_voy = 0
        self.dip_base = self.dip_pmin = self.dip_pmax = self.dip_voy = 0
        self.sec_base = self.sec_pmin = self.sec_pmax = self.sec_voy = 0
        self.eng_base = self.eng_pmin = self.eng_pmax = self.eng_voy = 0
        self.sci_base = self.sci_pmin = self.sci_pmax = self.sci_voy = 0
        self.med_base = self.med_pmin = self.med_pmax = self.med_voy = 0

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        s = ''
        for a in self.__dict__:
            s += ', {}:{}'.format(a, self.__getattribute__(a))
        return '[' + s[2:] + ']'


class CrewData:

    '''
    JSON structure (of interest):
    player
        character
            crew
                id
                name
                short_name
                level
                rarity
                max_rarity
                traits
                traits_hidden
                skills
                    diplomacy_skill
                        core
                        range_min
                        range_max
                    command_skill
    '''

    __ATTR_OF_INTEREST = set(['id','name','short_name','level','rarity','max_rarity','traits','traits_hidden','skills'])
    __VOYAGE_ATTR = set(['id','name','cmd_voy','dip_voy','sec_voy','eng_voy','sci_voy','med_voy','traits'])
    __VOYAGE_DF_COLS = ['crew_id','name','cmd','dip','sec','eng','sci','med','traits']

    def __init__(self, game_data_player, debug=False):
        self.crew = []
        print('Parsing {} crew members...'.format(len(game_data_player['character']['crew'])))
        for crew_member_data in game_data_player['character']['crew']:
            cm = CrewMember()
            for k in crew_member_data:
                if k in self.__ATTR_OF_INTEREST:
                    if k == 'skills':
                        for skill_name in crew_member_data[k]:
                            prefix = (skill_name[:3] if skill_name[:3] != 'com' else 'cmd') + '_'
                            base = crew_member_data[k][skill_name]['core']
                            pmin = crew_member_data[k][skill_name]['range_min']
                            pmax = crew_member_data[k][skill_name]['range_max']
                            voy = base + int((pmax + pmin)/2)
                            cm.__setattr__(prefix + 'base', base)
                            cm.__setattr__(prefix + 'pmin', pmin)
                            cm.__setattr__(prefix + 'pmax', pmax)
                            cm.__setattr__(prefix + 'voy', voy)
                    else:
                        cm.__setattr__(k, crew_member_data[k])
            if KEEP_HIDDEN_TRAITS:
                cm.traits.extend(cm.traits_hidden)
            cm.__delattr__('traits_hidden')
            self.crew.append(cm)

        # Credit for this section: https://stackoverflow.com/questions/10715965/add-one-row-to-pandas-dataframe
        rows_list = []
        for cm in self.crew:
            d = {}
            for attr in cm.__dict__:
                if attr in self.__VOYAGE_ATTR:
                    if attr[-3:] == 'voy':
                        d[attr[:3]] = getattr(cm, attr)
                    elif attr == 'id':
                        d['crew_id'] = getattr(cm, 'id')
                    else:
                        d[attr] = getattr(cm, attr)
            rows_list.append(d)

        self.voyDF = pd.DataFrame(rows_list, columns=self.__VOYAGE_DF_COLS)


class GameData:

    __PLAYER_KEY = 'player'
    __ITEM_CACHE_KEY = 'item_archetype_cache'
    __ARCHETYPES_KEY = 'archetypes'

    def __init__(self, game_data, *, debug=False):
        assert type(game_data) is dict, type(game_data)
        assert self.__PLAYER_KEY in game_data
        assert self.__ITEM_CACHE_KEY in game_data
        assert self.__ARCHETYPES_KEY in game_data[self.__ITEM_CACHE_KEY]

        player_data_json = game_data[self.__PLAYER_KEY]
        items_data_json = game_data[self.__ITEM_CACHE_KEY][self.__ARCHETYPES_KEY]

        self._raw_data = game_data
        self.crew_data = CrewData(player_data_json, debug=debug)
        self.factions_data = FactionsData(player_data_json, debug=debug)
        self.items_data = ItemsData(items_data_json, player_data_json, debug=debug)
        self.event_data = EventData(player_data_json, debug=debug)


def authenticate(force_reauthentication=False):
    if force_reauthentication:
        authtoken = None
    else:
        authtoken = read_auth_token_from_file()

    if authtoken is None:
        username, password = read_creds_from_file()
        if username is None or password is None:
            return None
        authtoken = login(username, password)
        if authtoken is None:
            return None
        write_auth_token_to_file(authtoken)

    return authtoken


def load_game_data(max_days_old=7, *, debug=False):
    data_age = get_game_data_age()
    if data_age >= max_days_old:
        print('Game data is {}; will download'.format(
            'missing' if data_age > 9999 else f'{data_age:1.1f} days old (exceeds {max_days_old} day limit)'))
        game_data_json = None
    else:
        print(f'Game data is {data_age:1.1f} days old (within {max_days_old} day limit); will use stored data')
        game_data_json = read_game_data_from_file()

    if game_data_json is None:
        authtoken = authenticate()

        try:
            game_data_json = get_game_data(authtoken)
        except requests.exceptions.HTTPError as err:
            if err.args[0].startswith('401 Client Error: Unauthorized for url:'):
                # the authtoken expired, try to authenticate again and get a new one
                print('Authentication token expired; re-authenticating')
                authtoken = authenticate(force_reauthentication=True)
                game_data_json = get_game_data(authtoken)
            else:
                raise
        if game_data_json is not None:
            write_game_data_to_file(game_data_json)

    return GameData(game_data_json, debug=debug)


if __name__ == "__main__":
    data = load_game_data(max_days_old=17, debug=False)

    if data.event_data.event is not None and type(data.event_data.event) in [FactionEvent, GalaxyEvent]:
#        print(data.event_data.event.get_wiki_text())
        pass

    if data.event_data.event is not None and type(data.event_data.event) is GalaxyEvent:
        data.event_data.event.write_csv()
    else:
        print(data.event_data.event)
