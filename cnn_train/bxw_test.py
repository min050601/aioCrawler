#coding=utf-8
import numpy as np
import tensorflow as tf
import os
import random
from PIL import Image
from io import BytesIO

number = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
            'v', 'w', 'x', 'y', 'z']

ALPHABET = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
            'V', 'W', 'X', 'Y', 'Z']
# 文本转向量
char_set = number + alphabet +ALPHABET+ ['_']  # 如果验证码长度小于4, '_'用来补齐
CHAR_SET_LEN = len(char_set)
IMAGE_HEIGHT = 60
IMAGE_WIDTH = 60
MAX_CAPTCHA = 1

X = tf.placeholder(tf.float32, [None, IMAGE_HEIGHT * IMAGE_WIDTH])
Y = tf.placeholder(tf.float32, [None, MAX_CAPTCHA * CHAR_SET_LEN])
keep_prob = tf.placeholder(tf.float32)  # dropout

# 定义CNN
def crack_captcha_cnn(w_alpha=0.01, b_alpha=0.1):

    x = tf.reshape(X, shape=[-1, IMAGE_HEIGHT, IMAGE_WIDTH, 1])

    # w_c1_alpha = np.sqrt(2.0/(IMAGE_HEIGHT*IMAGE_WIDTH)) #
    # w_c2_alpha = np.sqrt(2.0/(3*3*32))
    # w_c3_alpha = np.sqrt(2.0/(3*3*64))
    # w_d1_alpha = np.sqrt(2.0/(8*32*64))
    # out_alpha = np.sqrt(2.0/1024)

    # 3 conv layer
    w_c1 = tf.Variable(w_alpha * tf.random_normal([3, 3, 1, 32]))
    b_c1 = tf.Variable(b_alpha * tf.random_normal([32]))
    conv1 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(x, w_c1, strides=[1, 1, 1, 1], padding='SAME'), b_c1))
    conv1 = tf.nn.max_pool(conv1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    conv1 = tf.nn.dropout(conv1, keep_prob)

    w_c2 = tf.Variable(w_alpha * tf.random_normal([3, 3, 32, 64]))
    b_c2 = tf.Variable(b_alpha * tf.random_normal([64]))
    conv2 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv1, w_c2, strides=[1, 1, 1, 1], padding='SAME'), b_c2))
    conv2 = tf.nn.max_pool(conv2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    conv2 = tf.nn.dropout(conv2, keep_prob)

    w_c3 = tf.Variable(w_alpha * tf.random_normal([3, 3, 64, 64]))
    b_c3 = tf.Variable(b_alpha * tf.random_normal([64]))
    conv3 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv2, w_c3, strides=[1, 1, 1, 1], padding='SAME'), b_c3))
    conv3 = tf.nn.max_pool(conv3, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    conv3 = tf.nn.dropout(conv3, keep_prob)

    # Fully connected layer
    w_d = tf.Variable(w_alpha * tf.random_normal([8 * 8 * 64, 1024]))
    b_d = tf.Variable(b_alpha * tf.random_normal([1024]))
    dense = tf.reshape(conv3, [-1, w_d.get_shape().as_list()[0]])
    dense = tf.nn.relu(tf.add(tf.matmul(dense, w_d), b_d))
    dense = tf.nn.dropout(dense, keep_prob)

    w_out = tf.Variable(w_alpha * tf.random_normal([1024, MAX_CAPTCHA * CHAR_SET_LEN]))
    b_out = tf.Variable(b_alpha * tf.random_normal([MAX_CAPTCHA * CHAR_SET_LEN]))
    out = tf.add(tf.matmul(dense, w_out), b_out)
    # out = tf.nn.softmax(out)
    return out

# 把彩色图像转为灰度图像（色彩对识别验证码没有什么用）
def convert2gray(img):
    if len(img.shape) > 2:
        gray = np.mean(img, -1)
        # 上面的转法较快，正规转法如下
        # r, g, b = img[:,:,0], img[:,:,1], img[:,:,2]
        # gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
        return gray
    else:
        return img

# 向量转回文本
def vec2text(vec):
    char_pos = vec.nonzero()[0]
    text = []
    for i, c in enumerate(char_pos):
        char_at_pos = i  # c/63
        char_idx = c % CHAR_SET_LEN
        if char_idx < 10:
            char_code = char_idx + ord('0')
        elif char_idx < 36:
            char_code = char_idx - 10 + ord('A')
        elif char_idx < 62:
            char_code = char_idx - 36 + ord('a')
        elif char_idx == 62:
            char_code = ord('-')
        else:
            raise ValueError('error')
        text.append(chr(char_code))
    return "".join(text)


class Check_Cnn():
    def __init__(self):
        self.output = crack_captcha_cnn()
        self.saver = tf.train.Saver()
        self.sess = tf.Session()
        self.saver.restore(self.sess, tf.train.latest_checkpoint('/root/wander/bxw_models'))

    def get_code(self,image_content):
        img = Image.open(BytesIO(image_content))
        im1 = img.crop((5, 5, 45, 45))
        code1=self.img_to_code(im1)
        im2 = img.crop((55, 5, 95, 45))
        code2 = self.img_to_code(im2)
        im3 = img.crop((105, 5, 145, 45))
        code3 = self.img_to_code(im3)
        im4 = img.crop((5, 55, 45, 95))
        code4 = self.img_to_code(im4)
        im5 = img.crop((55, 55, 95, 95))
        code5 = self.img_to_code(im5)
        im6 = img.crop((105, 55, 145, 95))
        code6 = self.img_to_code(im6)
        im7 = img.crop((5, 105, 45, 145))
        code7 = self.img_to_code(im7)
        im8 = img.crop((55, 105, 95, 145))
        code8 = self.img_to_code(im8)
        im9 = img.crop((105, 105, 145, 145))
        code9 = self.img_to_code(im9)
        return {code1:'23,22',
                code2:'74,26',
                code3:'123,28',
                code4:'25,71',
                code5: '74,77',
                code6: '122,78',
                code7: '25,129',
                code8: '77,127',
                code9: '124,124'}

    def img_to_code(self,image):
        image = image.resize((60, 60), Image.ANTIALIAS).convert('L')
        image = np.array(image)
        image = convert2gray(image)
        image = image.flatten() / 255
        predict = tf.argmax(tf.reshape(self.output, [-1, MAX_CAPTCHA, CHAR_SET_LEN]), 2)
        text_list = self.sess.run(predict, feed_dict={X: [image], keep_prob: 1})
        predict_text = text_list[0].tolist()

        vector = np.zeros(MAX_CAPTCHA * CHAR_SET_LEN)
        i = 0
        for t in predict_text:
            vector[i * 63 + t] = 1
            i += 1
        return vec2text(vector)
if __name__=="__main__":
    import os
    import time
    model=Check_Cnn()
    start=time.time()

    file_list=os.listdir('F:/bxw_train/data/val')
    for file in file_list:
        im = Image.open('F:/bxw_train/data/val/%s'%file)
        # im = Image.open('./yzm.jpg')
        code=model.img_to_code(im)
        print('识别结果为：%s'%code,'真实code为：%s'%file.split('.')[0])
    end=time.time()
    cost=end-start
    print(cost)
