import os
import pprint
import subprocess
import shutil

from data_reader import TraceReader, VtuneReader, VtuneReaderPrediction
from data_formatter import generate_trace_graph, generate_vtune_graph, generate_block_graph

# Routines
AUTOMATE_TRACE = False
GENERATE_TRACE_GRAPH = False
GENERATE_BLOCK_GRAPH = False

AUTOMATE_VTUNE = False
GENERATE_VTUNE_GRAPH = False

PROCESS_REPORTS = True

# Trace Reader
TRACE_INPUT = "mem_trace.txt"
TRACE_OUTPUT = "trace_reader_output.csv"

AUTOMATE_TRACE_OUTPUT = "automate_trace_output.csv"

HEADER_TRACE = "Video encoder,Encoder Configuration,Video sequence,Resolution," \
               "Search range,QP,Candidate blocks,Accessed data,Accessed data (GB),"

# Vtune Reader
VTUNE_REPORT_INPUT = "report_vtune.csv"
VTUNE_REPORT_OUTPUT = "vtune_reader_output.csv"

AUTOMATE_VTUNE_OUTPUT = "automate_vtune_output.csv"

HEADER_VTUNE = "Video encoder,Encoder Configuration,Video sequence,Resolution,Search range,QP,Metric,"

VTUNE_SCRIPT = "vtune_script.sh"
DIRECTORY_OUTPUT = "result_dir"

SOURCE_AMPLXE = "source /opt/intel/vtune_amplifier_2019/amplxe-vars.sh\n"
ANALYSE_MEM_CMD = f"amplxe-cl -collect memory-access -data-limit=158000 -result-dir { DIRECTORY_OUTPUT } -- "
GENERATE_CSV_CMD = f"amplxe-cl -report top-down -result-dir { DIRECTORY_OUTPUT } -report-output " \
                   + f"{ VTUNE_REPORT_INPUT } -format csv -csv-delimiter semicolon\n"

# Report reader
AUTOMATE_VTUNE_PREDICTION_OUTPUT = "vtune_prediction.csv"
REPORTS = "reports"

CFG_SHORT = {
    "RA": "Random Access",
    "LD": "Low Delay",
    "AI": "All Intra"
}

# Encoder Paths
HM = "../hm-videomem/"
VTM = "../vtm-mem/"

HEVC = False
VVC = True

ENCODER_CMD = dict()

if HEVC is True:
    ENCODER_CMD["HEVC"] = HM + "bin/TAppEncoderStatic"

if VVC is True:
    ENCODER_CMD["VVC"] = VTM + "bin/EncoderAppStatic"

CONFIG = {"HEVC": {"Low Delay": HM + "cfg/encoder_lowdelay_main.cfg",
                   "Random Access": HM + "cfg/encoder_randomaccess_main.cfg"},
          "VVC": {"Low Delay": VTM + "cfg/encoder_lowdelay_vtm.cfg",
                  "Random Access": VTM + "cfg/encoder_randomaccess_vtm.cfg",
                  "All Intra": VTM + "cfg/encoder_intra_vtm.cfg"}}
VIDEO_CFG_PATH = {"HEVC": HM + "cfg/per-sequence/",
                  "VVC": VTM + "cfg/per-sequence/"}

VIDEO_SEQUENCES_PATH = "../video_sequences"

# Parameters
FRAMES = '17'
SEARCH_RANGE = ['96']
QP = ['37', '32', '27', '22']


# Auxiliary Functions
def list_all_videos(path):
    paths = list()

    for root, _, files in os.walk(path):
        for f in files:
            video_path = os.path.join(root, f)
            paths.append(video_path)

    return paths


def generate_cmd_array(command, video_path, video_cfg, cfg, sr, qp, bin_path):
    command = [command, '-c', cfg, '-c', video_cfg, '-i',
               video_path, '-f', FRAMES, '-sr', sr, '-q',
               qp, '-b', bin_path]

    if cfg == VTM + "cfg/encoder_intra_vtm.cfg":
        command.extend(['-ts', '1'])

    return command


def get_video_info(video_path, cfg_path):
    # video_path: '../video_sequences/BQTerrace_1920x1080_60.yuv'
    parse = video_path.split("/")
    video_info = parse.pop()

    # video_info = ['BQTerrace', '1920x1080', '60.yuv']
    title, resolution, *_ = video_info.split("_")
    width, height = resolution.split('x')

    video_cfg = cfg_path + title + ".cfg"

    return title, width, height, video_cfg


def append_output_file(routine_output, automate_output):
    with open(routine_output) as trace:
        with open(automate_output, 'a') as automate_read:
            for line in trace:
                automate_read.write(line)


def create_output_file(output_path, header, aux_data):
    with open(output_path, 'w+') as output_file:
        output_file.write(header)
        output_file.write(aux_data)


# Report processor functions
def read_reports(title, cfg, qp, data_reader, report_path, automate_output):
    data_reader.set_info(title, 1920, 1080, 'VVC', cfg, '96', qp)
    data_reader.read_data(report_path)
    data_reader.save_data()
    append_output_file(VTUNE_REPORT_OUTPUT, automate_output)
    os.remove(VTUNE_REPORT_OUTPUT)


def get_report_info(report):
    title, cfg_short, qp, *_ = report.split('_')
    qp = qp[2:4]
    cfg = CFG_SHORT[cfg_short]

    return title, qp, cfg


