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


class VideoData(object):
    def __init__(self):
        # Informações do video codificado
        self.title = ""
        self.resolution = []
        self.search_range = ""
        self.video_encoder = ""
        self.encoder_config = ""

        # Contadores
        self.candidate_blocks = 0
        self.data_volume = 0
        self.size_pu_counter = BLOCK_SIZES

        # Variaveis auxiliares
        self.current_partition = ""
        self.current_cu_size = 0
        self.current_volume = 0

    def set_resolution(self, x, y):
        self.resolution.append(x)
        self.resolution.append(y)

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
        string = self.video_encoder + ';'
        string += self.encoder_config + ';'
        string += self.title + ';'
        string += self.resolution[0].__str__() + 'x' + self.resolution[1].__str__() + ';'
        string += self.search_range + ';'
        string += int(self.candidate_blocks).__str__() + ';'
        string += int(self.data_volume).__str__() + ';'
        volume_in_gb = int(self.data_volume)/(1024*1024*1024)
        string += round(volume_in_gb, 2).__str__() + ';'

        for partition, counter in self.size_pu_counter.items():
            string += counter.__str__() + ';'

        return string

    def clear(self):
        self.title = ""
        self.resolution = []
        self.search_range = ""
        self.candidate_blocks = 0
        self.data_volume = 0
        self.current_cu_size = 0
        for size in self.size_pu_counter:
            self.size_pu_counter[size] = 0


class TraceData(VideoData):
    def __init__(self):
        super().__init__()


class VtuneData(VideoData):
    def __init__(self):
        super().__init__()