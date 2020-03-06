# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys

import subprocess
from PIL import Image
from io import BytesIO
from urllib2 import urlopen

WORK_DIR = os.path.dirname(__file__)

UNIT_MAPS = {
    1: 'KB',
    2: 'MB',
    3: 'GB',
    4: 'TB'
}

OS_MAPS = {
    'linux2': 'linux',
    'win32': 'windows',
    'darwin': 'mac'
}

TOOL_MAPS = {
    'png': 'pngquant',
    'jpg': 'jpegoptim'
}


def convert_unit(num, count=0):
    count += 1
    num /= 1024.0
    if num < 1024:
        return '%2.2f%s' % (num, UNIT_MAPS.get(count, 'TB'))
    return convert_unit(num, count)


class CompressUtil(object):
    def __init__(self, input, format):
        format = format.lower()
        self.io = input
        if format not in ['jpeg', 'jpg', 'png']:
            raise TypeError('only accept jpeg, jpg, png')
        self.format = format if format == 'png' else 'jpg'

    def get_png_command_line(self, quality_min=50, quality_max=50):
        if OS_MAPS.get(sys.platform) == 'linux':
            tool_path = 'pngquant'  # linux下安装pngquant: yum install pngquant
        else:
            tool_path = '{0}/tools/{1}/{2}/{3}'.format(WORK_DIR, self.format, OS_MAPS.get(sys.platform),
                                                       TOOL_MAPS.get(self.format))
        command = '{0} --skip-if-larger -v -f --quality={1}-{2} - -o -'.format(tool_path, quality_min, quality_max)
        return command

    def get_jpg_command_line(self, quality=100, size=50):
        if OS_MAPS.get(sys.platform) == 'linux':
            # linux下安装jpegoptim: yum install jpegoptim   mac下安装jpegoptim: brew install jpegoptim
            tool_path = 'jpegoptim'
        else:
            tool_path = '{0}/tools/{1}/{2}/{3}'.format(WORK_DIR, self.format, OS_MAPS.get(sys.platform),
                                                       TOOL_MAPS.get(self.format))
        command = '{0} -m{1} -S{2}% -v -q --stdin --stdout'.format(tool_path, quality, size)
        return command

    def execute_command(self, compress_factor=None):
        if self.format == 'png':
            if compress_factor:
                command_line = self.get_png_command_line(quality_min=compress_factor, quality_max=compress_factor)
            else:
                command_line = self.get_png_command_line()
        else:
            if compress_factor:
                command_line = self.get_jpg_command_line(size=compress_factor)
            else:
                command_line = self.get_jpg_command_line()

        args = command_line.split(' ')
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, errout = p.communicate(input=self.io.getvalue())
        code = p.poll()
        if code:
            raise subprocess.CalledProcessError(code, args)
        return BytesIO(stdout)


class TinyImage(object):
    def __init__(self, img_path=None, img_url=None, img_buff=None):
        self.img_path = img_path
        self.img_url = img_url
        self.img_buff = img_buff

        if not any([self.img_path, self.img_url, self.img_buff]):
            raise TypeError('only support img_path, img_url and img_buff.')

        if not self.img_buff:
            if self.img_url:
                r = urlopen(img_url)
                self.img_buff = BytesIO(r.read())
            else:
                if self.img_path:
                    with open(self.img_path, 'rb') as f:
                        self.img_buff = BytesIO(f.read())

        self.im = Image.open(self.img_buff)
        self.img_buff.seek(0)
        im_format = self.im.format.lower()
        if im_format not in ['png', 'jpeg']:
            raise TypeError('this util only support jpg, jpeg and png.')

    @classmethod
    def from_url(cls, img_url):
        return cls(img_url=img_url)

    @property
    def format(self):
        return self.im.format

    @property
    def content_type(self):
        return 'image/{0}'.format(self.im.format.lower())

    @property
    def ext(self):
        im_format = self.im.format.lower()
        return 'jpg' if im_format == 'jpeg' else im_format

    @property
    def size(self):
        return self.im.size

    @property
    def width(self):
        return self.im.width

    @property
    def height(self):
        return self.im.height

    @property
    def mode(self):
        return self.im.mode

    @property
    def file_size(self):
        self.img_buff.seek(0, 2)
        x = self.img_buff.tell()
        self.img_buff.seek(0)
        return convert_unit(x)

    def compress(self, compress_factor=None):
        # compress_factor 压缩因子:
        # 对于png来说就是压缩后的图片的quality， 例如：50， 百分之50的quality, pngquant 里的参数
        # 对于jpg来说就是压缩后的图片的size， 例如：50， 百分之50的size，jpegOptim 里的参数
        cu = CompressUtil(self.img_buff, self.format)
        io = cu.execute_command(compress_factor)
        return self.__class__(img_buff=io)

    def save(self, image_path):
        dirname = os.path.dirname(image_path)
        if dirname:
            if not os.path.exists(dirname):
                try:
                    os.makedirs(dirname)
                except Exception as ex:
                    raise Exception('creating directory {0} failed.'.format(dirname))
        try:
            with open(image_path, 'wb') as f:
                f.write(self.img_buff.getvalue())
                self.img_buff.seek(0)
        except Exception as ex:
            raise Exception('save image {0} failed.'.format(image_path))


if __name__ == '__main__':
    ti = TinyImage(os.path.join(WORK_DIR, 'output', 'input.png'))
    print ti.size, ti.file_size, ti.format, ti.mode, ti.content_type
    new = ti.compress()
    print new.size, new.file_size, new.format, new.mode, new.content_type
    new.save(os.path.join(WORK_DIR, 'output', 'output.png'))

    # ti = TinyImage(os.path.join(WORK_DIR, 'output', 'input.jpg'))
    ti = TinyImage.from_url('http://cdn.17zuoye.com/fs-resource/5a616411b1e48a7551661c79.jpg')
    print ti.size, ti.file_size, ti.format, ti.mode, ti.content_type
    new = ti.compress()
    print new.size, new.file_size, new.format, new.mode, new.content_type
    new.save(os.path.join(WORK_DIR, 'output', 'output.jpg'))