class VideoData(object):
    def __init__(self):
        self.title = ""
        self.resolution = []
        self.search_range = 0
        self.candidate_blocks = 0
        self.data_volume = 0

    def set_title(self, title):
        self.title = title

    def set_resolution(self, x, y):
        self.resolution.append(x)
        self.resolution.append(y)

    def set_search_range(self, search_range):
        self.search_range = search_range

    def increment_candidate_blocks(self, blocks):
        self.candidate_blocks += blocks

    def increment_data_volume(self, volume):
        self.data_volume += volume

    def return_string(self):
        string = self.title + ";"
        string += self.resolution[0].__str__() + self.resolution[1].__str__() + ";"
        string += self.search_range.__str__() + ";"
        string += self.candidate_blocks.__str__() + ";"
        string += self.data_volume.__str__()

        return string


