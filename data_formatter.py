import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages
from video_data import MODULES

font = fm.FontProperties(size=5.7)
FILE_PATH = "automate_read_output.txt"


class DataFormatter(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.volume = {}
        self.loads_stores = {}

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

    @staticmethod
    def generate_trace_graph(volume, title):
        x = np.arange(len(SEARCH_RANGE))  # localização dos rotulos
        width = 0.35  # largura das barras

        fig, ax = plt.subplots()
        rects1 = ax.bar(x - width / 2, volume["HEVC"], width, label='HEVC')
        rects2 = ax.bar(x + width / 2, volume["VVC"], width, label='VVC')

        ax.set_xlabel('Search Range')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(SEARCH_RANGE)
        ax.legend(loc=2, fontsize=9)

        ax.set_ylabel("Volume in GB")

        auto_label(rects1, ax)
        auto_label(rects2, ax)

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


def auto_label(rects, ax):
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 0),
                    textcoords="offset points",
                    ha='center', va='bottom')


def generate_trace_graph(path):
    data_formatter = DataFormatter(path)
    data_formatter.get_trace_data()

    figs = []
    for title, video_data in data_formatter.volume.items():
        for cfg, volume in video_data.items():
            graph_title = data_formatter.get_title(title, cfg)
            figs.append(data_formatter.generate_trace_graph(volume, graph_title))

    with PdfPages('graphs.pdf') as pdf:
        for fig in figs:
            pdf.savefig(fig)


def generate_vtune_graph(path):
    data_formatter = DataFormatter(path)
    data_formatter.get_vtune_data()

    for video, data in data_formatter.loads_stores.items():
        data_formatter.generate_vtune_graph(data, video)


if __name__ == "__main__":
    from automate_read import SEARCH_RANGE
    # generate_trace_graph(FILE_PATH)
    generate_vtune_graph("vtune_output.txt")


