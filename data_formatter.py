import numpy as np
import seaborn as sn
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages

from video_data import MODULES, BLOCK_SIZES

font = fm.FontProperties(size=5.7)
FILE_PATH = "trace_1080.txt"

MATRIX_INDEX = {
    '128': 0,
    '64': 1,
    '32': 2,
    '24': 3,
    '16': 4,
    '12': 5,
    '8': 6,
    '4': 7
}


class DataFormatter(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.volume = {}
        self.loads_stores = {}
        self.block_size_info = {}
        self.total_blocks = {}

    def get_trace_data(self):
        with open(self.file_path) as file:
            # Pula o header
            next(file)

            for line in file:
                # HEVC;Low Delay;BQSquare;416x240;64;22182858;2575891968;
                data = line.split(';')
                self.volume.setdefault(data[2], {})

                self.volume[data[2]].setdefault(data[1], {})
                self.volume[data[2]][data[1]].setdefault(data[0], [])

                self.volume[data[2]][data[1]][data[0]].append(float(data[7]))

    @staticmethod
    def get_title(config, title):
        return title + " - " + config

    def generate_trace_graph(self, volume, title, sr):
        x = np.arange(len(sr))  # localização dos rotulos
        width = 0.35  # largura das barras

        fig, ax = plt.subplots()
        rects1 = ax.bar(x - width / 2, volume["HEVC"], width, label='HEVC')
        rects2 = ax.bar(x + width / 2, volume["VVC"], width, label='VVC')

        ax.set_xlabel('Search Range')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(sr)
        ax.legend(loc=2, fontsize=9)

        ax.set_ylabel("Volume in GB")

        self.auto_label(rects1, ax)
        self.auto_label(rects2, ax)

        fig.tight_layout()

        # plt.show()
        return fig

    def get_vtune_data(self):
        with open(self.file_path) as file:
            # Pula o header
            next(file)

            for line in file:
                data = line.split(';')

                self.loads_stores.setdefault(data[2], {})
                video_modules = self.loads_stores[data[2]]

                for i in range(MODULES.__len__()):
                    video_modules.setdefault(MODULES[i], {"Loads": 0,
                                                          "Stores": 0})
                    video_modules[MODULES[i]][data[5]] = data[i+6]

    @staticmethod
    def generate_vtune_graph(video_dict, video):
        number_bars = MODULES.__len__()

        loads = []
        stores = []
        for module in video_dict:
            module = video_dict[module]
            loads.append(int(module["Loads"]))
            stores.append(int(module["Stores"]))

        memory_access_total = sum(loads) + sum(stores)

        loads = tuple(map(lambda x: (x / memory_access_total) * 100, tuple(loads)))
        stores = tuple(map(lambda x: (x / memory_access_total) * 100, tuple(stores)))

        ind = np.arange(number_bars)

        width = 0.8

        load_plot = plt.bar(ind, loads, width)
        store_plot = plt.bar(ind, stores, width, bottom=loads)

        plt.xlabel('Encoder Modules')
        plt.ylabel('Percentages')
        plt.title(f"Memory Access(Loads and Stores) - { video }")
        plt.xticks(ind, MODULES, fontproperties=font, multialignment='center')
        # plt.yticks(np.arange(0, 100, 10))
        plt.legend((load_plot[0], store_plot[0]), ('Loads', 'Stores'))

        plt.show()

    def generate_matrix(self):
        block_size_dict = {}
        total_dict = {}

        with open(self.file_path) as file:
            # Pula o header
            next(file)

            for line in file:
                data = line.split(';')

                title = data[2]
                encoder = data[0]
                cfg = data[1]

                block_size_dict.setdefault(title, {})
                block_size_dict[title].setdefault(encoder, {})
                block_size_dict[title][encoder].setdefault(cfg, np.zeros((8, 8)))

                matrix = block_size_dict[title][encoder][cfg]

                total_dict.setdefault(title, {})
                total_dict[title].setdefault(encoder, {})
                total_dict[title][encoder].setdefault(cfg, 0)

                data_index = 8
                for block in BLOCK_SIZES:
                    hor_size, ver_size = block.split('x')
                    block_counter = int(data[data_index])

                    index = MATRIX_INDEX[hor_size]
                    column = MATRIX_INDEX[ver_size]

                    matrix[index][column] += block_counter
                    total_dict[title][encoder][cfg] += block_counter
                    data_index += 1

                block_size_dict[title][encoder][cfg] = matrix

        self.total_blocks = total_dict
        self.block_size_info = block_size_dict

    @staticmethod
    def generate_block_graph(title, encoder, cfg, matrix):
        df_cm = pd.DataFrame(matrix, index=[i for i in MATRIX_INDEX],
                             columns=[i for i in MATRIX_INDEX])

        fig, ax = plt.subplots()

        heat_map = sn.heatmap(df_cm, annot=True, fmt='.2f')

        bottom, top = heat_map.get_ylim()
        heat_map.set_ylim(bottom + 0.5, top - 0.5)

        ax.set_title(f'Inter access per CU Size - { title } - { encoder } - { cfg }')
        ax.set_ylabel('Vertical Dimension')
        ax.set_xlabel('Horizontal Dimension')

        fig.tight_layout()

        return fig

    @staticmethod
    def auto_label(rects, ax):
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 0),
                        textcoords="offset points",
                        ha='center', va='bottom')


def generate_trace_graph(path):
    from automate_read import SEARCH_RANGE
    data_formatter = DataFormatter(path)
    data_formatter.get_trace_data()

    figs = []
    for title, video_data in data_formatter.volume.items():
        for cfg, volume in video_data.items():
            graph_title = data_formatter.get_title(title, cfg)
            figs.append(data_formatter.generate_trace_graph(volume, graph_title, SEARCH_RANGE))

    with PdfPages('trace_graphs.pdf') as pdf:
        for fig in figs:
            pdf.savefig(fig)


def generate_vtune_graph(path):
    data_formatter = DataFormatter(path)
    data_formatter.get_vtune_data()

    for video, data in data_formatter.loads_stores.items():
        data_formatter.generate_vtune_graph(data, video)


def generate_block_graph(path):
    data_formatter = DataFormatter(path)
    data_formatter.generate_matrix()

    figs = []
    for title, encoder_dict in data_formatter.block_size_info.items():
        for encoder, cfg_dict in encoder_dict.items():
            for cfg, matrix in cfg_dict.items():
                total = data_formatter.total_blocks[title][encoder][cfg]

                # Converte o valor para porcentagens
                for i in range(8):
                    matrix[i] = list(map(lambda x: (x / total) * 100, matrix[i]))

                figs.append(data_formatter.generate_block_graph(title, encoder, cfg, matrix))

    with PdfPages('block_size_graphs.pdf') as pdf:
        for fig in figs:
            pdf.savefig(fig)


if __name__ == "__main__":
    # generate_trace_graph(FILE_PATH)
    # generate_vtune_graph("vtune_output.txt")
    generate_block_graph(FILE_PATH)
