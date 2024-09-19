import asyncio
import logging
import re
import time
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import music_downloader_class
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext

storage = MemoryStorage()

button1 = InlineKeyboardButton('1', callback_data='button1')
button2 = InlineKeyboardButton('2', callback_data='button2')
button3 = InlineKeyboardButton('3', callback_data='button3')
button4 = InlineKeyboardButton('4', callback_data='button4')
button5 = InlineKeyboardButton('5', callback_data='button5')
button6 = InlineKeyboardButton('6', callback_data='button6')
button7 = InlineKeyboardButton('7', callback_data='button7')
button8 = InlineKeyboardButton('8', callback_data='button8')
button9 = InlineKeyboardButton('9', callback_data='button9')
button10 = InlineKeyboardButton('10', callback_data='button10')


logging.basicConfig(level=logging.INFO)

bot = Bot(token="7540561916:AAGnl6VCFHDNxqWlPpHx358oDkq_Ex945P4")

dp = Dispatcher(bot, storage=storage)


class SongState(StatesGroup):
    song = State()


def captcha_handler(captcha):
    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()
    return captcha.try_again(key)


async def download_music(object: music_downloader_class.Downloader, song: list, index: int):
    song_url, song_name, song_artist = \
        await object.get_song_name_and_url(song=song[index])
    song_segments = await object.get_song_segments(url=song_url)
    cleaned_segments = await object.clean_segment(segments=song_segments)
    downoaded_segments = await object.download_song_by_segment(segments_data=cleaned_segments, m3u8_url=song_url)
    await object.convert_ts_to_mp3(artist=song_artist, song_name=song_name, segments=downoaded_segments)


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await song_state.song.set()
    await message.answer("Просто пришли название песни и я ее обязательно найду.")


@dp.message_handler(state=song_state.song)
async def search_and_send_result(message: types.Message, state: FSMContext):
    audio_list = await vk_downloader.get_song_from_VK(song_name=message.text)

    await state.update_data(song=message.text)
    stroke = ""
    counter = 1
    urlkb = InlineKeyboardMarkup(row_width=5)

    urlkb.row(button1, button2, button3, button4, button5)
    urlkb.row(button6, button7, button8, button9, button10)
    for i in audio_list:
        time_format = time.strftime("%M:%S", time.gmtime(i['duration']))
        stroke += str(counter) + '. ' + i['title'] + ' - ' + i['artist'] + ' ' + time_format + '\n'
        counter += 1
    await message.answer(stroke, reply_markup=urlkb)


@dp.callback_query_handler(lambda call: call.data == "button1" or call.data == "button2" or call.data == "button3" \
                                        or call.data == "button4" or call.data == "button5" or call.data == "button6" \
                                        or call.data == "button7" or call.data == "button8" or call.data == "button9" \
                                        or call.data == "button10", state=song_state.song)
async def send_audio(call: types.CallbackQuery, state: FSMContext):
    result = re.search(pattern='\d+', string=call.data)
    index = result[0]
    data = await state.get_data()
    audio_list = await vk_downloader.get_song_from_VK(song_name=data['song'])
    song_name = audio_list[int(index)-1]['title']
    artist = audio_list[int(index)-1]['artist']
    await download_music(vk_downloader, audio_list, int(index)-1)
    await bot.send_audio(call.message.chat.id, audio=open("path_to_audio_folder/" + song_name + "_" + artist + ".mp3", "rb"))


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    vk_downloader = music_downloader_class.Downloader(login="", password="", captcha_handler=captcha_handler)
    asyncio.run(main())
