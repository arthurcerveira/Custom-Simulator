import json
from datetime import datetime
import pprint

from video_data import TraceData, VtuneData, BlockStatsData, MODULES, BLOCK_SIZES

# Number of blocks based on search window
BLOCKS = {
    '1': 4,
    '2': 8,
    '4': 8,
    '8': 8,
    '16': 16,
    '32': 16,
    '64': 16,
    '128': 16,
    '256': 16
}

# Partition format
PARTITION_PU = {
    '0': ([1, 1],     [1, 1]),      # 2N X 2N
    '1': ([1, 0.5],   [1, 0.5]),    # 2N X N
    '2': ([0.5, 1],   [0.5, 1]),    # N X 2N
    '3': ([0.5, 0.5], [0.5, 0.5]),  # N X N
    '4': ([1, 0.75],  [1, 0.25]),   # 2N x nU
    '5': ([1, 0.25],  [1, 0.75]),   # 2N x nD
    '6': ([0.25, 1],  [0.75, 1]),   # nL x 2N
    '7': ([0.75, 1],  [0.25, 1])    # nR x 2N
}

RASTER_SEARCH = 3

TRACE_PATH = "samples/mem_trace.txt"  # "vvc_mem_trace.txt"
TRACE_OUTPUT = "trace_reader_output.csv"

VTUNE_REPORT_PATH = "samples/report_vtune.csv"
VTUNE_REPORT_OUTPUT = "vtune_reader_output.csv"

BLOCK_STATS_PATH = "samples/block_stats.csv"
BLOCK_STATS_OUTPUT = "block_stats_output.csv"
BLOCK_STATS_HEADER = "Video Sequence, Encoder Configuration, QP, "

VIDEO_NAME = "Campfire"
CFG = "Low Delay"

with open('function2module-HM.json', 'r') as fp:
    FUNCTIONS_MAP_HM = json.load(fp)

with open('function2module-VTM.json', 'r') as fp:
    FUNCTIONS_MAP_VTM = json.load(fp)

FUNCTION_MAP = {"HEVC": FUNCTIONS_MAP_HM,
                "VVC": FUNCTIONS_MAP_VTM}


class TraceReader(object):
    def __init__(self, input_path):
        self.input_path = input_path
        self.trace_data = TraceData()
        self.first_line = True

    def read_data(self, video_title, encoder_cfg, qp):
        print(f'\n[{datetime.now():%H:%M:%S}] Calculating memory '
              + f'accesses in {video_title} for {encoder_cfg}')

        self.trace_data.title = video_title
        self.trace_data.encoder_config = encoder_cfg
        self.trace_data.qp = str(qp)

        with open(self.input_path) as input_file:
            for line in input_file:
                self.process_line(line)

    def process_line(self, line):
        if line.startswith('U '):
            self.get_size(line)

        elif line.startswith('I '):
            self.process_frame(line)

        elif line.startswith('P '):
            self.process_pu(line)

        elif line.startswith('C '):
            self.process_block()

        elif line.startswith('F '):
            self.process_first_search(line)

        elif line.startswith('R '):
            self.process_rectangle(line)

        # Codificador VVC
        elif line.startswith("VU"):
            self.vvc_get_volume(line)

        # A primeira linha contém as informações do video
        elif self.first_line:
            self.first_line = False
            self.set_info(line)

        # Se não se enquadra nenhum dos casos, pula
        else:
            return

    def process_frame(self, line):
        _, frame = line.split()

        print(f"[{datetime.now():%H:%M:%S}] Processing frame {frame}.")

    def get_size(self, line):
        # U <xCU> <yCU> <size>
        *_, size = line.split()

        self.trace_data.current_cu_size = int(size)

    def process_pu(self, line):
        # P <sizePU> <idPart> <ref_frame_id>
        try:
            _, pu, id_part, _ = line.split()
        except ValueError:  # Esse erro ocorre quando P não está bem formatado
            return

        partition_hor, partition_ver = PARTITION_PU[pu][int(id_part)]
        cu_size = self.trace_data.current_cu_size

        size_hor = partition_hor * cu_size
        size_ver = partition_ver * cu_size

        self.trace_data.set_current_partition(size_hor, size_ver)

        volume = size_hor * size_ver
        self.trace_data.current_volume = volume

    def process_block(self):
        # C <xCand> <yCand>
        self.trace_data.increment_candidate_blocks(1)
        self.trace_data.increment_data_volume(self.trace_data.current_volume)

        self.trace_data.increment_pu_counter(1)

    def process_first_search(self, line):
        # F <itID>
        _, it_id = line.split()

        candidate_blocks = BLOCKS[it_id]
        self.trace_data.increment_candidate_blocks(candidate_blocks)

        self.trace_data.increment_data_volume(
            self.trace_data.current_volume * candidate_blocks)
        self.trace_data.increment_pu_counter(candidate_blocks)

    def process_rectangle(self, line):
        # R <xL> <xR> <yT> <yB> <step>
        _, x_position_left, x_position_right, y_position_top, y_position_bottom, _ = line.split()

        hor_size = int(x_position_right) - int(x_position_left)
        ver_size = int(y_position_bottom) - int(y_position_top)

        candidate_blocks = int(
            (ver_size / RASTER_SEARCH) + (hor_size / RASTER_SEARCH))
        self.trace_data.increment_candidate_blocks(candidate_blocks)

        self.trace_data.increment_pu_counter(candidate_blocks)

        volume = candidate_blocks * self.trace_data.current_cu_size
        self.trace_data.increment_data_volume(volume)

    def set_info(self, line):
        # <encoder> <title> <width> <height> <searchRange>
        encoder, _, width, height, search_range = line.split()

        self.trace_data.video_encoder = encoder
        self.trace_data.set_resolution(width, height)
        self.trace_data.search_range = search_range

    def vvc_get_volume(self, line):
        # VU <xCU> <yCU> <size_hor> <size_ver> <depth>
        *_, size_hor, size_ver, _ = line.split()

        size_hor = int(size_hor)
        size_ver = int(size_ver)

        current_volume = size_hor * size_ver

        self.trace_data.current_volume = current_volume

        self.trace_data.set_current_partition(size_hor, size_ver)

    def block_sizes(self):
        block_size_string = str()

        for block_size, _ in self.trace_data.size_pu_counter.items():
            block_size_string += block_size + ","

        block_size_string += "\n"

        return block_size_string

    def save_data(self):
        with open(TRACE_OUTPUT, 'w') as output_file:
            output_file.write(str(self.trace_data))

        self.trace_data.clear()
        self.first_line = True


