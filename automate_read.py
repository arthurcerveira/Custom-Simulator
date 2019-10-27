import os
import subprocess

from data_reader import TraceReader, VtuneReader
from data_formatter import generate_graph

# Routines
AUTOMATE_TRACE = False
GENERATE_GRAPH = False

AUTOMATE_VTUNE = True

# Trace Reader
TRACE_INPUT = "mem_trace.txt"
TRACE_OUTPUT = "trace_reader_output.txt"

AUTOMATE_TRACE_OUTPUT = "automate_trace_output.txt"

HEADER_TRACE = "Video encoder;Encoder Configuration;Video sequence;Resolution;" \
               "Search range;Candidate blocks;Accessed data;Accessed data (GB);"

# Vtune Reader
VTUNE_REPORT_INPUT = "report_vtune.csv"

AUTOMATE_VTUNE_OUTPUT = "automate_vtune_output.txt"

HEADER_VTUNE = "Video encoder;Encoder Configuration;Video sequence;Resolution;Search range;"

# Encoder Paths
HM = "../hm-videomem/"
VTM = "../vtm-mem/"

ENCODER_CMD = {"HEVC": HM + "bin/TAppEncoderStatic",
               "VVC": VTM + "bin/EncoderAppStatic"}
CONFIG = {"HEVC": {"Low Delay": HM + "cfg/encoder_lowdelay_main.cfg",
                   "Random Access": HM + "cfg/encoder_randomaccess_main.cfg"},
          "VVC": {"Low Delay": VTM + "cfg/encoder_lowdelay_vtm.cfg",
                  "Random Access": VTM + "cfg/encoder_randomaccess_vtm.cfg"}}
VIDEO_CFG_PATH = {"HEVC": HM + "cfg/per-sequence/",
                  "VVC": VTM + "cfg/per-sequence/"}

VIDEO_SEQUENCES_PATH = "../video_sequences"

# Parameters
FRAMES = '9'
SEARCH_RANGE = ['64', '96', '128', '256']


# Auxiliary Functions
def list_all_videos(path):
    paths = []

    for root, directory, files in os.walk(path):
        for f in files:
            video_path = os.path.join(root, f)
            paths.append(video_path)

    return paths


def generate_cmd_array(command, video, video_cfg, cfg, sr):
    cmd_array = [command, '-c', cfg, '-c', video_cfg, '-i', video, '-f', FRAMES, '-sr', sr]

    return cmd_array


def get_video_info(video_path, cfg_path):
    # video.split("_") = ['../video', 'sequences/Video_name', 'widthxheight', 'fps.yuv']
    parse = video_path.split("_")

    # parse[1] = 'sequences/Video_name'
    title = parse[1].split('/')
    title = title[1]

    # parse[2] = 'widthxheight'
    resolution = parse[2].split('x')
    width = resolution[0]
    height = resolution[1]

    # parse[3] = 'fps.yuv'
    fps = parse[3].split('.')
    fps = fps[0]

    video_cfg = cfg_path + title + ".cfg"

    return {"title": title,
            "width": width,
            "height": height,
            "fps": fps,
            "video_cfg": video_cfg}


def append_output_file(routine_output, automate_output):
    with open(routine_output) as trace:
        with open(automate_output, 'a') as automate_read:
            for line in automate_read:
                automate_read.write(line)
            automate_read.write("\n")


class AutomateTraceReader(object):
    def __init__(self):
        self.video_paths = []
        self.data_reader = TraceReader(TRACE_INPUT)

        # Cria o arquivo de saida
        with open(AUTOMATE_TRACE_OUTPUT, 'w+') as output_file:
            output_file.write(HEADER_TRACE)
            output_file.write(self.data_reader.block_sizes())

    def process_trace(self, video_title, cfg):
        self.data_reader.read_data(video_title, cfg)
        self.data_reader.save_data()

    def process_video(self, video_path):
        for encoder, cmd in ENCODER_CMD.items():
            video_info = get_video_info(video_path, VIDEO_CFG_PATH[encoder])

            for cfg, cfg_path in CONFIG[encoder].items():
                for sr in SEARCH_RANGE:
                    cmd_array = generate_cmd_array(cmd, video_path, video_info["video_cfg"], cfg_path, sr)
                    subprocess.run(cmd_array)

                    self.process_trace(video_info["title"], cfg)
                    append_output_file(TRACE_OUTPUT, AUTOMATE_TRACE_OUTPUT)

                    # Apaga o arquivo trace antes de gerar o próximo
                    os.remove(TRACE_INPUT)
                    os.remove(TRACE_OUTPUT)


class AutomateVtuneReader:
    def __init__(self):
        self.video_paths = []
        self.data_reader = VtuneReader(VTUNE_REPORT_INPUT)

        # Cria o arquivo de saida
        with open(AUTOMATE_VTUNE_OUTPUT, 'w+') as output_file:
            output_file.write(HEADER_VTUNE)
            output_file.write(self.data_reader.modules_header())

    def process_video(self, video_path):
        for encoder, cmd in ENCODER_CMD.items():
            video_info = get_video_info(video_path, VIDEO_CFG_PATH[encoder])

            for cfg, cfg_path in CONFIG[encoder].items():
                for sr in SEARCH_RANGE:
                    cmd_array = generate_cmd_array(cmd, video_path, video_info["video_cfg"], cfg_path, sr)
                    # TODO
                    # Executar o comando
                    # Processar a saida
                    # Concatenar ao arquivo final de saida
                    # Apagar os arquivos desnecesarios


def main():
    if AUTOMATE_TRACE is True:
        automate_reader = AutomateTraceReader()
        automate_reader.video_paths = list_all_videos(VIDEO_SEQUENCES_PATH)

        for video_path in automate_reader.video_paths:
            automate_reader.process_video(video_path)

        if GENERATE_GRAPH is True:
            generate_graph(AUTOMATE_TRACE_OUTPUT)

    if AUTOMATE_VTUNE is True:
        automate_reader = AutomateVtuneReader()
        automate_reader.video_paths = list_all_videos(VIDEO_SEQUENCES_PATH)

        for video_path in automate_reader.video_paths:
            automate_reader.process_video(video_path)


if __name__ == "__main__":
    main()
