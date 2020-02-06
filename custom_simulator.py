import os
import pprint
import subprocess
import shutil

from data_reader import TraceReader, VtuneReader
from data_formatter import generate_trace_graph, generate_vtune_graph, generate_block_graph

# Routines
AUTOMATE_TRACE = False
GENERATE_TRACE_GRAPH = False
GENERATE_BLOCK_GRAPH = False

AUTOMATE_VTUNE = True
GENERATE_VTUNE_GRAPH = True

# Trace Reader
TRACE_INPUT = "mem_trace.txt"
TRACE_OUTPUT = "trace_reader_output.txt"

AUTOMATE_TRACE_OUTPUT = "automate_trace_output.txt"

HEADER_TRACE = "Video encoder;Encoder Configuration;Video sequence;Resolution;" \
               "Search range;Candidate blocks;Accessed data;Accessed data (GB);"

# Vtune Reader
VTUNE_REPORT_INPUT = "report_vtune.csv"
VTUNE_REPORT_OUTPUT = "vtune_reader_output.txt"

AUTOMATE_VTUNE_OUTPUT = "automate_vtune_output.txt"

HEADER_VTUNE = "Video encoder;Encoder Configuration;Video sequence;Resolution;Search range;Metric;"

VTUNE_SCRIPT = "vtune_script.sh"
DIRECTORY_OUTPUT = "result_dir"

SOURCE_AMPLXE = "source /opt/intel/vtune_amplifier_2019/amplxe-vars.sh\n"
ANALYSE_MEM_CMD = f"amplxe-cl -collect memory-access -data-limit=200000 -result-dir { DIRECTORY_OUTPUT } -- "
GENERATE_CSV_CMD = f"amplxe-cl -report top-down -result-dir { DIRECTORY_OUTPUT } -report-output " \
                   + f"{ VTUNE_REPORT_INPUT } -format csv -csv-delimiter semicolon\n"

# Encoder Paths
HM = "../hm-videomem/"
VTM = "../vtm-mem/"

HEVC = True
VVC = True

ENCODER_CMD = dict()

if HEVC is True:
    ENCODER_CMD["HEVC"] = HM + "bin/TAppEncoderStatic"

if VVC is True:
    ENCODER_CMD["VVC"] = VTM + "bin/EncoderAppStatic"

CONFIG = {"HEVC": {"Low Delay": HM + "cfg/encoder_lowdelay_main.cfg",
                   "Random Access": HM + "cfg/encoder_randomaccess_main.cfg"},
          "VVC": {"Low Delay": VTM + "cfg/encoder_lowdelay_vtm.cfg",
                  "Random Access": VTM + "cfg/encoder_randomaccess_vtm.cfg"}}
VIDEO_CFG_PATH = {"HEVC": HM + "cfg/per-sequence/",
                  "VVC": VTM + "cfg/per-sequence/"}

VIDEO_SEQUENCES_PATH = "../video_sequences"

# Parameters
FRAMES = '17'
SEARCH_RANGE = ['384']


# Auxiliary Functions
def list_all_videos(path):
    paths = []

    for root, directory, files in os.walk(path):
        for f in files:
            video_path = os.path.join(root, f)
            paths.append(video_path)

    return paths


def generate_cmd_array(command, video_path, video_cfg, cfg, sr):
    return [command, '-c', cfg, '-c', video_cfg, '-i', video_path, '-f', FRAMES, '-sr', sr]


def generate_cmd_str(command, video_path, video_cfg, cfg, sr):
    return f'{command} -c {cfg} -c {video_cfg} -i {video_path} -f {FRAMES} -sr {sr}'


def get_video_info(video_path, cfg_path):
    # video_path: '../video_sequences/BQTerrace_1920x1080_60.yuv'
    parse = video_path.split("/")
    video_info = parse.pop()

    # video_info = ['BQTerrace', '1920x1080', '60.yuv']
    video_info = video_info.split("_")

    title = video_info[0]

    resolution = video_info[1].split('x')
    width = resolution[0]
    height = resolution[1]

    video_cfg = cfg_path + title + ".cfg"

    return {"title": title,
            "width": width,
            "height": height,
            "video_cfg": video_cfg}


