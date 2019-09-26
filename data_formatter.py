import matplotlib.pyplot as plt
import numpy as np


class DataFormatter(object):
    def __init__(self, file_path):
        self.file_path = file_path

    def generate_graph(self):
        search_range = ["64", "96", "128"]
        volume = {"HEVC": [],
                  "VVC": []}

        x = np.arange(len(search_range))  # localização dos rotulos
        width = 0.35  # largura das barras

        with open(self.file_path) as file:
            for line in file:
                # HEVC;Low Delay;BQSquare;416x240;64;22182858;2575891968;
                data = line.split(';')
                if data[1] == "Random Access":
                    volume[data[0]].append(data[5])

        fig, ax = plt.subplots()
        rects1 = ax.bar(x - width / 2, volume["HEVC"], width, label='HEVC')
        rects2 = ax.bar(x + width / 2, volume["VVC"], width, label='VVC')

        ax.set_xlabel('Search Range')
        ax.set_title('Random Access')
        ax.set_xticks(x)
        ax.set_xticklabels(search_range)
        ax.legend()

        auto_label(rects1, ax)
        auto_label(rects2, ax)

        fig.tight_layout()

        plt.show()


def auto_label(rects, ax):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')





