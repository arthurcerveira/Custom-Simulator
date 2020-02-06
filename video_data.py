import json

BLOCK_SIZES = {
    "128x128": 0,
    "128x64": 0,
    "64x128": 0,
    "64x64": 0,
    "64x32": 0,
    "32x64": 0,
    "32x32": 0,
    "64x16": 0,
    "16x64": 0,
    "32x24": 0,
    "24x32": 0,
    "32x16": 0,
    "16x32": 0,
    "64x8": 0,
    "8x64": 0,
    "16x16": 0,
    "32x8": 0,
    "8x32": 0,
    "64x4": 0,
    "4x64": 0,
    "16x12": 0,
    "12x16": 0,
    "16x8": 0,
    "8x16": 0,
    "32x4": 0,
    "4x32": 0,
    "8x8": 0,
    "16x4": 0,
    "4x16": 0,
    "8x4": 0,
    "4x8": 0
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


class VideoData(object):
    def __init__(self):
        # Encoded video info
        self.title = str()
        self.resolution = list()
        self.search_range = str()
        self.video_encoder = str()
        self.encoder_config = str()

    def set_resolution(self, width, height):
        self.resolution.append(width)
        self.resolution.append(height)

    def return_string(self):
        string = f'{ self.video_encoder };'
        string += f'{ self.encoder_config };'
        string += f'{ self.title };'
        string += f'{ self.resolution[0] }x{ self.resolution[1] };'
        string += f'{ self.search_range };'

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
        self.current_partition = str()
        self.current_cu_size = 0
        self.current_volume = 0

    def increment_candidate_blocks(self, candidate_blocks):
        self.candidate_blocks += candidate_blocks

    def increment_data_volume(self, volume):
        self.data_volume += volume

    def set_current_partition(self, size_hor, size_ver):
        partition_string = f'{ int(size_hor) }x{ int(size_ver) }'

        self.current_partition = partition_string

    def increment_pu_counter(self, blocks):
        self.size_pu_counter[self.current_partition] += blocks

    def return_string(self):
        string = super().return_string()

        string += f'{ int(self.candidate_blocks) };'
        string += f'{ int(self.data_volume) };'

        volume_in_gb = int(self.data_volume) / (1024 * 1024 * 1024)

        string += f'{ round(volume_in_gb, 2) };'

        for partition, counter in self.size_pu_counter.items():
            string += f'{ counter };'

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

        self.modules = dict()

        # Inicializa os contadores de em 0
        for module in MODULES:
            self.modules[module] = {"Loads": 0,
                                    "Stores": 0}

    def increment_load_counter(self, load_mem, module):
        self.modules[module]["Loads"] += load_mem

    def increment_store_counter(self, store_mem, module):
        self.modules[module]["Stores"] += store_mem

    def return_string(self):
        string = str()

        for metric in ("Loads", "Stores"):
            string += super().return_string()

            string += f'{ metric };'

            for module in MODULES:
                string += f'{ self.modules[module][metric] };'

            string += "\n"

        return string

    def clear(self):
        super().clear()

        for module in self.modules:
            self.modules[module]["Loads"] = 0
            self.modules[module]["Stores"] = 0
