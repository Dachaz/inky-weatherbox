class MockDisplay:
    WHITE = '#ffffff'
    BLACK = '#000000'
    RED = '#ff0000'

    def __init__(self, model="v1") -> None:
        if model == "v2":
            self.WIDTH = 250
            self.HEIGHT = 122
        else:
            self.WIDTH = 212
            self.HEIGHT = 104

    def set_image(self, image):
        self.image = image

    def show(self):
        self.image.save('inky.png')
