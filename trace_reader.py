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
    '0': [1, 1],        # 2N X 2N
    '1': [0.5, 0.5],    # 2N X N
    '2': [0.5, 0.5],    # N X 2N
    '3': [0.25, 0.25],  # N X N
    '4': [0.25, 0.75],  # 2N x nU
    '5': [0.75, 0.25],  # 2N x nD
    '6': [0.25, 0.75],  # nL x 2N
    '7': [0.75, 0.25]   # nR x 2N
}

RASTER_SEARCH = 3

TRACE_PATH = "../hm-videomem/mem_trace.txt"  # "vvc_mem_trace.txt"
VIDEO_NAME = "BQSquare"
ENCODER = "HEVC"
CFG = "Low Delay"


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
        self.size_pu_counter = {}

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

        for partition, counter in self.size_pu_counter.items():
            string += partition + ':'
            string += counter.__str__() + ';'

        return string

    def clear(self):
        self.title = ""
        self.resolution = []
        self.search_range = ""
        self.candidate_blocks = 0
        self.data_volume = 0
        self.current_cu_size = 0


class DataReader(object):
    def __init__(self, input_path):
        self.input_path = input_path
        self.video_data = VideoData()
        self.first_line = True

    def read_data(self, video_title, video_encoder, encoder_cfg):
        self.video_data.title = video_title
        self.video_data.video_encoder = video_encoder
        self.video_data.encoder_config = encoder_cfg

        with open(self.input_path) as input_file:
            for line in input_file:
                self.process_line(line)

    def process_line(self, line):
        if line.startswith('U'):
            self.get_size(line)

        elif line.startswith('P'):
            self.process_pu(line)

        elif line.startswith('C '):
            self.process_block()

        elif line.startswith('F'):
            self.process_first_search(line)

        elif line.startswith('R'):
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
        self.video_data.current_cu_size = size

    def process_pu(self, line):
        # P <sizePU> <idPart> <ref_frame_id>
        data = line.split()
        pu = data[1]

        if int(pu) < 4:
            id_part = 0
        else:
            id_part = int(data[2])

        partition = PARTITION_PU[pu][id_part] * self.video_data.current_cu_size

        self.video_data.set_current_partition(self.video_data.current_cu_size, partition)

        volume = self.video_data.current_cu_size * partition
        self.video_data.current_volume = volume

    def process_block(self):
        # C <xCand> <yCand>
        self.video_data.increment_candidate_blocks(1)
        self.video_data.increment_data_volume(self.video_data.current_volume)

        self.video_data.increment_pu_counter(1)

    def process_first_search(self, line):
        # F <itID>
        data = line.split()
        it_id = data[1]

        candidate_blocks = BLOCKS[it_id]
        self.video_data.increment_candidate_blocks(candidate_blocks)

        self.video_data.increment_data_volume(self.video_data.current_volume * candidate_blocks)
        self.video_data.increment_pu_counter(candidate_blocks)

    def process_rectangle(self, line):
        # R <xL> <xR> <yT> <yB> <step>
        data = line.split()

        ver_size = int(data[2]) - int(data[1])
        hor_size = int(data[4]) - int(data[3])

        candidate_blocks = (ver_size / RASTER_SEARCH) + (hor_size / RASTER_SEARCH)
        self.video_data.increment_candidate_blocks(candidate_blocks)

        self.video_data.increment_pu_counter(candidate_blocks)

        volume = candidate_blocks * self.video_data.current_cu_size
        self.video_data.increment_data_volume(volume)

    def set_info(self, line):
        # <width> <height> <searchRange>
        data = line.split()

        self.video_data.set_resolution(data[0], data[1])
        self.video_data.search_range = data[2]

    def vvc_get_volume(self, line):
        # VU <xCU> <yCU> <size_hor> <size_ver> <depth>
        data = line.split()

        size_hor = int(data[3])
        size_ver = int(data[4])

        current_volume = size_hor * size_ver

        self.video_data.current_volume = current_volume

        self.video_data.set_current_partition(size_hor, size_ver)

    def save_data(self):
        with open("trace_reader_output.txt", 'w') as output_file:
            output_file.write(self.video_data.return_string())

        self.video_data.clear()
        self.first_line = True


def main():
    data_reader = DataReader(TRACE_PATH)
    data_reader.read_data(VIDEO_NAME, ENCODER, CFG)
    data_reader.save_data()


if __name__ == "__main__":
    main()
