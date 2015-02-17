#Embedded file name: scriber\widgets.py
"""
HTML Widgets
"""
import warnings
import scriber
COLOR_DEFAULT = 0
COLOR_PRIMARY = 1
COLOR_INFO = 2
COLOR_SUCCESS = 3
COLOR_WARNING = 4
COLOR_DANGER = 5
COLOR_INVERT = 6
COLOR_TEXT = 7
COLOR_CLASSES = {COLOR_DEFAULT: '',
 COLOR_PRIMARY: 'primary',
 COLOR_INFO: 'info',
 COLOR_SUCCESS: 'success',
 COLOR_WARNING: 'warning',
 COLOR_DANGER: 'danger',
 COLOR_INVERT: 'inverse',
 COLOR_TEXT: 'link'}
SIZE_DEFAULT = 0
SIZE_MINI = 1
SIZE_SMALL = 2
SIZE_LARGE = 3
SIZE_CLASSES = {SIZE_DEFAULT: '',
 SIZE_MINI: 'mini',
 SIZE_SMALL: 'small',
 SIZE_LARGE: 'large'}
FLOAT_NONE = 0
FLOAT_LEFT = 1
FLOAT_RIGHT = 2
FLOAT_CLASSES = {FLOAT_NONE: '',
 FLOAT_LEFT: 'pull-left',
 FLOAT_RIGHT: 'pull-right'}
BADGE_DEFAULT = 0
BADGE_SUCCESS = 1
BADGE_WARNING = 2
BADGE_IMPORTANT = 3
BADGE_INFO = 4
BADGE_INVERT = 5
BADGE_CLASSES = {BADGE_DEFAULT: '',
 BADGE_SUCCESS: 'success',
 BADGE_WARNING: 'warning',
 BADGE_IMPORTANT: 'important',
 BADGE_INFO: 'info',
 BADGE_INVERT: 'inverse'}

class Label(object):

    @classmethod
    def get(cls, text, tooltip = '', badge_type = BADGE_DEFAULT):
        badge_class = ''
        if badge_type:
            badge_class = ' label-%s' % BADGE_CLASSES[badge_type]
        if tooltip:
            tooltip = ' data-html="true" title="%s"' % tooltip.replace('"', '&quot;')
            badge_class = '%s ttip' % badge_class
        return '<span class="label%s"%s>%s</span>' % (badge_class, tooltip, text)

    @classmethod
    def green(cls, text, tooltip = ''):
        return cls.get(text, tooltip, badge_type=BADGE_SUCCESS)

    @classmethod
    def blue(cls, text, tooltip = ''):
        return cls.get(text, tooltip, badge_type=BADGE_INFO)

    @classmethod
    def yellow(cls, text, tooltip = ''):
        return cls.get(text, tooltip, badge_type=BADGE_WARNING)

    @classmethod
    def red(cls, text, tooltip = ''):
        return cls.get(text, tooltip, badge_type=BADGE_IMPORTANT)

    @classmethod
    def black(cls, text, tooltip = ''):
        return cls.get(text, tooltip, badge_type=BADGE_INVERT)


class Badge(object):

    @classmethod
    def get(cls, text, tooltip = '', badge_type = BADGE_DEFAULT):
        badge_class = ''
        if badge_type:
            badge_class = ' badge-%s' % BADGE_CLASSES[badge_type]
        if tooltip:
            tooltip = ' data-html="true" title="%s"' % tooltip.replace('"', '&quot;')
            badge_class = '%s ttip' % badge_class
        return '<span class="badge%s"%s>%s</span>' % (badge_class, tooltip, text)

    @classmethod
    def green(cls, text, tooltip = ''):
        return cls.get(text, tooltip, badge_type=BADGE_SUCCESS)

    @classmethod
    def blue(cls, text, tooltip = ''):
        return cls.get(text, tooltip, badge_type=BADGE_INFO)

    @classmethod
    def yellow(cls, text, tooltip = ''):
        return cls.get(text, tooltip, badge_type=BADGE_WARNING)

    @classmethod
    def red(cls, text, tooltip = ''):
        return cls.get(text, tooltip, badge_type=BADGE_IMPORTANT)

    @classmethod
    def black(cls, text, tooltip = ''):
        return cls.get(text, tooltip, badge_type=BADGE_INVERT)


class Icon(object):

    @classmethod
    def get(cls, icon, white = False):
        if icon:
            if white:
                icon = '%s icon-white' % icon
            return '<i class="%s"></i> ' % icon
        return ''


class Style(object):

    def __init__(self, icon = None, color = COLOR_DEFAULT, size = SIZE_DEFAULT, float_to = FLOAT_NONE, **kwargs):
        self._icon = icon
        self._color = color
        self._size = size
        self._float = float_to
        for k, v in kwargs.iteritems():
            setattr(self, '_%s' % k, v)

        self._color_format = '%s'
        self._size_format = '%s'
        self._float_format = '%s'

    @property
    def icon_class(self):
        if self._icon:
            white = ''
            if self.color:
                white = ' icon-white'
            return 'icon-%s%s' % (self._icon, white)
        return ''

    @property
    def icon(self):
        if self._icon:
            return '<i class="%s"></i> ' % self.icon_class
        return ''

    @property
    def float(self):
        print '######## Style.float was just called!'
        if self._float:
            return self._float_format % FLOAT_CLASSES[self._float]
        return ''

    @property
    def size(self):
        if self._size:
            return self._size_format % SIZE_CLASSES[self._size]
        return ''

    @property
    def color(self):
        if self._color:
            return self._color_format % COLOR_CLASSES[self._color]
        return ''


