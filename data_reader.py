import json

from video_data import TraceData, VtuneData, MODULES

# Numero de blocos acessados baseado na janela de busca
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

# Formato da partição
PARTITION_PU = {
    '0': [1, 1],  # 2N X 2N
    '1': [0.5, 0.5],  # 2N X N
    '2': [0.5, 0.5],  # N X 2N
    '3': [0.25, 0.25],  # N X N
    '4': [0.25, 0.75],  # 2N x nU
    '5': [0.75, 0.25],  # 2N x nD
    '6': [0.25, 0.75],  # nL x 2N
    '7': [0.75, 0.25]  # nR x 2N
}

RASTER_SEARCH = 3

TRACE_PATH = "../hm-videomem/mem_trace.txt"  # "vvc_mem_trace.txt"
TRACE_OUTPUT = "trace_reader_output.txt"
VIDEO_NAME = "BasketballDrive"
CFG = "Low Delay"

VTUNE_REPORT_PATH = "samples/report_vtune.csv"
VTUNE_REPORT_OUTPUT = "vtune_reader_output.txt"

with open('function2module.json', 'r') as fp:
    FUNCTIONS_MAP = json.load(fp)


class TraceReader(object):
    def __init__(self, input_path):
        self.input_path = input_path
        self.trace_data = TraceData()
        self.first_line = True

    def read_data(self, video_title, encoder_cfg):
        self.trace_data.title = video_title
        self.trace_data.encoder_config = encoder_cfg

        with open(self.input_path) as input_file:
            for line in input_file:
                self.process_line(line)

    def process_line(self, line):
        if line.startswith('U '):
            self.get_size(line)

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

        # A primeira linha contem as informações do video
        elif self.first_line:
            self.first_line = False
            self.set_info(line)

        # Se não se enquadra nenhum dos casos, pula
        else:
            return

    def get_size(self, line):
        # U <xCU> <yCU> <size>
        data = line.split()
        size = int(data[3])
        self.trace_data.current_cu_size = size

    def process_pu(self, line):
        # P <sizePU> <idPart> <ref_frame_id>
        data = line.split()

        # Garante que P esta formatado certo
        if data.__len__() != 4:
            return

        pu = data[1]

        if int(pu) < 4:
            id_part = 0
        else:
            id_part = int(data[2])

        partition = PARTITION_PU[pu][id_part] * self.trace_data.current_cu_size

        self.trace_data.set_current_partition(self.trace_data.current_cu_size, partition)

        volume = self.trace_data.current_cu_size * partition
        self.trace_data.current_volume = volume

    def process_block(self):
        # C <xCand> <yCand>
        self.trace_data.increment_candidate_blocks(1)
        self.trace_data.increment_data_volume(self.trace_data.current_volume)

        self.trace_data.increment_pu_counter(1)

    def process_first_search(self, line):
        # F <itID>
        data = line.split()
        it_id = data[1]

        candidate_blocks = BLOCKS[it_id]
        self.trace_data.increment_candidate_blocks(candidate_blocks)

        self.trace_data.increment_data_volume(self.trace_data.current_volume * candidate_blocks)
        self.trace_data.increment_pu_counter(candidate_blocks)

    def process_rectangle(self, line):
        # R <xL> <xR> <yT> <yB> <step>
        data = line.split()

        ver_size = int(data[2]) - int(data[1])
        hor_size = int(data[4]) - int(data[3])

        candidate_blocks = int((ver_size / RASTER_SEARCH) + (hor_size / RASTER_SEARCH))
        self.trace_data.increment_candidate_blocks(candidate_blocks)

        self.trace_data.increment_pu_counter(candidate_blocks)

        volume = candidate_blocks * self.trace_data.current_cu_size
        self.trace_data.increment_data_volume(volume)

    def set_info(self, line):
        # <encoder> <name> <width> <height> <searchRange>
        data = line.split()

        self.trace_data.video_encoder = data[0]
        self.trace_data.set_resolution(data[2], data[3])
        self.trace_data.search_range = data[4]

    def vvc_get_volume(self, line):
        # VU <xCU> <yCU> <size_hor> <size_ver> <depth>
        data = line.split()

        size_hor = int(data[3])
        size_ver = int(data[4])

        current_volume = size_hor * size_ver

        self.trace_data.current_volume = current_volume

        self.trace_data.set_current_partition(size_hor, size_ver)

    def block_sizes(self):
        block_size_string = ""

        for block_size, counter in self.trace_data.size_pu_counter.items():
            block_size_string += block_size + ";"

        block_size_string += "\n"

        return block_size_string

    def save_data(self):
        with open(TRACE_OUTPUT, 'w') as output_file:
            output_file.write(self.trace_data.return_string() + "\n")

        self.trace_data.clear()
        self.first_line = True


class VtuneReader(object):
    def __init__(self, vtune_input_path):
        self.input_path = vtune_input_path
        self.vtune_data = VtuneData()
        self.function_log = set()

    def set_info(self, title, width, height, encoder, encoder_cfg, sr):
        self.vtune_data.title = title
        self.vtune_data.set_resolution(width, height)
        self.vtune_data.video_encoder = encoder
        self.vtune_data.encoder_config = encoder_cfg
        self.vtune_data.search_range = sr

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

        self.vtune_data.set_module(module)

        load_mem = self.get_load_mem(line)
        self.vtune_data.increment_load_counter(load_mem, module)

        store_mem = self.get_store_mem(line)
        self.vtune_data.increment_store_counter(store_mem, module)

    @staticmethod
    def get_module(line):
        data = line.split(";")
        function = data[0]

        # Retira os espaços em branco do inicio da string
        while function[0] == " ":
            function = function[1::]

        try:
            module = {
                "value": FUNCTIONS_MAP[function],
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
            module_string += module + ";"

        module_string += "\n"

        return module_string

    def save_data(self):
        with open(VTUNE_REPORT_OUTPUT, 'w') as output_file:
            output_file.write(self.vtune_data.return_string())

        self.vtune_data.clear()


def main():
    # trace_reader = TraceReader(TRACE_PATH)
    # trace_reader.read_data(VIDEO_NAME, CFG)
    # trace_reader.save_data()
    vtune_reader = VtuneReader(VTUNE_REPORT_PATH)
    vtune_reader.read_data()
    vtune_reader.save_data()


if __name__ == "__main__":
    main()
