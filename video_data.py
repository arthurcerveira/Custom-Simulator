import json

BLOCK_SIZES = {
    "128x128": 0,
    "128x64": 0,
    "64x64": 0,
    "64x32": 0,
    "32x32": 0,
    "64x16": 0,
    "32x24": 0,
    "32x16": 0,
    "64x8": 0,
    "16x16": 0,
    "32x8": 0,
    "64x4": 0,
    "16x12": 0,
    "16x8": 0,
    "32x4": 0,
    "8x8": 0,
    "16x4": 0,
    "8x4": 0
}

MODULES = ("Inter (IME)",
           "Inter (FME)",
           "Intra",
           "Transf. and Quant.",
           "Others",
           "Entropy",
           "Encoder control",
           "Current frame",
           "Filters")

with open('function2module.json', 'r') as fp:
    FUNCTIONS_MAP = json.load(fp)


class VideoData(object):
    def __init__(self):
        # Encoded video info
        self.title = ""
        self.resolution = []
        self.search_range = ""
        self.video_encoder = ""
        self.encoder_config = ""

    def set_resolution(self, x, y):
        self.resolution.append(x)
        self.resolution.append(y)

    def return_string(self):
        string = self.video_encoder + ';'
        string += self.encoder_config + ';'
        string += self.title + ';'
        string += self.resolution[0].__str__() + 'x' + self.resolution[1].__str__() + ';'
        string += self.search_range + ';'

        return string

    def clear(self):
        self.title = ""
        self.resolution.clear()
        self.search_range = ""
        self.video_encoder = ""
        self.encoder_config = ""


class TraceData(VideoData):
    def __init__(self):
        super().__init__()

        # Counter
        self.candidate_blocks = 0
        self.data_volume = 0
        self.size_pu_counter = BLOCK_SIZES

        # Aux Variables
        self.current_partition = ""
        self.current_cu_size = 0
        self.current_volume = 0

    def increment_candidate_blocks(self, candidate_blocks):
        self.candidate_blocks += candidate_blocks

    def increment_data_volume(self, volume):
        self.data_volume += volume

    def set_current_partition(self, size_hor, size_ver):
        # Coloca sempre o maior lado antes
        if size_hor >= size_ver:
            partition_string = size_hor.__str__()
            partition_string += 'x'
            partition_string += int(size_ver).__str__()

        else:
            partition_string = int(size_ver).__str__()
            partition_string += 'x'
            partition_string += size_hor.__str__()

        self.current_partition = partition_string

    def increment_pu_counter(self, blocks):
        # Se não houver a partição atual no pu counter, cria e inicializa em 0
        self.size_pu_counter.setdefault(self.current_partition, 0)

        self.size_pu_counter[self.current_partition] += blocks

    def return_string(self):
        string = super().return_string()

        string += int(self.candidate_blocks).__str__() + ';'
        string += int(self.data_volume).__str__() + ';'
        volume_in_gb = int(self.data_volume) / (1024 * 1024 * 1024)
        string += round(volume_in_gb, 2).__str__() + ';'

        for partition, counter in self.size_pu_counter.items():
            string += counter.__str__() + ';'

        return string

    def clear(self):
        super().clear()

        self.candidate_blocks = 0
        self.data_volume = 0
        self.current_cu_size = 0
        for size in self.size_pu_counter:
            self.size_pu_counter[size] = 0


class VtuneData(VideoData):
    def __init__(self):
        super().__init__()

        self.modules = {}

    def set_module(self, module):
        # Se o modulo não estiver em modules, cria e inicializa seus contadores em 0
        self.modules.setdefault(module, {"Loads": 0,
                                         "Stores": 0})

    def increment_load_counter(self, load_mem, module):
        self.modules[module]["Loads"] += load_mem

    def increment_store_counter(self, store_mem, module):
        self.modules[module]["Stores"] += store_mem

    def return_string(self):
        string = ""

        for metric in ("Loads", "Stores"):
            string += super().return_string()

            string += metric + ";"

            for module in MODULES:
                string += self.modules[module][metric].__str__() + ";"

            string += "\n"

        return string

    def clear(self):
        super().clear()
        self.modules.clear()
