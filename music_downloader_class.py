import m3u8
import requests
import os
from vk_api import VkApi
from vk_api.audio import VkAudio
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


class Downloader():
    def __init__(self, login, password, captcha_handler):
        self._vk_session = VkApi(
            login=login,
            password=password,
            captcha_handler=captcha_handler,
        )
        self._vk_session.auth()
        self.vk_audio = VkAudio(self._vk_session)

    async def get_song_from_VK(self, song_name):
        result = self.vk_audio.search(q=song_name, count=10)
        return list(result)

    async def get_song_segments(self, url: str):
        m3u8_data = m3u8.load(uri=url)
        return m3u8_data.segments

    async def clean_segment(self, segments):
        segment_data = {}
        for i in segments:
            if i.key.uri is not None:
                keyForEncrypt = i.key.uri

        for segment in segments:
            segment_uri = segment.absolute_uri

            extended_segment = {
                "segment_method": None,
                "method_uri": None
            }
            if str(segment.key).startswith('#EXT-X-KEY:METHOD=AES-128'):
                extended_segment["segment_method"] = True
                extended_segment["method_uri"] = keyForEncrypt
            segment_data[segment_uri] = extended_segment

        return segment_data

    async def download_song_by_segment(self, segments_data: dict, m3u8_url):
        downloaded_segments = []
        for uri in segments_data:
            if len(uri) == 227: # TODO: use regex
                audio = requests.get(url=m3u8_url.replace("index.m3u8", uri[len(uri) - 11:len(uri)]))
            else:
                audio = requests.get(url=m3u8_url.replace("index.m3u8", uri[len(uri) - 12:len(uri)]))

            downloaded_segments.append(audio.content)

            if segments_data.get(uri).get("segment_method") is not None:
                key_uri = segments_data.get(uri).get("method_uri")

                key = requests.get(url=key_uri)
                iv = downloaded_segments[-1][0:16]
                ciphered_data = downloaded_segments[-1][16:]

                cipher = AES.new(key=key.content, mode=AES.MODE_CBC, iv=iv)

                data = unpad(cipher.decrypt(ciphered_data), AES.block_size)
                downloaded_segments[-1] = data

        return b''.join(downloaded_segments)

    async def convert_ts_to_mp3(self, artist: str, song_name: str, segments: bytes):
        with open(f'path_to_audio_folder/{song_name}_{artist}.ts', 'w+b') as f:
            f.write(segments)
        os.system(
            f'ffmpeg -i "path_to_audio_folder/{song_name}_{artist}.ts" "path_to_audio_folder/{song_name}_{artist}.mp3"')

        os.remove(f'path_to_audio_folder/{song_name}_{artist}.ts')

    async def get_song_name_and_url(self, song):
        song_url, song_name, song_artist = song['url'], song['title'], song['artist']
        return song_url, song_name, song_artist


