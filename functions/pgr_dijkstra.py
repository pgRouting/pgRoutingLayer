from .DijkstraBase import DijkstraBase


class Function(DijkstraBase):

    minPGRversion = 2.1

    def __init__(self, ui):
        DijkstraBase.__init__(self, ui)

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_dijkstra'
