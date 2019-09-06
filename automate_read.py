import os
import subprocess

from trace_reader import DataReader

TRACE_FILE = "mem_trace.txt"

COMMAND = "bin/TAppEncoderStatic"
CONFIG = ["cfg/encoder_lowdelay_main.cfg", "cfg/encoder_randomaccess_main.cfg"]
VIDEO_CFG_PATH = "cfg/per-sequence/"

VIDEO_PATH = "../videos_vitech"
ENCODER_PATH = "../hm-videomem"

FRAMES = 9
SEARCH_RANGE = [64, 96, 128]


class AutomateRead(object):
    def __init__(self, command):
        self.command = command
        self.video_paths = []
        self.output_file = open("saida.txt", 'w')
        self.data_reader = DataReader(TRACE_FILE)

    def list_all_videos(self, path):
        for root, directory, file in os.walk(path):
            for f in file:
                self.video_paths.append(os.path.join(root, f))
                # print(os.path.join(root, f))

    @staticmethod
    def get_video_cfg(video, path):
        # video.split("_") = ['../videos', 'vitech/Video_name', 'widthxheight', 'fps.yuv']
        parse = video.split("_")

        # parse[1] = 'vitech/Video_name'
        name = parse[1].split('/')
        name = name[1]

        video_cfg = path + name + ".cfg"

        print(video_cfg)
        return video_cfg

    def generate_trace(self, video, video_cfg, cfg, sr):
        cmd_array = [self.command, '-c', cfg, '-c', video_cfg, '-i', video, '-f', FRAMES, '-sr', sr]
        # print(cmd_array)
        # subprocess.run(cmd_array)

    def process_trace(self):
        self.data_reader.read_data()
        self.data_reader.save_data()

    def append_output_file(self):
        with open(TRACE_FILE) as trace:
            self.output_file.write(trace.read())
        self.output_file.write("\n")

    def process_videos(self):
        for video in self.video_paths:
            video_cfg = self.get_video_cfg(video, VIDEO_CFG_PATH)
            for cfg in CONFIG:
                for sr in SEARCH_RANGE:
                    self.generate_trace(video, video_cfg, cfg, sr)
                    # self.process_trace()
                    # self.append_output_file()
                    # Apaga o arquivo trace antes de gerar o próximo
                    # os.remove(TRACE_FILE)


def main():
    os.chdir(ENCODER_PATH)

    automate_reader = AutomateRead(COMMAND)
    automate_reader.list_all_videos(VIDEO_PATH)
    automate_reader.process_videos()


if __name__ == "__main__":
    main()
