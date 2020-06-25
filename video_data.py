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

MODULES = ("Inter",
           "Intra",
           "TQ",
           "Others",
           "Entropy",
           "Control",
           "Filters")

MODULES_PREDICTION = ("IME",
                      "IME:RDCost",
                      "FME",
                      "FME:RDCost",
                      "FME:Interpolation",
                      "Affine",
                      "Affine:RDCost",
                      "Geo",
                      "Geo:RDCost",
                      "Intra",
                      "Intra:RDCost",
                      "Inter")


class VideoData(object):
    def __init__(self):
        # Encoded video info
        self.title = str()
        self.resolution = list()
        self.search_range = str()
        self.video_encoder = str()
        self.encoder_config = str()
        self.qp = str()

    def set_resolution(self, width, height):
        self.resolution.append(width)
        self.resolution.append(height)

    def __str__(self):
        string = f'{ self.video_encoder },'
        string += f'{ self.encoder_config },'
        string += f'{ self.title },'
        string += f'{ self.resolution[0] }x{ self.resolution[1] },'
        string += f'{ self.search_range },'
        string += f'{ self.qp },'

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

    def __str__(self):
        string = str(super())

        string += f'{ int(self.candidate_blocks) },'
        string += f'{ int(self.data_volume) },'

        volume_in_gb = int(self.data_volume) / (1024 * 1024 * 1024)

        string += f'{ round(volume_in_gb, 2) },'

        for _, counter in self.size_pu_counter.items():
            string += f'{ counter },'

        string += '\n'

        return string

    def clear(self):
        super().clear()

        self.candidate_blocks = 0
        self.data_volume = 0
        self.current_cu_size = 0
        for size in self.size_pu_counter:
            self.size_pu_counter[size] = 0


class VtuneData(VideoData):
    def __init__(self, modules_list):
        super().__init__()

        self.modules_list = modules_list
        self.modules = dict()

        # Initialize the counters in 0
        for module in self.modules_list:
            self.modules[module] = {"Loads": 0,
                                    "Stores": 0}

    def increment_load_counter(self, load_mem, module):
        self.modules[module]["Loads"] += load_mem

    def increment_store_counter(self, store_mem, module):
        self.modules[module]["Stores"] += store_mem

    def __str__(self):
        string = str()

        for metric in ("Loads", "Stores"):
            string += super().__str__()

            string += f'{ metric },'

            for module in self.modules_list:
                string += f'{ self.modules[module][metric] },'

            string += "\n"

        return string

    def clear(self):
        super().clear()

        for module in self.modules:
            self.modules[module]["Loads"] = 0
            self.modules[module]["Stores"] = 0


class BlockStatsData(VideoData):
    def __init__(self):
        super().__init__()

        self.block_sizes = BLOCK_SIZES
        self.invalid_sizes = dict()

    def increment_block_size(self, block_size):
        try:
            self.block_sizes[block_size] += 1
        except KeyError:
            self.invalid_sizes.setdefault(block_size, 0)
            self.invalid_sizes[block_size] += 1

    def __str__(self):
        string = f'{ self.title },'
        string += f'{ self.encoder_config },'
        string += f'{ self.qp },'

        for _, total in self.block_sizes.items():
            string += f'{ total },'

        string += '\n'

        return string

    def clear(self):
        super().clear()

        for block_size in BLOCK_SIZES:
            self.block_sizes[block_size] = 0

        self.invalid_sizes = {}