class Widget(object):
    template = 'widgets/test.html'

    def __init__(self):
        self.style = None

    def _pre_render(self):
        pass

    def set_style(self, style):
        """
        :param style: Style
        :type style: Style or dict or None
        """
        if style:
            if isinstance(style, dict):
                self.style = Style(**style)
            elif isinstance(style, Style):
                self.style = style
            else:
                warnings.warn('Widget.set_style got unexpected parameter type: %s => %r' % (type(style), style))
                self.style = Style()
        else:
            self.style = Style()

    def render(self):
        self._pre_render()
        return scriber.scribe(self.template, self.__dict__)


class LinkItem(object):

    def __init__(self, label, action, icon = None):
        self.label = label
        self.action = action
        self._icon = icon

    @property
    def icon(self):
        if self._icon:
            return Icon.get(self._icon)
        return ''


class ButtonGroup(Widget):
    template = 'widgets/button_group.html'

    def __init__(self, label, action, item_list = None, style = None):
        """
        :param label:
        :type label:
        :param action:
        :type action: str
        :param item_list:
        :type item_list:
        :param style: Style
        :type style: Style or dict or None
        """
        super(ButtonGroup, self).__init__()
        self.label = label
        self.action = action
        self.set_style(style)
        self.style._color_format = ' btn-%s'
        self.style._size_format = ' btn-%s'
        self.style._float_format = ' %s'
        if item_list:
            self.item_list = item_list
        else:
            self.item_list = []

    def add_item(self, label, action, icon = None):
        self.item_list.append(LinkItem(label, action, icon))

    def add_divider(self):
        self.item_list.append(LinkItem('', '', ''))

    def _pre_render(self):
        for i, item in enumerate(self.item_list):
            if isinstance(item, (list, tuple)):
                self.item_list[i] = LinkItem(*item)
            elif isinstance(item, dict):
                self.item_list[i] = LinkItem(**item)
            elif not isinstance(item, LinkItem):
                self.item_list[i] = LinkItem(item, '')

        if self.action.startswith('/') or self.action.startswith('http'):
            self.action = "go('%s');" % self.action

    @classmethod
    def get(cls, label, action, item_list, style):
        return cls(label=label, action=action, item_list=item_list, style=style).render()


class ModalMessage(Widget):
    template = 'widgets/modal_message.html'

    def __init__(self, title, body = '', dom_id = '', ok_label = 'Ok'):
        super(ModalMessage, self).__init__()
        self.title = title
        self.body = body
        self.dom_id = dom_id
        self.ok_label = ok_label

    def _pre_render(self):
        if isinstance(self.body, (list, tuple)):
            self.body = '</p><p>'.join(self.body)

    @classmethod
    def get(cls, title, body = '', dom_id = '', ok_label = 'Ok'):
        return cls(title, body, dom_id, ok_label).render()


class QuickTable(Widget):
    template = 'widgets/quick_table.html'
    DEFAULT_DOM_CLASSES = ['table',
     'table-condensed',
     'table-bordered',
     'table-striped',
     'table-hover']

    def __init__(self, dict_or_list_of_lists, dom_id = None, dom_classes = DEFAULT_DOM_CLASSES, dom_style = None, **kwargs):
        """Renders a python dict (dict-like object) or list of lists (data
        result set) into a simple HTML table.
        
        Dicts and dict like objects (key, value pairs) get turned into a
        vertical "property" table with the keys as TH with right text align in
        a column to the left and the value in a TD in the adjacent column.
        
        Lists of lists and similar data sets get turned into standard tables
        where the first "row" (list) is the header for the table and the rest
        of the data are rows.
        
        :param dict_or_list_of_lists:
        :type dict_or_list_of_lists: dict or list or tuple
        :type dom_id: str
        :param dom_classes: A single string or list of strings. Default
                            contains 'table-condensed', 'table-bordered',
                            'table-striped' and 'table-hover'
        :type dom_classes: str or list
        :param dom_style: A single string or a dict of properties and values
        :type dom_style: str or dict
        :param kwargs: Any other HTML attributes to assign to the table
        :type kwargs: dict
        """
        super(QuickTable, self).__init__()
        self._dom_id = dom_id
        self._dom_classes = dom_classes
        self._dom_style = dom_style
        self._attr_map = kwargs
        self.data = dict_or_list_of_lists
        self.attributes = ''
        self.is_vertical = False

    def _pre_render(self):
        table_attributes = []
        if isinstance(self.data, dict):
            self.is_vertical = True
        if self._dom_id:
            table_attributes.append('id="%s"' % self._dom_id)
        if self._dom_classes:
            if isinstance(self._dom_classes, (list, tuple)):
                table_attributes.append('class="%s"' % ' '.join(self._dom_classes))
            else:
                table_attributes.append('class="%s"' % self._dom_classes)
        if self._dom_style:
            if isinstance(self._dom_style, dict):
                table_attributes.append('style="%s"' % ';'.join([ '%s:%s' % (k, v) for k, v in self._dom_style ]))
            else:
                table_attributes.append('style="%s"' % self._dom_style)
        if self._attr_map:
            for k, v in self._attr_map:
                table_attributes.append('%s="%s"' % (k, v))

        self.attributes = ' %s' % ' '.join(table_attributes)

    @classmethod
    def get(cls, dict_or_list_of_lists, dom_id = None, dom_classes = DEFAULT_DOM_CLASSES, dom_style = None, **kwargs):
        return cls(dict_or_list_of_lists, dom_id, dom_classes, dom_style, **kwargs).render()
