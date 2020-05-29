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


class StaticMissionData:
    # this data isn't in the JSON
    MISSIONS_PER_EPISODE = {'E1': 14, 'E2': 19, 'E3': 5, 'E4': 14, 'E5': 18, 'E6': 4, 'E7': 13, 'E8': 14, 'E9': 4,
                            'E10': 7, 'DE': 8, 'CT': 8, 'KE': 5, 'IN': 8, '??': 100000}

    # some item sources are missing the dispute value for unclear reasons, so this is a workaround
    EPISODE_FOR_MISSION_ID = {
        117: 'E4', 120: 'DE', 121: 'CT', 123: 'CT', 125: 'DE', 126: 'DE', 128: 'DE', 129: 'CT',
        130: 'CT', 132: 'DE', 133: 'DE', 134: 'DE', 135: 'DE', 137: 'CT', 139: 'CT', 140: 'CT',
        210: 'E10', 214: 'E10', 216: 'E10', 220: 'E6', 221: 'E6', 224: 'E6', 225: 'E6', 227: 'E3', 233: 'E3',
        234: 'E3', 235: 'E3', 237: 'E3',
        548: 'KE', 549: 'KE', 550: 'KE', 551: 'KE', 552: 'KE',
        720: 'IN', 721: 'IN', 738: 'IN', 739: 'IN', 743: 'IN', 744: 'IN', 762: 'IN', 763: 'IN',
        837: 'E10', 838: 'E10', 842: 'E10', 843: 'E10'
    }


class ItemSource:

    # types
    AWAY_TEAM = 0
    FACTION_ONLY = 1
    SPACE_BATTLE = 2
    RARE_REWARD = 3

    def __init__(self):
        self.type = -1
        self.id = -1
        self.name = None
        self.energy_quotient = -1
        self.chance_grade = -1
        # JSON mission is the mission number anti-mod number of missions in the episode.
        # for example, episode 7 has 13 missions, so mission 33 is M7-E7
        # weirdly, sometimes the JSON mission is multiples of the number of missions, but the mod still works
        # for example, E6-M3 is JSON mission 19 even though there are only 4 missions in E6 (but 19%4=3 so it's ok)
        self.mission = -1
        # episode = dispute + 1
        # for unknown reasons, sometimes the dispute is missing, so use the MISSIONS_PER_EPISODE as a workaround
        self.episode = None
        # I thought mastery: 0 is normal, 1 is elite, 2 is epic but now I'm not sure
        self.mastery = -1

    def is_rare_reward(self):
        return self.type == self.RARE_REWARD

    def is_faction_only(self):
        return self.type == self.FACTION_ONLY

    def __str__(self):
        return f'{self.episode}-{self.mission} {self.name}' + ' (Rare reward)' if self.is_rare_reward() else ''


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

#    def __repr__(self):
#        s = ''
#        for a in self.__dict__:
#            s += ', {}:{}'.format(a, self.__getattribute__(a))
#        return '[' + s[2:] + ']'


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

    def __init__(self, game_data_items):
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
                    if not item_source.is_faction_only():
                        item_source.mastery = src[self.__MASTERY_KEY]

                        # for unknown reasons, sometimes the dispute is missing, so use the MISSIONS_PER_EPISODE as a
                        # workaround
                        if self.__DISPUTE_KEY in src:
                            item_source.episode = f'E{src[self.__DISPUTE_KEY] + 1}'
                        elif item_source.id in StaticMissionData.EPISODE_FOR_MISSION_ID:
                            item_source.episode = StaticMissionData.EPISODE_FOR_MISSION_ID[item_source.id]
                        else:
                            missing_missions.add(f'{item_source.id} {item_source.name}')
                            item_source.episode = '??'

                        item_source.mission = src[self.__MISSION_KEY] % \
                                              StaticMissionData.MISSIONS_PER_EPISODE[item_source.episode]

            if self.__BONUSES_KEY in item_data:
                self.bonuses = item_data[self.__BONUSES_KEY]

            self.items[item.id] = item

        for mission_id in sorted(missing_missions):
            print(f'Need episode for mission id {mission_id} added to EPISODE_FOR_MISSION_ID dict')

#        print(f'Loaded {len(self.items)} items')


class GalaxyEventData:
    '''
    JSON structure (of interest):
    action
    player
        character
            events
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
                    <list item>
                        id
                        adventures
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
                    <list item>
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
                        challenge_id
                        challenge_skill
                        challenge_difficulty
                        type: 0 (away team) or 2 (space battle)
                        id
                        name
                        energy_quotient
                        chance_grade (1-5? number of pips displayed?)
                        place
                        mission
                        mastery
                    <list item>
                    ...
                    <list item> (faction)
                        type: 1
                        id
                        name: <faction name> Transmission
                        energy_quotient
                        chance_grade
                bonuses (optional?)
                    <number> (not sure what these are)
                    <number>
                    ...
    '''


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
#        self.voyDF.set_index('crew_id', inplace=True, verify_integrity=True)


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
        self.items_data = ItemsData(game_data[self.__ITEM_CACHE_KEY][self.__ARCHETYPES_KEY])


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
        authtoken = read_auth_token_from_file()
        if authtoken is None:
            username, password = read_creds_from_file()
            if username is None or password is None:
                return None
            authtoken = login(username, password)
            if authtoken is None:
                return None
            write_auth_token_to_file(authtoken)

        game_data_json = get_game_data(authtoken)
        if game_data_json is not None:
            write_game_data_to_file(game_data_json)

    return GameData(game_data_json)


if __name__ == "__main__":
    data = load_game_data(max_days_old=7)

