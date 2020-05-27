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


def get_player_data(authtoken):
    print('Getting player data...')
    form = {'client_api': CLIENT_API_VERSION, ACCESS_TOKEN: authtoken}
    resp = requests.get(PLAYER_URL, data=form)
    resp.raise_for_status()
    return json.loads(resp.content)


def write_player_data_to_file(player):
    print('Writing player data to file...')
    filepath = Path.home().joinpath(SUBFOLDER_NAME, PLAYER_JSON_FILENAME)
    with open(filepath, 'w') as f:
        json.dump(player, f, indent=3)


def read_player_data_from_file():
    print('Reading player data from file...')
    player = None
    filepath = Path.home().joinpath(SUBFOLDER_NAME, PLAYER_JSON_FILENAME)
    if filepath.exists():
        with open(filepath) as f:
            player = json.load(f)

    if player is not None and len(player) < 1:
        player = None

    return player


def get_player_data_age():
    filepath = Path.home().joinpath(SUBFOLDER_NAME, PLAYER_JSON_FILENAME)
    if filepath.exists():
        last_modified = os.path.getmtime(filepath)
        return (time.time()-os.path.getmtime(filepath))/SECONDS_PER_DAY
    else:
        return 99999999


class CrewMember():

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


class PlayerData():

    '''
    JSON structure (of interest):
    action
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
    item_archetype_cache
    '''

    __ITEM_KEY = 'item_archetype_cache'
    __ACTION_KEY = 'action'
    __PLAYER_KEY = 'player'
    __ATTR_OF_INTEREST = set(['id','name','short_name','level','rarity','max_rarity','traits','traits_hidden','skills'])
    __VOYAGE_ATTR = set(['id','name','cmd_voy','dip_voy','sec_voy','eng_voy','sci_voy','med_voy','traits'])
    __VOYAGE_DF_COLS = ['crew_id','name','cmd','dip','sec','eng','sci','med','traits']

    def __init__(self, player_data):
        assert type(player_data) is dict, type(player_data)
        assert self.__ITEM_KEY in player_data and self.__ACTION_KEY in player_data and self.__PLAYER_KEY in player_data

        self.__raw_data = player_data
        self.crew = []
        print('Parsing {} crew members...'.format(len(player_data[self.__PLAYER_KEY]['character']['crew'])))
        for crew_member_data in player_data[self.__PLAYER_KEY]['character']['crew']:
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


def load_player_data(max_days_old=7):
    data_age = get_player_data_age()
    if data_age >= max_days_old:
        print('Player data is {}; will download'.format(
            'missing' if data_age > 9999 else f'{data_age:1.1f} days old (exceeds {max_days_old} day limit)'))
        player = None
    else:
        print(f'Player data is {data_age:1.1f} days old (within {max_days_old} day limit); will use stored data')
        player = read_player_data_from_file()

    if player is None:
        authtoken = read_auth_token_from_file()
        if authtoken is None:
            username, password = read_creds_from_file()
            if username is None or password is None:
                return None
            authtoken = login(username, password)
            if authtoken is None:
                return None
            write_auth_token_to_file(authtoken)

        player = get_player_data(authtoken)
        if player is not None:
            write_player_data_to_file(player)

    return PlayerData(player)


if __name__ == "__main__":
    data = load_player_data(max_days_old=7)

