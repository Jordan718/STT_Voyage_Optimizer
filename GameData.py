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

    def __init__(self, game_data_player):
        FactionsData.__STATIC_REFERENCE_TO_DATA = self
        self.factions = {}
        self.__shuttle_token_id_to_faction_id = {}
        self.__raw_data = game_data_player['character']['factions']
        print(f'Parsing {len(self.__raw_data)} factions...')
        for faction_data in self.__raw_data:
            fac = Faction()
            for k in faction_data:
                if k in self.__ATTR_OF_INTEREST:
                    fac.__setattr__(k, faction_data[k])
            self.factions[fac.id] = fac
            self.__shuttle_token_id_to_faction_id[fac.shuttle_token_id] = fac.id

    def get_transmission_name_for_shuttle_token_id(self, shuttle_token_id):
        return self.factions[self.__shuttle_token_id_to_faction_id[shuttle_token_id]].name + ' Transmission'

    @classmethod
    def get_transmission_name_for_shuttle_token_id_static(cls, shuttle_token_id):
        assert cls.__STATIC_REFERENCE_TO_DATA is not None
        return cls.__STATIC_REFERENCE_TO_DATA.get_transmission_name_for_shuttle_token_id(shuttle_token_id)


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
        # recipe = dict of demands; archetype_id: count
        self.recipe = None
        # sources = list of missions; id, name, energy_quotient, chance_grade
        self.sources = None
        self.bonuses = None

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

    def get_recipe_string(self, *, tab_count=0):
        if self.recipe is None:
            return None

        tabs = '\t' * tab_count
        demand_strings = []
        for item_id, count in self.recipe.items():
            item = ItemsData.get_item_by_archetype_id_static(item_id)
            demand_strings.append(f'{tabs}{count} of {item}')

        return f'{tabs}Recipe of {len(demand_strings)} demands:\n\t' + f'\n\t'.join(demand_strings)


class ItemsData:
    '''
    JSON structure (of interest):
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

    __STATIC_REFERENCE_TO_DATA = None

    def __init__(self, game_data_items):
        ItemsData.__STATIC_REFERENCE_TO_DATA = self
        self.__raw_data = game_data_items
        self.items = {}
        print('Parsing {} items...'.format(len(game_data_items)))
        missing_missions = set()
        for item_data in self.__raw_data:
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

        for mission_id in sorted(missing_missions):
            print(f'Need episode for mission id {mission_id} added to EPISODE_FOR_MISSION_ID dict')

    @classmethod
    def get_item_by_archetype_id_static(cls, archetype_id):
        assert cls.__STATIC_REFERENCE_TO_DATA is not None
        return cls.__STATIC_REFERENCE_TO_DATA.items[archetype_id]


class GalaxyEvent:

    def __init__(self):
        self.id = -1
        self.name = None
        self.featured_crew = []
        # Content type should always be "gather" for galaxy events
        self.content_type = None
        self.crew_bonuses = None
        self.gather_pools = []


class GatherPool:

    def __init__(self):
        self.id = -1
        self.goal_index = -1
        self.adventures = {}


class Adventure:

    def __init__(self):
        self.id = -1
        self.name = None
        self.description = None
        self.demands = {}
        self.golden_octopus = False


class GalaxyEventData:
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
                        content_type: "gather" (for galaxy events)
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
                                        golden_octopus: true|false  (ignore true; represents the SR build item count/recipe)
                                    <list item>
                                    ...
                            <list item>
                            ...
    '''

    def __init__(self, game_data_player, debug=False):
        self.__raw_data = game_data_player['character']['events']
        if len(self.__raw_data) == 0:
            print('No event data found')
            return

        if len(self.__raw_data) > 1:
            print(f'WARNING: Expected only 0 or 1 events, found {len(self.__raw_data)}; ignoring all but the first')

        self.__raw_data = self.__raw_data[0]
        print(f'Parsing event "{self.__raw_data["name"]}"...')
        self.galaxy_event = GalaxyEvent()
        self.galaxy_event.id = self.__raw_data['id']
        self.galaxy_event.name = self.__raw_data['name']
        for f_crew in self.__raw_data['featured_crew']:
            self.galaxy_event.featured_crew.append(f_crew['id'])
            if debug:
                print(f'Featured crew: {f_crew["id"]} {f_crew["full_name"]}')
        self.galaxy_event.crew_bonuses = self.__raw_data['content']['crew_bonuses']
        if debug:
            for crew_name,bonus in self.galaxy_event.crew_bonuses.items():
                print(f'Crew bonuses: {crew_name}: {bonus}')

        for gather_pool_data in self.__raw_data['content']['gather_pools']:
            gp = GatherPool()
            gp.id = gather_pool_data['id']
            gp.goal_index = gather_pool_data['goal_index']
            if debug:
                print(f'GatherPool: index {gp.goal_index}, id {gp.id}')
            for adventure_data in gather_pool_data['adventures']:
                adv = Adventure()
                for k in adventure_data:
                    if k == 'demands':
                        # demands is a list of dicts with keys archetype_id and count
                        for demand_data in adventure_data[k]:
                            adv.demands[demand_data['archetype_id']] = demand_data['count']
                    else:
                        adv.__setattr__(k, adventure_data[k])
                gp.adventures[adv.id] = adv
                if debug:
                    print(f'\tAdventure: id {adv.id}, {len(adv.demands)} demands, name "{adv.name}"' +
                          (', golden octopus!' if adv.golden_octopus else ''))
                    for item_id, count in adv.demands.items():
                        event_item = ItemsData.get_item_by_archetype_id_static(item_id)
                        print(f'\t\tDemand: {count} of {event_item}')
                        recipe_string = event_item.get_recipe_string(tab_count=3)
                        if recipe_string is not None:
                            print(event_item.get_recipe_string(tab_count=3))
            self.galaxy_event.gather_pools.append(gp)


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

    def __init__(self, game_data_player):
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

    def __init__(self, game_data):
        assert type(game_data) is dict, type(game_data)
        assert self.__PLAYER_KEY in game_data
        assert self.__ITEM_CACHE_KEY in game_data
        assert self.__ARCHETYPES_KEY in game_data[self.__ITEM_CACHE_KEY]

        self.__raw_data = game_data
        self.crew_data = CrewData(game_data[self.__PLAYER_KEY])
        self.factions_data = FactionsData(game_data[self.__PLAYER_KEY])
        self.items_data = ItemsData(game_data[self.__ITEM_CACHE_KEY][self.__ARCHETYPES_KEY])
        self.events_data = GalaxyEventData(game_data[self.__PLAYER_KEY], True)


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


def load_game_data(max_days_old=7):
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

    return GameData(game_data_json)


if __name__ == "__main__":
    data = load_game_data(max_days_old=0)
