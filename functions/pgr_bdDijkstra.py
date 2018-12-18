from .DijkstraBase import DijkstraBase

class Function(DijkstraBase):

    minPGRversion = 2.5

    @classmethod
    def getName(self):
        ''' returns Function name. '''
        return 'pgr_bdDijkstra'

    def __init__(self, ui):
        DijkstraBase.__init__(self, ui)
