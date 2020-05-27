import requests
from pathlib import Path, PurePath


USERPASS_FILENAME = "STT website login.txt"
#PLAYER_URL = 'https://stt.disruptorbeam.com/player'
#LOGIN_URL = 'https://games.disruptorbeam.com/auth/authenticate/userpass'

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


def login2(username, password):
    s = requests.Session()
    headers = {'Content-type':'application/x-www-form-urlencoded; charset=UTF-8'}
    form = {'username': username, 'password': password, 'client_id': CLIENT_ID, 'grant_type': 'password'}
    print(form)
    resp = s.post(URL_PLATFORM + 'oauth2/token', headers=headers, data=form)
    print(resp.url)
    resp.raise_for_status()
    print(resp.content)
    return s, resp


def get_player_data(s):
    resp = s.get(PLAYER_URL)
#    print(resp.status_code)
    resp.raise_for_status()
    print(len(resp.content))
    print(resp.content)
    print(resp.url)
    for k, v in s.cookies.iteritems():
        print(f'\t{k}\t{v}')
    return resp


def login(username = None, password = None):
    if username is None or password is None:
        home = Path.home()
        filepath = Path.home().joinpath(USERPASS_FILENAME)
        if filepath.exists():
            with open(filepath) as f:
                username = f.readline().strip()
                password = f.readline().strip()
        else:
            print('Please create a text file named "{}" in folder {}\n'.format(USERPASS_FILENAME, home) +
                    'with your username on the first line and your password on the second line, like this:\n' +
                    '{}\nContents:\nusername\npassword'.format(filepath))
            return None, None

    print(f'Attempting login for: {username}...')

    '''
    From: https://games.disruptorbeam.com/login
     <div class="login-box">
        <form action = "https://games.disruptorbeam.com/auth/authenticate/userpass" class="form-signin" autocomplete="on" method="POST">
            <label for="username">Email:</label><input type="text" id="username" name="username"/>
            <label for="password">Password:</label><input type="password" id="password" name="password"/>
            <button type="submit" class="btn-sm" id="login-submit"><span class="btn-bg">Sign In</span></button>
    '''

    s = requests.Session()

    # Step 1: go to the player page to get the _startrek_session cookie
    resp = s.get(PLAYER_URL)
    assert '_startrek_session' in s.cookies
    print(resp.url)
    for k, v in s.cookies.iteritems():
        print(f'\t{k}\t{v}')

    # Step 2: go to the login page to log in
    params = {'username': username, 'password': password}
    headers = {'referer': PLAYER_URL}
    resp = s.get(LOGIN_URL, headers=headers, params=params)
#    print(r.status_code)
    resp.raise_for_status()
    assert 'dbid_ss' in s.cookies
    print(resp.url)
    for k, v in s.cookies.iteritems():
        print(f'\t{k}\t{v}')

    print('Login successful!')
    return s


#if __name__ == "__main__":
#    s = login()
#    resp = get_player_data(s)
#    get_player_data()
