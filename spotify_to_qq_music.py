import spotipy
import spotipy.util as util
import requests
import json
import re

SPOTIFY_SCOPE = 'user-library-read'
SPOTIFY_API_CLIENT_ID = 'Register at https://developer.spotify.com'
SPOTIFY_API_USERNAME =  'and create an app'
SPOTIFY_API_SECRET = 'then put them here'
SPOTIFY_API_REDIRECT_URL = 'http://localhost'

QQ_MUSIC_ADD_FAVORITE_API = "https://c.y.qq.com/splcloud/fcgi-bin/fcg_music_add2songdir.fcg?g_tk=5381"
QQ_MUSIC_AUTH_COOKIES = {"login_type": "2",
           'qm_keyst': "请打开浏览器",
           'wxopenid': "启动调试工具",
           "wxrefresh_token": "把这些cookie都拷贝过来",
           'wxuin': "TODO: Use Official QQ Login API(tan90)",
           'wxunionid': "好消息是貌似只有gm_keyst会变"
                         }
QQ_MUSIC_SONG_QUERY_API = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp?ct=24&qqmusic_ver=1298&new_json=1&remoteplace=txt.yqq.centert=0&aggr=1&cr=1&catZhida=1&lossless=0&flag_qc=0&p=1&n=20&w={name}&g_tk=5381&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0"
QQ_MUSIC_ADD_FAVORITE_FORM_DATA = {
    "format": "fs",
    "inCharset": "GB2312",
    "outCharset": "utf8",
    "notice": "0",
    "platform": "yqq",
    "needNewCode": "0",
    "g_tk": "5381",
    "typelist": "13",
    "dirid": "201",
    "addtype": "",
    "formsender": "1",
    "source": "153",
    "r2": "0",
    "r3": "1",
    "utf8": "1",
}


def get_spotify_music():
    access_token = spotipy.util.prompt_for_user_token(SPOTIFY_API_USERNAME, SPOTIFY_SCOPE,
                                                      client_id=SPOTIFY_API_CLIENT_ID, client_secret=SPOTIFY_API_SECRET,
                                                      redirect_uri=SPOTIFY_API_REDIRECT_URL)
    # 这里可能蹦出来个输入框，把spotify登陆后callback的页面贴过来就行
    client = spotipy.Spotify(auth=access_token)
    NUM_SONG = 50
    name_list = []
    idx = 0
    while True:
        tracks = client.current_user_saved_tracks(NUM_SONG, idx)

        name_list += [(item['track']['name'], item['track']['artists'][0]['name']) for item in tracks['items']]
        idx += NUM_SONG
        if len(tracks['items']) < NUM_SONG:
            break
    return name_list


def match_singer(singer, music_obj):
    music_obj_singer_list = ' '.join([item['name'] for item in music_obj['singer']])
    singer = re.sub('[ \"\'\(\)]+', ' ', singer).strip()
    music_obj_singer_list = re.sub('[ \"\'\(\)]+', ' ', music_obj_singer_list).strip()
    if len(set(singer.split(' ')).intersection(set(music_obj_singer_list.split(' ')))) > 0:
        return True
    if '周杰伦' in music_obj_singer_list or '梁静茹' in music_obj_singer_list:
        return True
    return False

def import_song_to_qq_music(name_list, success_name_list, failed_name_list):

    for name, singer in name_list[105:]:
        result = requests.get(QQ_MUSIC_SONG_QUERY_API.format(**{'name': name}), cookies=QQ_MUSIC_AUTH_COOKIES)
        query_str = result.text[result.text.find('(') + 1:-1]
        try:
            query_json = json.loads(query_str)
        except Exception:
            print(result.text)
        print(query_json['data']['song']['curnum'])
        if query_json['data']['song'] and query_json['data']['song']['list']:
            import_single_song_to_qq_favorite(query_json, name, singer, success_name_list, failed_name_list)
        else:
            print("于QQ音乐中未发现音乐" + name)
            failed_name_list.append((name, singer))

def import_single_song_to_qq_favorite(query_json, name, singer, success_name_list, failed_name_list):
    music_obj = query_json['data']['song']['list'][0]
    for item in query_json['data']['song']['list']:
        if match_singer(singer, item):
            music_obj = item
            break
    print("于QQ音乐中发现音乐" + music_obj["name"] + " by " + music_obj["singer"][0]['name'])


    try:
        data = QQ_MUSIC_ADD_FAVORITE_API.copy()
        data["midlist"] = music_obj['mid']
        add_result = requests.post(QQ_MUSIC_ADD_FAVORITE_API, data=QQ_MUSIC_ADD_FAVORITE_FORM_DATA, cookies=QQ_MUSIC_AUTH_COOKIES)
        if "歌曲已经加入您的音乐收藏" in add_result.text:
            print(music_obj['name'] + ' by ' + music_obj['singer'][0]['name'] + u'已添加成功')
            success_name_list.append((name, music_obj["singer"][0]['name']))
        else:
            print(music_obj['name'] + ' by ' + singer + u'添加失败')
            failed_name_list.append((name, singer))

    except Exception:
        print(music_obj['name'] + ' by ' + singer + u'添加失败')
        failed_name_list.append((name, singer))



if __name__ == '__main__':
    failed_name_list = []
    success_name_list = []
    name_list = get_spotify_music()
    import_song_to_qq_music(name_list, success_name_list, failed_name_list)
    print("总成功导入歌曲{}首".format(len(success_name_list)))
    print("以下歌曲导入失败")
    for item in failed_name_list:
        print("{} by {}" .format(*item))
