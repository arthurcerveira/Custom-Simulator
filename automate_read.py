import os
import subprocess

from trace_reader import DataReader

TRACE_FILE = "mem_trace.txt"

COMMAND = "bin/TAppEncoderStatic"
CONFIG = "cfg/encoder_lowdelay_main.cfg"

VIDEO_PATH = "../videos_vitech"
ENCODER_PATH = "../hm-videomem"


class AutomateRead(object):
    def __init__(self, command, config):
        self.command = command
        self.config = config
        self.video_paths = []
        self.output_file = open("saida.txt", 'w')
        self.data_reader = DataReader(TRACE_FILE)

    def list_all_videos(self, path):
        for root, directory, file in os.walk(path):
            for f in file:
                self.video_paths.append(os.path.join(root, f))
                # print(os.path.join(root, f))

    @staticmethod
    def parse_video_info(video):
        # video.split("_") = ['../videos', 'vitech/Video_name', 'widthxheight', 'fps.yuv']
        parse = video.split("_")

        # parse[1] = 'vitech/Video_name'
        name = parse[1].split('/')
        name = name[1]

        # parse[2] = 'widthxheight'
        resolution = parse[2].split('x')

        # parse[3] = 'fps.yuv'
        fps = parse[3].split('.')
        fps = fps[0]

        return [name, resolution[0], resolution[1], fps]

    def generate_trace(self, video, width, height, fps):
        cmd_array = [self.command, '-c', self.config, '-i', video, '-wdt', width, '-hgt', height, '-fr', fps, '-f', fps]
        subprocess.run(cmd_array)

    def process_trace(self):
        self.data_reader.read_data()
        self.data_reader.save_data()

    def append_output_file(self):
        with open(TRACE_FILE) as trace:
            self.output_file.write(trace.read())
        self.output_file.write("\n")

    def process_videos(self, path):
        os.chdir(path)

        for video in self.video_paths:
            info = self.parse_video_info(video)
            # info = ['VideoName', 'Width', 'Height', 'FPS']
            self.generate_trace(video, info[1], info[2], info[3])
            self.process_trace()
            self.append_output_file()
            # Apaga o arquivo trace antes de gerar o próximo
            os.remove(TRACE_FILE)


# automate_reader = AutomateRead(COMMAND, CONFIG)
# automate_reader.list_all_videos(VIDEO_PATH)
# automate_reader.process_videos(ENCODER_PATH)

