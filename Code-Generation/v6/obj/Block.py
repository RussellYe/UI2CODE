import pandas as pd
import cv2
from random import randint as rint

from obj.Compo_HTML import CompoHTML
from obj.HTML import HTML
from obj.CSS import CSS

block_id = 0


def slice_blocks(compos_html, direction='v'):
    '''
    Vertically or horizontally scan compos
    :param direction: slice vertically or horizontally
    :param compos_html: CompoHTML objects, including elements and lists
    :return blocks: list of [block], block: list of [CompoHTML objects]
    '''
    blocks = []
    block_compos = []
    global block_id

    dividers = []
    divider = -1
    prev_divider = 0
    if direction == 'v':
        # reverse the direction of next slicing
        direction = 'h'
        compos_html.sort(key=lambda x: x.top)
        for compo in compos_html:
            # new block
            # if divider is lower than this compo's top, then slice the last block
            if divider < compo.top:
                prev_divider = divider
                dividers.append(compo.top)
                divider = compo.bottom
                dividers.append(divider)

                margin = int(compo.top - prev_divider)
                # a single compo is not be counted as a block
                if len(block_compos) == 1:
                    block_compos = []

                elif len(block_compos) > 1:
                    block_id += 1
                    css_name = '#block-' + str(block_id)
                    css = CSS(css_name, margin_top=str(margin) + 'px', clear='left', border="solid 2px black")
                    blocks.append(Block(id=block_id, compos=block_compos, slice_sub_block_direction=direction,
                                        html_id='block-'+str(block_id), css={css_name: css}))
                    block_compos = []
            # extend block
            elif compo.top < divider < compo.bottom:
                divider = compo.bottom
                dividers[-1] = divider
            block_compos.append(compo)

        # collect left compos
        if len(blocks) > 0 and len(block_compos) > 1:
            block_id += 1
            css_name = '#block-' + str(block_id)
            css = CSS(css_name, margin_top=str(int(block_compos[0].top - prev_divider)) + 'px', clear='left', border="solid 2px black")
            blocks.append(Block(id=block_id, compos=block_compos, slice_sub_block_direction=direction,
                                html_id='block-' + str(block_id), css={css_name: css}))

    elif direction == 'h':
        # reverse the direction of next slicing
        direction = 'v'
        compos_html.sort(key=lambda x: x.left)
        for compo in compos_html:
            # new block
            if divider < compo.left:
                prev_divider = divider
                dividers.append(compo.left)
                divider = compo.right
                dividers.append(divider)

                margin = int(compo.left - prev_divider)
                # a single compo is not be counted as a block
                if len(block_compos) == 1:
                    block_compos = []

                elif len(block_compos) > 1:
                    block_id += 1
                    css_name = '#block-' + str(block_id)
                    css = CSS(css_name, margin_left=str(margin) + 'px', float='left', border="solid 2px black")
                    blocks.append(Block(id=block_id, compos=block_compos, slice_sub_block_direction=direction,
                                        html_id='block-' + str(block_id), css={css_name: css}))
                    block_compos = []
            # extend block
            elif compo.left < divider < compo.right:
                divider = compo.right
                dividers[-1] = divider
            block_compos.append(compo)

        # collect left compos
        if len(blocks) > 0 and len(block_compos) > 1:
            block_id += 1
            css_name = '#block-' + str(block_id)
            css = CSS(css_name, margin_left=str(int(block_compos[0].left - prev_divider)) + 'px', float='left', border="solid 2px black")
            blocks.append(Block(id=block_id, compos=block_compos, slice_sub_block_direction=direction,
                                html_id='block-' + str(block_id), css={css_name: css}))

    return blocks


def visualize_blocks(blocks, img, img_shape):
    board = cv2.resize(img, img_shape)
    for block in blocks:
        board = block.visualize_block(board, show=False)
    cv2.imshow('compos', board)
    cv2.waitKey()
    cv2.destroyWindow('compos')


class Block:
    def __init__(self, id, compos,
                 slice_sub_block_direction='h', html_tag=None, html_id=None, html_class_name=None, css=None):
        self.block_id = id
        self.compos = compos                # list of CompoHTML objs
        self.block_obj = None               # CompoHTML obj
        self.block_img = None
        self.sub_blocks = []                  # list of Block objs

        self.top = None
        self.left = None
        self.bottom = None
        self.right = None
        self.width = None
        self.height = None

        # html info
        self.html = None        # HTML obj
        self.html_tag = 'div' if html_tag is None else html_tag
        self.html_id = html_id
        self.html_class_name = html_class_name
        self.html_script = ''   # sting
        self.css = css           # CSS objs
        self.css_script = ''    # string

        # only slice sub-block once
        self.slice_sub_blocks(slice_sub_block_direction)

        if css is not None:
            self.init_css()

        self.init_boundary()
        self.init_html()

    def init_boundary(self):
        self.top = min(self.compos, key=lambda x: x.top).top
        self.bottom = max(self.compos, key=lambda x: x.bottom).bottom
        self.left = min(self.compos, key=lambda x: x.left).left
        self.right = max(self.compos, key=lambda x: x.right).right

    def init_html(self):
        self.html = HTML(tag=self.html_tag, id=self.html_id, class_name=self.html_class_name)

        if len(self.sub_blocks) > 1:
            # add compos of sub blocks
            for sub_block in self.sub_blocks:
                self.html.add_child(sub_block.html_script)
        else:
            for compo in self.compos:
                self.html.add_child(compo.html_script)

        self.html_script = self.html.html_script

    def init_css(self):
        if len(self.sub_blocks) > 1:
            for sub_block in self.sub_blocks:
                self.css.update(sub_block.css)
        else:
            for compo in self.compos:
                self.css.update(compo.css)
        self.css_script = self.css
        self.assembly_css()

    def assembly_css(self):
        self.css_script = ''
        for i in self.css:
            self.css_script += self.css[i].css_script
        # self.block_obj.css = self.css

    def slice_sub_blocks(self, slice_sub_block_direction):
        '''
        Horizontally slice the block into sub-blocks
        '''
        self.sub_blocks = slice_blocks(self.compos, direction=slice_sub_block_direction)

    def clip_block_img(self, org, show=False):
        self.block_img = org[self.top: self.bottom, self.left: self.right]
        if show:
            self.show_block_img()

    def show_block_img(self):
        cv2.imshow('block', self.block_img)
        cv2.waitKey()
        cv2.destroyWindow('block')

    def visualize_block(self, img, flag='line', show=False, color=(0, 255, 0)):
        fill_type = {'line': 2, 'block': -1}
        board = img.copy()
        board = cv2.rectangle(board, (self.left, self.top), (self.right, self.bottom), color, fill_type[flag])
        if show:
            cv2.imshow('compo', board)
            cv2.waitKey()
            cv2.destroyWindow('compo')
        return board

    def visualize_sub_blocks(self, img, flag='line', show=True, color=None):
        fill_type = {'line': 2, 'block': -1}
        color = (rint(0, 255), rint(0, 255), rint(0, 255))
        board = img.copy()
        board = self.visualize_block(board, flag, color=color)
        for sub_block in self.sub_blocks:
            board = sub_block.visualize_block(board)
            # board = sub_block.visualize_sub_blocks(board, flag=flag, show=True, color=color)

        if show:
            print(len(self.sub_blocks), len(self.compos))
            cv2.imshow('sub_blocks', board)
            cv2.waitKey()
            cv2.destroyWindow('sub_blocks')

        board = img.copy()
        for sub_block in self.sub_blocks:
            board = sub_block.visualize_sub_blocks(board)

        return board
