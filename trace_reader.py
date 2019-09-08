# Numero de blocos acessados baseado na janela de busca
BLOCKS = {
    '16': 44,
    '32': 60,
    '64': 76,
    '96': 76,
    '128': 76
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


class VideoData(object):
    def __init__(self):
        self.title = ""
        self.resolution = []
        self.search_range = ""
        self.candidate_blocks = 0
        self.data_volume = 0
        self.cu_size = 0
        self.current_volume = 0

    def set_title(self, title):
        self.title = title

    def set_resolution(self, x, y):
        self.resolution.append(x)
        self.resolution.append(y)

    def set_search_range(self, search_range):
        self.search_range = search_range

    def set_cu_size(self, cu_size):
        self.cu_size = cu_size

    def increment_candidate_blocks(self, candidate_blocks):
        self.candidate_blocks += candidate_blocks

    def increment_data_volume(self, volume):
        self.data_volume += volume

    def return_string(self):
        string = self.title + ";"
        string += self.resolution[0].__str__() + 'x' + self.resolution[1].__str__() + ";"
        string += self.search_range + ";"
        string += int(self.candidate_blocks).__str__() + ";"
        string += int(self.data_volume).__str__()

        return string

    def clear(self):
        self.title = ""
        self.resolution = []
        self.search_range = ""
        self.candidate_blocks = 0
        self.data_volume = 0
        self.cu_size = 0


class DataReader(object):
    def __init__(self, input_path):
        self.input_path = input_path
        self.video_data = VideoData()
        self.first_line = True

    def read_data(self, video_title):
        self.video_data.set_title(video_title)

        input_file = open(self.input_path)

        for line in input_file:
            self.process_line(line)

        input_file.close()

    def process_line(self, line):
        # Pula a linha de inicio da codificação do quadro e da CTU
        if line.startswith('I') or line.startswith('L'):
            return

        elif line.startswith('U'):
            self.get_size(line)

        elif line.startswith('P'):
            self.process_pu(line)

        elif line.startswith('C'):
            self.process_block()

        elif line.startswith('F'):
            self.process_first_search()

        elif line.startswith('R'):
            self.process_rectangle(line)

        # A primeira linha contem as informações do video
        elif self.first_line:
            self.first_line = False
            self.set_info(line)

        else:
            return

    def get_size(self, line):
        # U <xCU> <yCU> <size>
        data = line.split()
        size = int(data[3])
        self.video_data.set_cu_size(size)

    def process_pu(self, line):
        # P <sizePU> <idPart> <ref_frame_id>
        data = line.split()
        pu = data[1]

        if int(pu) < 4:
            partition = PARTITION_PU[pu][0]
        else:
            id_part = int(data[2])
            partition = PARTITION_PU[pu][id_part] * self.video_data.cu_size

        volume = self.video_data.cu_size * partition

        self.video_data.current_volume = volume

    def process_block(self):
        # C <xCand> <yCand>
        self.video_data.increment_candidate_blocks(1)
        self.video_data.increment_data_volume(self.video_data.current_volume)

    def process_first_search(self):
        # F <xStart> <yStart>
        candidate_blocks = BLOCKS[self.video_data.search_range]
        self.video_data.increment_candidate_blocks(candidate_blocks)

        self.video_data.increment_data_volume(self.video_data.current_volume * candidate_blocks)

    def process_rectangle(self, line):
        # R < xL > < xR > < yT > < yB >
        data = line.split()

        x = int(data[2]) - int(data[1])
        y = int(data[4]) - int(data[3])

        volume = x*y

        self.video_data.increment_data_volume(volume)

        candidate_blocks = (int(self.video_data.search_range) * 2 / RASTER_SEARCH) * 2

        self.video_data.increment_candidate_blocks(candidate_blocks)

    def set_info(self, line):
        # <width> <height> <searchRange>
        data = line.split()

        self.video_data.set_resolution(data[0], data[1])
        self.video_data.set_search_range(data[2])

    def save_data(self):
        output_file = open("trace_reader_output.txt", 'w')
        output_file.write(self.video_data.return_string())

        output_file.close()

        self.video_data.clear()
        self.first_line = True


def main():
    data_reader = DataReader("../hm-videomem/mem_trace.txt")
    data_reader.read_data("PartyScene")
    data_reader.save_data()


if __name__ == "__main__":
    main()
