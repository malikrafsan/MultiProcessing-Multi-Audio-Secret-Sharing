import wave
import pickle
import asyncio
from typing import List, Tuple
from BBS import BBS
from multiprocessing import Pool
import time

SEPARATOR = b'\xff\xff\x00\x00\xff\xff'

RANDOMIZER = BBS(30000000091, 40000000003)

def gen_rand_bytes(num_bytes: int):
    return [
        RANDOMIZER.randrange(0, 256)
        for _ in range(num_bytes)
    ]

def multiprocessing_gen_rand_bytes(num_bytes: int, num: int):
    with Pool() as pool:
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

def sync_write_wave(param: Tuple[str, bytearray, wave._wave_params]):   #path: str, frame_bytes: bytearray, params: wave._wave_params):
    path, frame_bytes, params = param

    with wave.open(path, 'wb') as wavefile:
        wavefile.setparams(params)
        wavefile.writeframes(bytes(frame_bytes))
        return True

async def async_write_wave(path: str, frame_bytes: bytearray, params: wave._wave_params):
    return await asyncio.to_thread(sync_write_wave, (path, frame_bytes, params))

def multiprocessing_write_wave(path: List[str], frame_bytes: List[bytearray], params: List[wave._wave_params], num_process: int):
    with Pool(processes=num_process) as pool:
        return pool.map(sync_write_wave, [
            (path[i], frame_bytes[i], params[i]) for i in range(len(path))
        ])

def mp_split(param: Tuple[bytearray | bytes, int]):
    data, num = param

    start_gen = time.perf_counter()
    arr_random_bytes = multiprocessing_gen_rand_bytes(len(data), num-1)
    end_gen = time.perf_counter()
    print("Gen time: {}".format(end_gen - start_gen))

    start_xor = time.perf_counter()
    shares = [arr_random_bytes[0]]
    for i in range(1,num-1):
        new_share = [arr_random_bytes[i-1][j] ^ arr_random_bytes[i][j] for j in range(len(data))]
        shares.append(new_share)
    
    last_share = [
        arr_random_bytes[-1][j] ^ data[j] for j in range(len(data))
    ]
    shares.append(last_share)
    end_xor = time.perf_counter()
    print("Xor time: {}".format(end_xor - start_xor))

    return [bytes(share) for share in shares]

def split(param: Tuple[bytearray | bytes, int]):
    data, num = param

    start_gen = time.perf_counter()
    arr_random_bytes = [
        gen_rand_bytes(len(data)) for _ in range(num-1)
    ]
    end_gen = time.perf_counter()
    print("Gen time: {}".format(end_gen - start_gen))

    start_xor = time.perf_counter()
    shares = [arr_random_bytes[0]]
    for i in range(1,num-1):
        new_share = [arr_random_bytes[i-1][j] ^ arr_random_bytes[i][j] for j in range(len(data))]
        shares.append(new_share)
    
    last_share = [
        arr_random_bytes[-1][j] ^ data[j] for j in range(len(data))
    ]
    shares.append(last_share)
    end_xor = time.perf_counter()
    print("Xor time: {}".format(end_xor - start_xor))

    return [bytes(share) for share in shares]

def multiprocessing_split(data: List[bytearray | bytes], num: int, num_process: int):
    # return [
    #     mp_split((data[i], num)) for i in range(len(data))
    # ]
    with Pool(processes=num_process) as pool:
        return pool.map(split, [(data[i], num) for i in range(len(data))])

async def multi_share():
    num_files = int(input("Number files: "))

    files_path = []
    for i in range(num_files):
        files_path.append(input("Path file {}: ".format(i+1)))

    num_share = int(input("Number share: "))

    start_read_file = time.perf_counter()
    frame_bytes: List[Tuple[bytearray, bytes]] = await asyncio.gather(*[async_read_wave(path) for path in files_path])
    end_read_file = time.perf_counter()
    print("Read file time: {}".format(end_read_file - start_read_file))

    arr_frames = [x[0] for x in frame_bytes]
    arr_params = [x[1] for x in frame_bytes]

    arr_data = arr_frames + arr_params
    num_process = len(arr_data)

    start_split = time.perf_counter()
    splitted = [
        mp_split((arr_data[i], num_share)) for i in range(num_process)
    ] #multiprocessing_split(arr_data, num_share, num_process)
    end_split = time.perf_counter()
    print("Split time: {}".format(end_split - start_split))

    # print("=====================================================================")

    # start_arr_mp_split = time.perf_counter()
    # arr_mp_split = multiprocessing_split(arr_data, num_share, num_process)
    # end_arr_mp_split = time.perf_counter()
    # print("Arr mp split time: {}".format(end_arr_mp_split - start_arr_mp_split))
    # # print(arr_mp_split[0][0][0])

    shares = [
        SEPARATOR.join(
            [splitted[i][j] for i in range(num_process)])
        for j in range(num_share)
    ]

    pivot_param: wave._wave_params = pickle.loads(frame_bytes[0][1])

    start_write_file = time.perf_counter()
    _ = await asyncio.gather(*[
        async_write_wave("share{}.wav".format(i+1), shares[i], pivot_param) 
        for i in range(num_share)])
    end_write_file = time.perf_counter()
    print("Write file time: {}".format(end_write_file - start_write_file))
    