def append_output_file(routine_output, automate_output):
    with open(routine_output) as trace:
        with open(automate_output, 'a') as automate_read:
            for line in trace:
                automate_read.write(line)


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

    @staticmethod
    def generate_trace(cmd, video_path, video_cfg, cfg_path, sr):
        cmd_array = generate_cmd_array(cmd, video_path, video_cfg, cfg_path, sr)
        subprocess.run(cmd_array)

    @staticmethod
    def clean():
        os.remove(TRACE_INPUT)
        os.remove(TRACE_OUTPUT)
        os.remove("str.bin")
        os.remove("rec.yuv")

    def process_video(self, video_path):
        for encoder, cmd in ENCODER_CMD.items():
            video_info = get_video_info(video_path, VIDEO_CFG_PATH[encoder])

            for cfg, cfg_path in CONFIG[encoder].items():
                for sr in SEARCH_RANGE:
                    self.generate_trace(cmd, video_path, video_info["video_cfg"], cfg_path, sr)

                    self.process_trace(video_info["title"], cfg)
                    append_output_file(TRACE_OUTPUT, AUTOMATE_TRACE_OUTPUT)

                    # Apaga o arquivo trace antes de gerar o próximo
                    self.clean()


class AutomateVtuneReader:
    def __init__(self):
        self.video_paths = []
        self.data_reader = VtuneReader(VTUNE_REPORT_INPUT)
        self.invalid_functions = set()

        # Cria o arquivo de saida
        with open(AUTOMATE_VTUNE_OUTPUT, 'w+') as output_file:
            output_file.write(HEADER_VTUNE)
            output_file.write(self.data_reader.modules_header())

    @staticmethod
    def generate_vtune_script(cmd, video_path, video_cfg, cfg_path, sr):
        cmd_str = generate_cmd_str(cmd, video_path, video_cfg, cfg_path, sr)
        vtune_cmd = ANALYSE_MEM_CMD + cmd_str + "\n"

        with open(VTUNE_SCRIPT, "w") as script:
            script.write("#!/bin/sh\n")
            script.write(SOURCE_AMPLXE)
            script.write(vtune_cmd)
            script.write(GENERATE_CSV_CMD)

    @staticmethod
    def run_vtune_script():
        subprocess.call(["bash", VTUNE_SCRIPT])

    def process_report(self, title, width, height, encoder, encoder_cfg, sr):
        self.data_reader.set_info(title, width, height, encoder, encoder_cfg, sr)
        self.data_reader.read_data()
        self.data_reader.save_data()

    def log_invalid_functions(self):
        self.invalid_functions = self.invalid_functions.union(self.data_reader.function_log)
        with open("undefined_functions.py", 'w') as log:
            log.write("functions = " + pprint.pformat(self.invalid_functions))

    @staticmethod
    def clean():
        os.remove(VTUNE_REPORT_OUTPUT)
        os.remove(VTUNE_REPORT_INPUT)
        os.remove(VTUNE_SCRIPT)
        os.remove("str.bin")
        os.remove("rec.yuv")

        # Remove diretorio gerado por vtune
        shutil.rmtree(DIRECTORY_OUTPUT)

    def process_video(self, video_path):
        for encoder, cmd in ENCODER_CMD.items():
            video_info = get_video_info(video_path, VIDEO_CFG_PATH[encoder])

            for cfg, cfg_path in CONFIG[encoder].items():
                for sr in SEARCH_RANGE:
                    self.generate_vtune_script(cmd, video_path, video_info["video_cfg"], cfg_path, sr)
                    self.run_vtune_script()

                    self.process_report(video_info["title"], video_info["width"],
                                        video_info["height"], encoder, cfg, sr)
                    append_output_file(VTUNE_REPORT_OUTPUT, AUTOMATE_VTUNE_OUTPUT)
                    self.log_invalid_functions()

                    self.clean()


def main():
    if AUTOMATE_TRACE is True:
        automate_trace()

    if AUTOMATE_VTUNE is True:
        automate_vtune()


def automate_trace():
    automate_reader = AutomateTraceReader()
    automate_reader.video_paths = list_all_videos(VIDEO_SEQUENCES_PATH)

    for video_path in automate_reader.video_paths:
        automate_reader.process_video(video_path)

    if GENERATE_TRACE_GRAPH is True:
        generate_trace_graph(AUTOMATE_TRACE_OUTPUT)

    if GENERATE_BLOCK_GRAPH is True:
        generate_block_graph(AUTOMATE_TRACE_OUTPUT)


def automate_vtune():
    automate_reader = AutomateVtuneReader()
    automate_reader.video_paths = list_all_videos(VIDEO_SEQUENCES_PATH)

    for video_path in automate_reader.video_paths:
        automate_reader.process_video(video_path)

    if GENERATE_VTUNE_GRAPH is True:
        generate_vtune_graph(AUTOMATE_VTUNE_OUTPUT)


if __name__ == "__main__":
    main()
