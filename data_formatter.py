import matplotlib.pyplot as plt
import numpy as np
from automate_read import SEARCH_RANGE
from matplotlib.backends.backend_pdf import PdfPages

FILE_PATH = "automate_read_output.txt"


class DataFormatter(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.volume = {}

    def get_data(self):
        first_line = True

        with open(self.file_path) as file:
            for line in file:
                if first_line:
                    first_line = False
                    continue

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
    def generate_graph(volume, title):
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


def auto_label(rects, ax):
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 0),
                    textcoords="offset points",
                    ha='center', va='bottom')


def generate_graph(path):
    data_formatter = DataFormatter(path)
    data_formatter.get_data()

    figs = []
    for title, video_data in data_formatter.volume.items():
        for cfg, volume in video_data.items():
            graph_title = data_formatter.get_title(title, cfg)
            figs.append(data_formatter.generate_graph(volume, graph_title))

    with PdfPages('graphs.pdf') as pdf:
        for fig in figs:
            pdf.savefig(fig)


if __name__ == "__main__":
    generate_graph(FILE_PATH)

