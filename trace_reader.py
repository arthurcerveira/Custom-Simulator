# Numero de blocos acessados baseado na janela de busca
blocks = {
    '16': 44,
    '32': 60,
    '64': 76,
    '96': 76,
    '128': 76
}

# Formato da partição
partition_pu = {
    '0': [1, 1],        # 2N X 2N
    '1': [0.5, 0.5],    # 2N X N
    '2': [0.5, 0.5],    # N X 2N
    '3': [0.25, 0.25],  # N X N
    '4': [0.25, 0.75],  # 2N x nU
    '5': [0.75, 0.25],  # 2N x nD
    '6': [0.25, 0.75],  # nL x 2N
    '7': [0.75, 0.25]   # nR x 2N
}


class VideoData(object):
    def __init__(self):
        self.title = ""
        self.resolution = []
        self.search_range = ""
        self.candidate_blocks = 0
        self.data_volume = 0
        self.cu_size = 0

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
        string += self.candidate_blocks.__str__() + ";"
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
    def __init__(self, file_name):
        self.input_file = open(file_name)
        self.output_file = open("output.txt", 'w')
        self.video_data = VideoData()

    def read_data(self):
        for line in self.input_file:
            self.process_line(line)

        self.save_data()

    def process_line(self, line):
        # Pula a linha de inicio da codificação do quadro e da CTU
        if line.startswith('I') or line.startswith('L'):
            return

        elif line.startswith('U'):
            self.get_size(line)

        elif line.startswith('P'):
            self.process_pu(line)

        elif line.startswith('C'):
            # C <xCand> <yCand>
            self.video_data.increment_candidate_blocks(1)

        elif line.startswith('F'):
            self.process_first_search()

        elif line.startswith('R'):
            self.process_retangle(line)

        # Senao se enquadrar em nenhum dos casos, é a linha do título
        else:
            self.set_info(line)

    def get_size(self, line):
        # U <xCU> <yCU> <size>
        data = line.split()
        size = int(data[3])
        self.video_data.set_cu_size(size)

    def process_pu(self, line):
        # P <sizePU> <idPart> <ref_frame_id>
        data = line.split()
        pu = data[1]
        id_part = int(data[2])
        partition = partition_pu[pu][id_part] * self.video_data.cu_size
        volume = self.video_data.cu_size * partition

        self.video_data.increment_data_volume(volume)

    def process_first_search(self):
        # F <xStart> <yStart>
        candidate_blocks = blocks[self.video_data.search_range]
        self.video_data.increment_candidate_blocks(candidate_blocks)

    def process_retangle(self, line):
        # R < xL > < xR > < yT > < yB >
        data = line.split()

        x = int(data[2]) - int(data[1])
        y = int(data[4]) - int(data[3])

        volume = x*y

        self.video_data.increment_data_volume(volume)

        # TODO
        # Incrementar o numero de blocos

    def set_info(self, line):
        # <videoName> <width> <height> <searchRange>
        data = line.split()

        self.video_data.set_title(data[0])
        self.video_data.set_resolution(data[1], data[2])
        self.video_data.set_search_range(data[3])

    def save_data(self):
        self.output_file.write(self.video_data.return_string())

        self.output_file.close()
        self.input_file.close()


def main():
    data_reader = DataReader("mem_trace.txt")
    data_reader.read_data()


if __name__ == "__main__":
    main()
