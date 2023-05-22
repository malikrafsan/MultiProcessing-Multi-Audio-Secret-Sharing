import wave

def main():
    print("Program to verify if two audio files are identical")
    file_path1 = input("Path file 1: ")
    file_path2 = input("Path file 2: ")

    with wave.open(file_path1, 'rb') as file1:
        with wave.open(file_path2, 'rb') as file2:
            if file1.getnchannels() != file2.getnchannels():
                Exception("Number of channels are different")
                return
            if file1.getsampwidth() != file2.getsampwidth():
                Exception("Sample width are different")
                return
            if file1.getframerate() != file2.getframerate():
                Exception("Frame rate are different")
                return
            if file1.getnframes() != file2.getnframes():
                Exception("Number of frames are different")
                return
            if file1.getcomptype() != file2.getcomptype():
                Exception("Compression type are different")
                return
            if file1.getcompname() != file2.getcompname():
                Exception("Compression name are different")
                return

            frames1 = file1.readframes(file1.getnframes())
            frames2 = file2.readframes(file2.getnframes())

            if frames1 == frames2:
                print("Files are identical")
            else:
                raise Exception("Files are different")

if __name__ == '__main__':
    main()