class AutomateTraceReader(object):
    def __init__(self):
        self.video_paths = list()
        self.data_reader = TraceReader(TRACE_INPUT)

        # Create output file
        block_sizes = self.data_reader.block_sizes()
        create_output_file(AUTOMATE_TRACE_OUTPUT, HEADER_TRACE, block_sizes)

    def process_trace(self, video_title, cfg, qp):
        self.data_reader.read_data(video_title, cfg, qp)
        self.data_reader.save_data()

    @staticmethod
    def generate_trace(cmd, video_path, video_cfg, cfg_path, sr, qp):
        cmd_array = generate_cmd_array(
            cmd, video_path, video_cfg, cfg_path, sr, qp, "str.bin")
        subprocess.run(cmd_array)

    @staticmethod
    def clean():
        os.remove(TRACE_INPUT)
        os.remove(TRACE_OUTPUT)
        os.remove("str.bin")
        os.remove("rec.yuv")

    def process_video(self, video_path):
        for encoder, cmd in ENCODER_CMD.items():
            title, _, _, video_cfg = get_video_info(
                video_path, VIDEO_CFG_PATH[encoder])

            for cfg, cfg_path in CONFIG[encoder].items():
                for sr in SEARCH_RANGE:
                    for qp in QP:
                        self.generate_trace(
                            cmd, video_path, video_cfg, cfg_path, sr, qp)

                        self.process_trace(title, cfg, qp)
                        append_output_file(TRACE_OUTPUT, AUTOMATE_TRACE_OUTPUT)

                        self.clean()


class AutomateVtuneReader:
    def __init__(self):
        self.video_paths = list()
        self.data_reader = VtuneReader()
        self.invalid_functions = set()

        modules = self.data_reader.get_modules_header()
        create_output_file(AUTOMATE_VTUNE_OUTPUT, HEADER_VTUNE, modules)

    @staticmethod
    def generate_vtune_script(cmd, video_path, video_cfg, cfg_path, sr, qp, bin_path):
        cmd_array = generate_cmd_array(
            cmd, video_path, video_cfg, cfg_path, sr, qp, bin_path)

        cmd_str = " ".join(cmd_array)

        vtune_cmd = ANALYSE_MEM_CMD + cmd_str + "\n"
        print(vtune_cmd)

        with open(VTUNE_SCRIPT, "w") as script:
            script.write("#!/bin/sh\n")
            script.write(SOURCE_AMPLXE)
            script.write(vtune_cmd)
            script.write(GENERATE_CSV_CMD)

    @staticmethod
    def run_vtune_script():
        subprocess.call(["bash", VTUNE_SCRIPT])

    def process_report(self, title, width, height, encoder, encoder_cfg, sr, qp):
        self.data_reader.set_info(
            title, width, height, encoder, encoder_cfg, sr, qp)
        self.data_reader.read_data(VTUNE_REPORT_INPUT)
        self.data_reader.save_data()

    def log_invalid_functions(self):
        self.invalid_functions = self.invalid_functions.union(
            self.data_reader.function_log)

        with open("undefined_functions.py", 'w') as log:
            log.write("\nfunctions = " +
                      pprint.pformat(self.invalid_functions))

    @staticmethod
    def clean(name):
        os.remove(VTUNE_REPORT_OUTPUT)
        os.rename(VTUNE_REPORT_INPUT, name)
        os.remove(VTUNE_SCRIPT)
        # os.remove("str.bin")
        os.remove("rec.yuv")

        # Remove directory generated by vtune
        shutil.rmtree(DIRECTORY_OUTPUT)

    def process_video(self, video_path):
        for encoder, cmd in ENCODER_CMD.items():
            title, width, height, video_cfg = get_video_info(
                video_path, VIDEO_CFG_PATH[encoder])

            for cfg, cfg_path in CONFIG[encoder].items():
                cfg_short = cfg.split()[0][0] + cfg.split()[1][0]

                for sr in SEARCH_RANGE:
                    for qp in QP:
                        video = f'{title}_{cfg_short}_QP{qp}'

                        bin_path = f'bins/{video}.bin'

                        self.generate_vtune_script(
                            cmd, video_path, video_cfg, cfg_path, sr, qp, bin_path)
                        self.run_vtune_script()

                        self.process_report(
                            title, width, height, encoder, cfg, sr, qp)
                        append_output_file(VTUNE_REPORT_OUTPUT,
                                           AUTOMATE_VTUNE_OUTPUT)

                        self.log_invalid_functions()

                        report = f'reports/{video}.csv'
                        self.clean(report)


def main():
    if AUTOMATE_TRACE is True:
        automate_trace()

    if AUTOMATE_VTUNE is True:
        automate_vtune()

    if PROCESS_REPORTS is True:
        process_reports()


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


def process_reports():
    vtune_reader = VtuneReader()
    vtune_reader_prediction = VtuneReaderPrediction()

    # Create output files
    modules = vtune_reader.get_modules_header()
    create_output_file(AUTOMATE_VTUNE_OUTPUT, HEADER_VTUNE, modules)

    modules = vtune_reader_prediction.get_modules_header()
    create_output_file(AUTOMATE_VTUNE_PREDICTION_OUTPUT, HEADER_VTUNE, modules)

    for root, _, files in os.walk(REPORTS):
        for report in files:
            title, qp, cfg = get_report_info(report)
            report_path = os.path.join(root, report)

            read_reports(title, cfg, qp, vtune_reader,
                         report_path, AUTOMATE_VTUNE_OUTPUT)
            read_reports(title, cfg, qp, vtune_reader_prediction,
                         report_path, AUTOMATE_VTUNE_PREDICTION_OUTPUT)


if __name__ == "__main__":
    main()
