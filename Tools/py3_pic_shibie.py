# -*- coding: utf-8 -*-
import pytesseract
from PIL import Image, ImageEnhance

def initTable(threshold=170):       # 二值化函数
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)

    return table

def pic_to_str(im):
    im=im.crop((2,2,62,18))
    im = im.convert('L')  # 2.将彩色图像转化为灰度图
    binaryImage = im.point(initTable(threshold=110), '1')
    binaryImage.save('111.png')
    auth = pytesseract.image_to_string(im,lang="chi_sim",  config="-psm 7 digits7").replace(' ', '')
    return auth
    diction = {'壹': 1, '贰': 2, '叁': 3, '肆': 4, '鏖': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '扭': '', '玖': 9,
               '玫': 9, '砍': 9, '拾': 10, '零': 0, '+': '+', 'x': '*', '×': '*', '_': '-', ',': '-',
               '^': '-', '`': '-', '一': '-', '-': '-', '~': '-'}
    x = ''
    try:
        for s in auth[0:3]:
            if s in diction.keys():
                x += str(diction[s])
            else:
                x += '-'  # 减号识别率较低,未识别的字符都视为减号
        return eval(x)
    except:
        print('The captcha is not recognized')
        x = ''
        return x


class code_two_pixel_line():
    def __init__(self):
        self.im = Image.open("222.png")
        self.pix = self.im.load()
        self.width = self.im.size[0]
        self.height = self.im.size[1]

    #四边去燥
    def remove_ridge(self):
        for x in range(self.width):
            self.im.putpixel((x, 0), (255, 255, 255))
            self.im.putpixel((x, self.im.size[1]-1), (255, 255, 255))
        for y in range(self.height):
            self.im.putpixel((0, y), (255, 255, 255))
            self.im.putpixel((self.im.size[0]-1, y), (255, 255, 255))
        # self.im.save('ceshi4.gif')



    #去除孤点
    def remove_pi(self):
        self.remove_ridge()
        while 1:
            remove_point=0
            for x in range(1,self.width-1):
                for y in range(1,self.height-1):
                    r, g, b = self.pix[x , y]
                    if r == 255 and g == 255 and b == 255:
                        continue
                    count=0
                    r, g, b = self.pix[x+1, y]
                    if r==255 and g==255 and b==255:
                        count+=1
                    r, g, b = self.pix[x - 1, y]
                    if r == 255 and g == 255 and b == 255:
                        count += 1
                    r, g, b = self.pix[x , y+1]
                    if r == 255 and g == 255 and b == 255:
                        count += 1
                    r, g, b = self.pix[x, y - 1]
                    if r == 255 and g == 255 and b == 255:
                        count += 1
                    if count>=3:
                        self.im.putpixel((x, y), (255, 255, 255))
                        remove_point+=1
            if remove_point==0:
                break
            else:
                print(remove_point)
        self.im.save('ceshi.png')


def jl_set(im):
    im = im.crop((51, 10, 155, 50))
    im = im.convert('L')  # 2.将彩色图像转化为灰度图
    im = im.point(initTable(), '1')
    im.save('222.png')
    pix = im.load()
    width = im.size[0]
    height = im.size[1]
    for x in range(1, width - 2):
        for y in range(2, height-1):
            ys = pix[x, y]
            if not ys:
                ys = pix[x + 2, y]
                if not ys:
                    if not pix[x + 1, y-1] or not pix[x + 1, y+1]:
                        im.putpixel((x + 1, y), 0)
    for x in range(1, width):
        for y in range(1, height - 4):
            ys = pix[x, y]
            if ys:
                ys = pix[x, y + 4]
                if ys:
                    im.putpixel((x, y + 1), 1)
                    im.putpixel((x, y + 2), 1)
                    im.putpixel((x, y + 3), 1)
    auth = pytesseract.image_to_string(im, lang="chi_sim", config="-psm 7 digits3").replace(' ', '')
    return auth


def bj_set(im):
    im=im.crop((51,10,165,50))
    im = im.convert('L')  # 2.将彩色图像转化为灰度图
    im = im.point(initTable(), '1')
    pix = im.load()
    width = im.size[0]
    height = im.size[1]
    for x in range(1, width):
        for y in range(1, height-4):
            ys = pix[x, y]
            if ys:
                ys = pix[x, y+4]
                if ys:
                    im.putpixel((x, y+1), 1)
                    im.putpixel((x, y +2), 1)
                    im.putpixel((x, y + 3), 1)
    for x in range(1, width-2):
        for y in range(1, height):
            ys = pix[x, y]
            if not ys:
                ys = pix[x+2, y]
                if not ys:
                    im.putpixel((x+1, y), 0)



    auth = pytesseract.image_to_string(im, lang="chi_sim", config="-psm 7 digits2").replace(' ', '')
    return auth




if __name__=="__main__":
    a = Image.open('./1108.png')
    # b=bj_set(a)
    c = pic_to_str(a)
    # width = a.size[0]
    # height = a.size[1]
    a1 = a.crop((0, 0, 50, 70))
    a1.save('a1.png')
    a2 = a.crop((50, 0, 82, 70))
    a2.save('a2.png')
    a3 = a.crop((82, 0, 117, 70))
    a3.save('a3.png')
    a4 = a.crop((117, 0, 160, 70))
    a4.save('a4.png')
    a11=pic_to_str(a1)
    a22 = pic_to_str(a2)
    a33 = pic_to_str(a3)
    a44 = pic_to_str(a4)
    c=pic_to_str(a)
    b=jl_set(a)
    print(b)
    # a=code_two_pixel_line()
    # a.remove_pi()
    # a=Image.open('../download/yzm.jpg')
    # a = Image.open('./ceshi.png')
    # b=pic_to_str(a)
    print(b)