class VtuneReader(object):
    def __init__(self, vtune_input_path):
        self.input_path = vtune_input_path
        self.vtune_data = VtuneData()
        self.function_log = set()
        self.function_map = dict()

    def set_info(self, title, width, height, encoder, encoder_cfg, sr, qp):
        self.vtune_data.title = title
        self.vtune_data.set_resolution(width, height)
        self.vtune_data.video_encoder = encoder
        self.vtune_data.encoder_config = encoder_cfg
        self.vtune_data.search_range = sr
        self.vtune_data.qp = qp

        self.function_map = FUNCTION_MAP[encoder]

    def read_data(self):
        with open(self.input_path) as input_file:
            # Pula as duas primeiras linhas
            next(input_file)
            next(input_file)

            for line in input_file:
                self.process_line(line)

    def process_line(self, line):
        module = self.get_module(line)

        if module["is_valid"] is True:
            module = module["value"]
        else:
            self.log_undefined_function(module)
            module = "Others"

        load_mem = self.get_load_mem(line)
        self.vtune_data.increment_load_counter(load_mem, module)

        store_mem = self.get_store_mem(line)
        self.vtune_data.increment_store_counter(store_mem, module)

    def get_module(self, line):
        function, *_ = line.split(";")

        # Retira os espaços em branco do inicio da string
        while function[0] == " ":
            function = function[1::]

        try:
            module = {
                "value": self.function_map[function],
                "function": function,
                "is_valid": True
            }
        except KeyError:
            module = {
                "value": None,
                "function": function,
                "is_valid": False
            }

        return module

    @staticmethod
    def get_load_mem(line):
        data = line.split(";")
        load_mem = int(data[18])
        return load_mem

    @staticmethod
    def get_store_mem(line):
        data = line.split(";")
        store_mem = int(data[20])
        return store_mem

    def log_undefined_function(self, module):
        self.function_log.add(module["function"])

    @staticmethod
    def modules_header():
        module_string = ""

        for module in MODULES:
            module_string += module + ","

        module_string += "\n"

        return module_string

    def save_data(self):
        with open(VTUNE_REPORT_OUTPUT, 'w') as output_file:
            output_file.write(str(self.vtune_data))

        self.vtune_data.clear()


class BlockStatsReader(object):
    def __init__(self, input_path):
        self.block_data = BlockStatsData()
        self.input_path = input_path

        self.header = BLOCK_STATS_HEADER

        for block_size in BLOCK_SIZES:
            self.header += f'{block_size}, '

    def read_data(self, video_title, encoder_cfg, qp):
        self.block_data.title = video_title
        self.block_data.encoder_config = encoder_cfg
        self.block_data.qp = qp

        with open(self.input_path) as input_file:
            for line in input_file:
                self.process_line(line)

    def process_line(self, line):
        # Skips header
        if line.startswith('#'):
            return

        _, ref_frame, _, _, block_width, block_height, *_ = line.split(';')

        # Frame 0 is processed by intra-prediction module
        if ref_frame == '0':
            return

        block_size = f'{int(block_width)}x{int(block_height)}'

        self.block_data.increment_block_size(block_size)

    def save_data(self):
        with open(BLOCK_STATS_OUTPUT, 'w') as output_file:
            output_file.write(self.header + '\n')
            output_file.write(str(self.block_data))

        with open("invalid_sizes.py", 'w') as log:
            log.write(
                f'invalid_sizes = {pprint.pformat(self.block_data.invalid_sizes)}')

        self.block_data.clear()


def main():
    # trace_reader = TraceReader(TRACE_PATH)
    # trace_reader.read_data(VIDEO_NAME, CFG, 22)
    # trace_reader.save_data()
    # vtune_reader = VtuneReader(VTUNE_REPORT_PATH)
    # vtune_reader.read_data()
    # vtune_reader.save_data()
    block_reader = BlockStatsReader(BLOCK_STATS_PATH)
    block_reader.read_data(VIDEO_NAME, CFG, 22)
    block_reader.save_data()


if __name__ == "__main__":
    main()