def recover(data: list[bytearray]):
    recovered = [x for x in data[0]]
    for i in range(1, len(data)):
        for j in range(len(data[i])):
            recovered[j] ^= data[i][j]
    return bytes(recovered)

def multiprocessing_recover(arr_data: List[List[bytearray]]):
    with Pool() as pool:
        return pool.map(recover, arr_data)

async def multi_combine():
    num_files = int(input("Number files: "))

    files_path = []
    for i in range(num_files):
        files_path.append(input("Path file {}: ".format(i+1)))

    start_read_file = time.perf_counter()
    frame_bytes: List[Tuple[bytearray, bytes]] = await asyncio.gather(*[async_read_wave(path) for path in files_path])
    end_read_file = time.perf_counter()
    print("Read file time: {}".format(end_read_file - start_read_file))

    arr_frames = [x[0] for x in frame_bytes]
    arr_splitted = [
        frame.split(SEPARATOR)
        for frame in arr_frames
    ]

    num_files = len(arr_splitted[0]) // 2

    arr_data = [
        [arr_splitted[i][j] for i in range(len(arr_splitted))]
        for j in range(num_files * 2)
    ]

    start_recover = time.perf_counter()
    arr_recovered = multiprocessing_recover(arr_data)
    end_recover = time.perf_counter()
    print("Recover time: {}".format(end_recover - start_recover))

    arr_frame = arr_recovered[:num_files]
    arr_params = arr_recovered[num_files:]
    arr_loaded_params = [pickle.loads(params) for params in arr_params]

    start_write_file = time.perf_counter()
    _ = await asyncio.gather(*[
        async_write_wave("combine{}.wav".format(i+1), 
                         arr_frame[i], arr_loaded_params[i]) 
        for i in range(num_files)])
    end_write_file = time.perf_counter()
    print("Write file time: {}".format(end_write_file - start_write_file))

def sync_multi_share():
    num_files = int(input("Number files: "))

    files_path = []
    for i in range(num_files):
        files_path.append(input("Path file {}: ".format(i+1)))

    num_share = int(input("Number share: "))

    start_read_file = time.perf_counter()
    frame_bytes: List[Tuple[bytearray, bytes]] = [sync_read_wave(path) for path in files_path]
    end_read_file = time.perf_counter()
    print("Read file time: {}".format(end_read_file - start_read_file))

    arr_frames = [x[0] for x in frame_bytes]
    arr_params = [x[1] for x in frame_bytes]

    arr_data = arr_frames + arr_params
    num_process = len(arr_data)

    start_split = time.perf_counter()
    splitted = [
        split((arr_data[i], num_share)) for i in range(num_process)
    ]
    end_split = time.perf_counter()
    print("Split time: {}".format(end_split - start_split))

    shares = [
        SEPARATOR.join(
            [splitted[i][j] for i in range(num_process)])
        for j in range(num_share)
    ]

    pivot_param: wave._wave_params = pickle.loads(frame_bytes[0][1])

    start_write_file = time.perf_counter()
    _ = [sync_write_wave(("share{}.wav".format(i+1), shares[i], pivot_param)) for i in range(num_share)]
    end_write_file = time.perf_counter()
    print("Write file time: {}".format(end_write_file - start_write_file))

def sync_multi_combine():
    num_files = int(input("Number files: "))

    files_path = []
    for i in range(num_files):
        files_path.append(input("Path file {}: ".format(i+1)))

    start_read_file = time.perf_counter()
    frame_bytes: List[Tuple[bytearray, bytes]] = [sync_read_wave(path) for path in files_path]
    end_read_file = time.perf_counter()
    print("Read file time: {}".format(end_read_file - start_read_file))

    arr_frames = [x[0] for x in frame_bytes]
    arr_splitted = [
        frame.split(SEPARATOR)
        for frame in arr_frames
    ]

    num_files = len(arr_splitted[0]) // 2

    arr_data = [
        [arr_splitted[i][j] for i in range(len(arr_splitted))]
        for j in range(num_files * 2)
    ]

    start_recover = time.perf_counter()
    arr_recovered = [
        recover(arr_data[i]) for i in range(len(arr_data))
    ]
    end_recover = time.perf_counter()
    print("Recover time: {}".format(end_recover - start_recover))

    arr_frame = arr_recovered[:num_files]
    arr_params = arr_recovered[num_files:]
    arr_loaded_params = [pickle.loads(params) for params in arr_params]

    start_write_file = time.perf_counter()
    _ = [sync_write_wave(("combine{}.wav".format(i+1), arr_frame[i], arr_loaded_params[i])) for i in range(num_files)]
    end_write_file = time.perf_counter()
    print("Write file time: {}".format(end_write_file - start_write_file))

def main():
    print("Program type: ")
    print("1. Multi share")
    print("2. Multi combine")
    print("3. Sync multi share")
    print("4. Sync multi combine")

    program_type = int(input("Program type: "))

    if program_type == 1:
        asyncio.run(multi_share())
    elif program_type == 2:
        asyncio.run(multi_combine())
    elif program_type == 3:
        sync_multi_share()
    elif program_type == 4:
        sync_multi_combine()
    else:
        print("Invalid program type")


if __name__ == '__main__':
    main()
