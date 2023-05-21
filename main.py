import wave
import pickle
import asyncio
from typing import List, Tuple
from BBS import BBS
from multiprocessing import Pool

SEPARATOR = b'\xff\xff\x00\x00\xff\xff'

RANDOMIZER = BBS(30000000091, 40000000003)

def gen_rand_bytes(num_bytes: int):
    return [
        RANDOMIZER.randrange(0, 256)
        for _ in range(num_bytes)
    ]

def multiprocessing_gen_rand_bytes(num_bytes: int, num: int):
    with Pool(processes=num) as pool:
        return pool.map(gen_rand_bytes, [num_bytes for _ in range(num)])

def sync_read_wave(path: str):
    with wave.open(path, 'rb') as wavefile:
        return (
            bytearray(list(
                wavefile.readframes(wavefile.getnframes()))),
            pickle.dumps(wavefile.getparams())
        )

async def async_read_wave(path: str):
    return await asyncio.to_thread(sync_read_wave, path)

def multiprocessing_read_wave(path: List[str], num_process: int):
    with Pool(processes=num_process) as pool:
        return pool.map(sync_read_wave, path)

def sync_write_wave(path: str, frame_bytes: bytearray, params: wave._wave_params):
    with wave.open(path, 'wb') as wavefile:
        wavefile.setparams(params)
        wavefile.writeframes(bytes(frame_bytes))
        return True

async def async_write_wave(path: str, frame_bytes: bytearray, params: wave._wave_params):
    return await asyncio.to_thread(sync_write_wave, path, frame_bytes, params)

def multiprocessing_write_wave(path: List[str], frame_bytes: List[bytearray], params: List[wave._wave_params], num_process: int):
    with Pool(processes=num_process) as pool:
        return pool.map(sync_write_wave, path, frame_bytes, params)

def split(data: bytearray | bytes, num: int):
    arr_random_bytes = multiprocessing_gen_rand_bytes(len(data), num-1)

    shares = [arr_random_bytes[0]]
    for i in range(1,num-1):
        new_share = [arr_random_bytes[i-1][j] ^ arr_random_bytes[i][j] for j in range(len(data))]
        shares.append(new_share)
    
    last_share = [
        arr_random_bytes[-1][j] ^ data[j] for j in range(len(data))
    ]
    shares.append(last_share)

    return [bytes(share) for share in shares]

def multiprocessing_split(data: List[bytearray | bytes], num: int, num_process: int):
    # with Pool(processes=num_process) as pool:
    #     return pool.map(split, data, [num for _ in range(len(data))])
    return [split(data[i], num) for i in range(len(data))]


async def multi_share():
    num_files = int(input("Number files: "))

    files_path = []
    for i in range(num_files):
        files_path.append(input("Path file {}: ".format(i+1)))

    # frame_bytes: List[Tuple[bytearray, bytes]] = await asyncio.gather(*[async_read_wave(path) for path in files_path])
    frame_bytes = multiprocessing_read_wave(files_path, num_files)

    num_share = int(input("Number share: "))

    arr_frames = [x[0] for x in frame_bytes]
    arr_params = [x[1] for x in frame_bytes]

    # combine
    arr_data = arr_frames + arr_params
    num_process = len(arr_data)
    splitted = multiprocessing_split(arr_data, num_share, num_process)

    shares = [
        SEPARATOR.join(
            [splitted[i][j] for i in range(num_process)])
        for j in range(num_share)
    ]

    pivot_param: wave._wave_params = pickle.loads(frame_bytes[0][1])

    # _ = await asyncio.gather(*[
    #     async_write_wave("share{}.wav".format(i+1), shares[i], pivot_param) 
    #     for i in range(num_share)])
    _ = multiprocessing_write_wave(
        ["share{}.wav".format(i+1) for i in range(num_share)], 
        shares, 
        [pivot_param for _ in range(num_share)], 
        num_share)

    
def main():
    print("Program type: ")
    print("1. Multi share")

    program_type = int(input("Program type: "))

    if program_type == 1:
        asyncio.run(multi_share())


if __name__ == '__main__':
    main()
