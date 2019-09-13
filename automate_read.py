import os
import subprocess

from trace_reader import DataReader

TRACE_INPUT = "mem_trace.txt"
TRACE_OUTPUT = "trace_reader_output.txt"

COMMAND = "bin/TAppEncoderStatic"
ENCODER = "HEVC"
CONFIG = {"Random Access": "cfg/encoder_randomaccess_main.cfg",
          "Low Delay": "cfg/encoder_lowdelay_main.cfg"}
VIDEO_CFG_PATH = "cfg/per-sequence/"

VIDEO_PATH = "../videos_vitech"
ENCODER_PATH = "../hm-videomem"

FRAMES = '17'
SEARCH_RANGE = ['64', '96', '128']


class AutomateRead(object):
    def __init__(self, command):
        self.command = command
        self.video_paths = []
        self.output_file = open("automate_read_output.txt", 'w')
        self.data_reader = DataReader(TRACE_INPUT)

    def list_all_videos(self, path):
        for root, directory, files in os.walk(path):
            for f in files:
                self.video_paths.append(os.path.join(root, f))

    @staticmethod
    def get_video_title(video):
        # video.split("_") = ['../video', 'sequences/Video_name', 'widthxheight', 'fps.yuv']
        parse = video.split("_")

        # parse[1] = 'sequences/Video_name'
        title = parse[1].split('/')
        title = title[1]

        return title

    @staticmethod
    def get_video_cfg(title, path):
        video_cfg = path + title + ".cfg"

        return video_cfg

    def generate_trace(self, video, video_cfg, cfg, sr):
        cmd_array = [self.command, '-c', cfg, '-c', video_cfg, '-i', video, '-f', FRAMES, '-sr', sr]

        subprocess.run(cmd_array)

    def process_trace(self, video_title, encoder, cfg):
        self.data_reader.read_data(video_title, encoder, cfg)
        self.data_reader.save_data()

    def append_output_file(self):
        with open(TRACE_OUTPUT) as trace:
            self.output_file.write(trace.read())

        self.output_file.write("\n")

    def process_videos(self):
        for video_path in self.video_paths:

            video_title = self.get_video_title(video_path)
            video_cfg = self.get_video_cfg(video_title, VIDEO_CFG_PATH)

            for cfg, cfg_path in CONFIG.items():
                for sr in SEARCH_RANGE:
                    self.generate_trace(video_path, video_cfg, cfg_path, sr)
                    self.process_trace(video_title, ENCODER, cfg)
                    self.append_output_file()
                    # Apaga o arquivo trace antes de gerar o próximo
                    os.remove(TRACE_INPUT)
                    os.remove(TRACE_OUTPUT)

        self.output_file.close()


def main():
    os.chdir(ENCODER_PATH)

    automate_reader = AutomateRead(COMMAND)
    automate_reader.list_all_videos(VIDEO_PATH)
    automate_reader.process_videos()


if __name__ == "__main__":
    main()
