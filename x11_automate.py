from subprocess import Popen, PIPE
import PIL.Image  # python-imaging
import PIL.ImageStat  # python-imaging
import Xlib.display  # python-xlib
import re
import tesserocr

class Window:
    def __init__(self, wid):
        assert type(wid) == int
        self.wid = wid
        self.geometry = self.get_geometry()

    def get_wid(self):
        return self.wid

    def get_pid(self):
        c = "getwindowpid %d" % self.wid
        return int(run_command(c))

    def get_name(self):
        c = "getwindowname %d" % self.wid
        return run_command(c)

    def get_geometry(self):
        # TODO: should be parsed into Python objects
        c = "getwindowgeometry %d" % self.wid
        result = run_command(c)
        ret = re.findall(
            r"Position: (\d+?),(\d+).+\n.+Geometry: (\d+?)x(\d+)",
            result.decode('utf-8'))
        return dict(x=int(ret[0][0]), y=int(ret[0][1]),
                    w=int(ret[0][2]), h=int(ret[0][3]))

    def set_size(self, width, height):
        c = "windowsize %d %d %d" % (self.wid, width, height)
        return run_command(c)

    def move(self, x, y):
        c = "windowmove %d %d %d" % (self.wid, x, y)
        return run_command(c)

    def activate(self):
        c = "windowactivate %d" % self.wid
        return run_command(c)

    def focus(self):
        c = "windowfocus %d" % self.wid
        return run_command(c)

    def screen_map(self):
        c = "windowmap %d" % self.wid
        return run_command(c)

    def minimize(self):
        c = "windowminimize %d" % self.wid
        return run_command(c)

    def kill(self):
        c = "windowkill %d" % self.wid
        return run_command(c)

    def key(self, keyname):
        c = "key --window %d %s" % (self.wid, keyname)
        return run_command(c)

    # Lifted from http://rosettacode.org/wiki/Color_of_a_screen_pixel
    def get_pixel_color(self, i_x, i_y):
        self.geometry = self.get_geometry()
        i_x = self.geometry['x'] + i_x
        i_y = self.geometry['y'] + i_y
        o_x_root = Xlib.display.Display().screen().root
        o_x_image = o_x_root.get_image(
            i_x, i_y, 1, 1, Xlib.X.ZPixmap, 0xffffffff)
        o_pil_image_rgb = PIL.Image.frombytes(
            "RGB", (1, 1), o_x_image.data, "raw", "BGRX")
        lf_colour = PIL.ImageStat.Stat(o_pil_image_rgb).mean
        return tuple(map(int, lf_colour))

    def get_window_image(self):
        self.geometry = self.get_geometry()
        o_x_root = Xlib.display.Display().screen().root
        o_x_image = o_x_root.get_image(
            self.geometry['x'], self.geometry['y'],
            self.geometry['w'], self.geometry['h'],
            Xlib.X.ZPixmap, 0xffffffff)
        return o_x_image

    def get_window_area_image(self, area):
        self.geometry = self.get_geometry()
        o_x_root = Xlib.display.Display().screen().root
        o_x_image = o_x_root.get_image(
            self.geometry['x'] + area['x'], self.geometry['y'] + area['y'],
            area['w'], area['h'],
            Xlib.X.ZPixmap, 0xffffffff)
        return o_x_image

    def check_multi_color(self, point_list, color_list, delta):
        image = self.get_window_image()
        return check_multi_color_of_image(image, point_list, color_list,
                                          (0, 0), delta)

    def find_multi_color(self, point_list, color_list, offset, delta):
        image = self.get_window_image()
        for x_offset in range(0, offset):
            for y_offset in range(0, offset):
                if check_multi_color_of_image(image, point_list, color_list,
                                              (x_offset, y_offset), delta):
                    return True
        for x_offset in range(-1, -offset, -1):
            for y_offset in range(-1, -offset, -1):
                if check_multi_color_of_image(image, point_list, color_list,
                                              (x_offset, y_offset), delta):
                    return True
        return False

    def find_area_text(self, area):
        image = self.get_window_area_image(area)
        o_pil_image_rgb = PIL.Image.frombytes(
                "RGB", (area['w'], area['h']), image.data, "raw", "BGRX")
        text = tesserocr.image_to_text(o_pil_image_rgb)
        return text.strip()


# Lifted from http://rosettacode.org/wiki/Color_of_a_screen_pixel
def get_pixel_color(i_x, i_y):
    o_x_root = Xlib.display.Display().screen().root
    o_x_image = o_x_root.get_image(i_x, i_y, 1, 1, Xlib.X.ZPixmap, 0xffffffff)
    o_pil_image_rgb = PIL.Image.frombytes(
        "RGB", (1, 1), o_x_image.data, "raw", "BGRX")
    return o_pil_image_rgb.getpixel((0, 0))


def get_pixel_color_of_image(o_x_image, i_x, i_y):
    if i_x < 0:
        return (-1000, -1000, -1000)
    if i_y < 0:
        return (-1000, -1000, -1000)
    o_pil_image_rgb = PIL.Image.frombytes(
        "RGB", (i_x + 1, i_y + 1), o_x_image.data, "raw", "BGRX")
    return o_pil_image_rgb.getpixel((i_x, i_y))


def check_multi_color_of_image(image, point_list, color_list, offset, delta):
    for i, p in enumerate(point_list):
        c = get_pixel_color_of_image(image, p[0] + offset[0], p[1] + offset[1])
        if(abs(c[0] - color_list[i][0]) > delta
           or abs(c[1] - color_list[i][1]) > delta
           or abs(c[2] - color_list[i][2]) > delta):
            return False
    return True


def get_focused_window():
    c = "getactivewindow"
    wid = int(run_command(c))
    return Window(wid)


def get_active_window():
    c = "getactivewindow"
    wid = int(run_command(c))
    return Window(wid)


def get_windows(wids):
    windows = []
    for wid in wids:
        windows.append(Window(wid))
    return windows


def search(**kwargs):
    c = "search"
    noargs = ["onlyvisible", "class", "classname", "all", "any", "sync"]
    for arg in noargs:
        if arg in kwargs:
            if kwargs[arg]:
                c += " --%s" % arg
    if "name" in kwargs:
        c += ' --name "%s"' % kwargs['name']
    if "pid" in kwargs:
        c += " --pid %s" % kwargs['pid']
    str_wids = run_command(c).split()
    wids = []
    for str_wid in str_wids:
        wids.append(int(str_wid))
    return get_windows(wids)


def mouse_move(x, y):
    c = "mousemove %d %d" % (x, y)
    return run_command(c)


def type_string(string):
    c = "type '%s'" % string
    return run_command(c)


def key(keyname):
    c = "key %s" % keyname
    return run_command(c)


def click(btn):
    c = "click %d" % btn
    return run_command(c)


def click_at(x, y, btn=1):
    mouse_move(x, y)
    return click(btn)


def run_command(c):
    return run_command_raw("xdotool " + c)


def run_command_raw(c):
    return Popen(c, stdout=PIPE, shell=True).stdout.read()
