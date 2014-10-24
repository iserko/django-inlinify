from __future__ import absolute_import, unicode_literals
import os
from os.path import dirname, abspath
from os.path import join as joinpath
import re
import unittest

from nose.tools import eq_, ok_

from django_premailer.premailer import Premailer
from django_premailer.css_tools import CSSParser

whitespace_between_tags = re.compile('>\s*<')


def compare_html(one, two):
    one = one.strip()
    two = two.strip()
    one = whitespace_between_tags.sub('>\n<', one)
    two = whitespace_between_tags.sub('>\n<', two)
    one = one.replace('><', '>\n<')
    two = two.replace('><', '>\n<')
    for i, line in enumerate(one.splitlines()):
        other = two.splitlines()[i]
        if line.lstrip() != other.lstrip():
            eq_(line.lstrip(), other.lstrip())

ROOT = abspath(joinpath(dirname(__file__)))


def html_path(filename):
    return os.path.join(ROOT, 'html', filename)


def css_path(filename):
    return os.path.join(ROOT, 'css', filename)


class Tests(unittest.TestCase):

    def test_merge_styles_basic(self):
        old = 'font-size:1px; color: red'
        new = 'font-size:2px; font-weight: bold'
        expect = 'color:red;', 'font-size:2px;', 'font-weight:bold'
        parser = CSSParser()
        result = parser.merge_styles(old, new)
        for each in expect:
            ok_(each in result)

    def test_merge_styles_non_trivial(self):
        old = 'background-image:url("data:image/png;base64,iVBORw0KGg")'
        new = 'font-size:2px; font-weight: bold'
        expect = (
            'background-image:url("data:image/png;base64,iVBORw0KGg")',
            'font-size:2px;',
            'font-weight:bold'
        )
        parser = CSSParser()
        result = parser.merge_styles(old, new)
        for each in expect:
            ok_(each in result)


    def test_basic_html(self):
        """test the simplest case"""

        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        h1, h2 { color:red; }
        strong {
            text-decoration:none
            }
        </style>
        </head>
        <body>
        <h1>Hi!</h1>
        <p><strong>Yes!</strong></p>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <h1 style="color:red">Hi!</h1>
        <p><strong style="text-decoration:none">Yes!</strong></p>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)
        compare_html(expect_html, result_html)

    def test_basic_html_shortcut_function(self):
        """test the plain transform function"""
        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        h1, h2 { color:red; }
        strong {
            text-decoration:none
            }
        </style>
        </head>
        <body>
        <h1>Hi!</h1>
        <p><strong>Yes!</strong></p>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <h1 style="color:red">Hi!</h1>
        <p><strong style="text-decoration:none">Yes!</strong></p>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)
        compare_html(expect_html, result_html)

    def test_empty_style_tag(self):
        """empty style tag"""

        html = """<html>
        <head>
        <title></title>
        <style type="text/css"></style>
        </head>
        <body>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title></title>
        </head>
        <body>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_include_star_selector(self):
        """test the simplest case"""

        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        p * { color: red }
        </style>
        </head>
        <body>
        <h1>Hi!</h1>
        <p><strong>Yes!</strong></p>
        </body>
        </html>"""

        expect_html_not_included = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <h1>Hi!</h1>
        <p><strong>Yes!</strong></p>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)

        compare_html(expect_html_not_included, result_html)

        expect_html_star_included = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <h1>Hi!</h1>
        <p><strong style="color:red">Yes!</strong></p>
        </body>
        </html>"""

        p = Premailer(include_star_selectors=True)
        result_html = p.transform(html)
        compare_html(expect_html_star_included, result_html)

    def test_mixed_pseudo_selectors(self):
        """mixing pseudo selectors with straight forward selectors"""

        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        p { color: yellow }
        a { color: blue }
        a:hover { color: pink }
        </style>
        </head>
        <body>
        <p>
          <a href="#">Page</a>
        </p>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">a:hover {color:pink !important}</style>
        </head>
        <body>
        <p style="color:yellow"><a href="#" style="color:blue">Page</a></p>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_basic_html_with_pseudo_selector(self):
        """test the simplest case"""

        html = """
        <html>
        <style type="text/css">
        h1 { border:1px solid black }
        p { color:red;}
        p::first-letter { float:left; }
        </style>
        <h1>Peter</h1>
        <p>Hej</p>
        </html>
        """

        expect_html = """<html>
        <head>
        <style type="text/css">p::first-letter {float:left !important}</style>
        </head>
        <body>
        <h1 style="border:1px solid black">Peter</h1>
        <p style="color:red">Hej</p>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)
        compare_html(expect_html, result_html)

    def test_parse_style_rules(self):
        p = Premailer()  # won't need the html
        func = p.css_parser.parse
        rules, leftover = func("""
        h1, h2 { color:red; }
        /* ignore
            this */
        strong {
            text-decoration:none
            }
        ul li {  list-style: 2px; }
        a:hover { text-decoration: underline }
        """, 0)

        # 'rules' is a list, turn it into a dict for
        # easier assertion testing
        rules_dict = {}
        rules_specificity = {}
        for specificity, k, v in rules:
            rules_dict[k] = v
            rules_specificity[k] = specificity

        ok_('h1' in rules_dict)
        ok_('h2' in rules_dict)
        ok_('strong' in rules_dict)
        ok_('ul li' in rules_dict)

        eq_(rules_dict['h1'], 'color:red')
        eq_(rules_dict['h2'], 'color:red')
        eq_(rules_dict['strong'], 'text-decoration:none')
        eq_(rules_dict['ul li'], 'list-style:2px')
        ok_('a:hover' not in rules_dict)

        p = Premailer(exclude_pseudoclasses=True)  # won't need the html
        func = p.css_parser.parse
        rules, leftover = func("""
        ul li {  list-style: 2px; }
        a:hover { text-decoration: underline }
        """, 0)

        eq_(len(rules), 1)
        specificity, k, v = rules[0]
        eq_(k, 'ul li')
        eq_(v, 'list-style:2px')

        eq_(leftover, 'a:hover {text-decoration:underline !important}')

    def test_precedence_comparison(self):
        p = Premailer()  # won't need the html
        rules, leftover = p.css_parser.parse("""
        #identified { color:blue; }
        h1, h2 { color:red; }
        ul li {  list-style: 2px; }
        li.example { color:green; }
        strong { text-decoration:none }
        div li.example p.sample { color:black; }
        """, 0)

        # 'rules' is a list, turn it into a dict for
        # easier assertion testing
        rules_specificity = {}
        for specificity, k, v in rules:
            rules_specificity[k] = specificity

        # Last in file wins
        ok_(rules_specificity['h1'] < rules_specificity['h2'])
        # More elements wins
        ok_(rules_specificity['strong'] < rules_specificity['ul li'])
        # IDs trump everything
        ok_(rules_specificity['div li.example p.sample'] <
            rules_specificity['#identified'])

        # Classes trump multiple elements
        ok_(rules_specificity['ul li'] <
            rules_specificity['li.example'])

    def test_base_url_fixer(self):
        """if you leave some URLS as /foo and set base_url to
        'http://www.google.com' the URLS become 'http://www.google.com/foo'
        """
        html = '''<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <img src="/images/foo.jpg">
        <img src="/images/bar.gif">
        <img src="cid:images/baz.gif">
        <img src="http://www.googe.com/photos/foo.jpg">
        <a href="/home">Home</a>
        <a href="http://www.peterbe.com">External</a>
        <a href="subpage">Subpage</a>
        <a href="#internal_link">Internal Link</a>
        </body>
        </html>
        '''

        expect_html = '''<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <img src="http://kungfupeople.com/images/foo.jpg">
        <img src="http://kungfupeople.com/images/bar.gif">
        <img src="cid:images/baz.gif">
        <img src="http://www.googe.com/photos/foo.jpg">
        <a href="http://kungfupeople.com/home">Home</a>
        <a href="http://www.peterbe.com">External</a>
        <a href="http://kungfupeople.com/subpage">Subpage</a>
        <a href="#internal_link">Internal Link</a>
        </body>
        </html>'''

        p = Premailer(
            base_url='http://kungfupeople.com',
            preserve_internal_links=True
        )
        result_html = p.transform(html)
        compare_html(expect_html, result_html)

    def test_base_url_with_path(self):
        """if you leave some URLS as /foo and set base_url to
        'http://www.google.com' the URLS become 'http://www.google.com/foo'
        """

        html = '''<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <img src="/images/foo.jpg">
        <img src="/images/bar.gif">
        <img src="http://www.googe.com/photos/foo.jpg">
        <a href="/home">Home</a>
        <a href="http://www.peterbe.com">External</a>
        <a href="http://www.peterbe.com/base/">External 2</a>
        <a href="subpage">Subpage</a>
        <a href="#internal_link">Internal Link</a>
        </body>
        </html>
        '''

        expect_html = '''<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <img src="http://kungfupeople.com/base/images/foo.jpg">
        <img src="http://kungfupeople.com/base/images/bar.gif">
        <img src="http://www.googe.com/photos/foo.jpg">
        <a href="http://kungfupeople.com/base/home">Home</a>
        <a href="http://www.peterbe.com">External</a>
        <a href="http://www.peterbe.com/base/">External 2</a>
        <a href="http://kungfupeople.com/base/subpage">Subpage</a>
        <a href="#internal_link">Internal Link</a>
        </body>
        </html>'''

        p = Premailer(base_url='http://kungfupeople.com/base', preserve_internal_links=True)
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_style_block_with_external_urls(self):
        """
        From http://github.com/peterbe/premailer/issues/#issue/2

        If you have
          body { background:url(http://example.com/bg.png); }
        the ':' inside '://' is causing a problem
        """

        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        body {
          color:#123;
          background: url(http://example.com/bg.png);
          font-family: Omerta;
        }
        </style>
        </head>
        <body>
        <h1>Hi!</h1>
        </body>
        </html>"""

        expect_html = '''<html>
        <head>
        <title>Title</title>
        </head>
        <body style="background:url(http://example.com/bg.png); color:#123; font-family:Omerta">
        <h1>Hi!</h1>
        </body>
        </html>'''

        p = Premailer()
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def fragment_in_html(self, fragment, html, fullMessage=False):
        if fullMessage:
            message = '"{0}" not in\n{1}'.format(fragment, html)
        else:
            message = '"{0}" not in HTML'.format(fragment)
        ok_(fragment in html, message)

    def test_css_with_html_attributes(self):
        """Some CSS styles can be applied as normal HTML attribute like
        'background-color' can be turned into 'bgcolor'
        """

        html = """<html>
        <head>
        <style type="text/css">
        td { background-color:red; }
        p { text-align:center; }
        table { width:200px; }
        </style>
        </head>
        <body>
        <p>Text</p>
        <table>
          <tr>
            <td>Cell 1</td>
            <td>Cell 2</td>
          </tr>
        </table>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        </head>
        <body>
        <p style="text-align:center" align="center">Text</p>
        <table style="width:200px" width="200">
          <tr>
            <td style="background-color:red" bgcolor="red">Cell 1</td>
            <td style="background-color:red" bgcolor="red">Cell 2</td>
          </tr>
        </table>
        </body>
        </html>"""

        p = Premailer(exclude_pseudoclasses=True)
        result_html = p.transform(html)

        expect_html = re.sub('}\s+', '}', expect_html)
        result_html = result_html.replace('}\n', '}')

        compare_html(expect_html, result_html)

    def test_css_disable_basic_html_attributes(self):
        """Some CSS styles can be applied as normal HTML attribute like
        'background-color' can be turned into 'bgcolor'
        """

        html = """<html>
        <head>
        <style type="text/css">
        td { background-color:red; }
        p { text-align:center; }
        table { width:200px; height: 300px; }
        </style>
        </head>
        <body>
        <p>Text</p>
        <table>
          <tr>
            <td>Cell 1</td>
            <td>Cell 2</td>
          </tr>
        </table>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        </head>
        <body>
        <p style="text-align:center">Text</p>
        <table style="height:300px; width:200px">
          <tr>
            <td style="background-color:red" bgcolor="red">Cell 1</td>
            <td style="background-color:red" bgcolor="red">Cell 2</td>
          </tr>
        </table>
        </body>
        </html>"""

        p = Premailer(
            exclude_pseudoclasses=True,
            disable_basic_attributes=['align', 'width', 'height']
        )
        result_html = p.transform(html)

        expect_html = re.sub('}\s+', '}', expect_html)
        result_html = result_html.replace('}\n', '}')

        compare_html(expect_html, result_html)

    def test_apple_newsletter_example(self):
        # stupidity test
        html = open(html_path('test-apple-newsletter.html')).read()

        p = Premailer(exclude_pseudoclasses=False, keep_style_tags=True)
        result_html = p.transform(html)
        ok_('<html>' in result_html)
        ok_('<style media="only screen and (max-device-width: 480px)" '
            'type="text/css">\n'
            '* {line-height: normal !important; -webkit-text-size-adjust: 125%}\n'
            '</style>' in result_html)

    def test_mailto_url(self):
        """if you use URL with mailto: protocol, they should stay as mailto:
        when baseurl is used
        """

        html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <a href="mailto:e-mail@example.com">e-mail@example.com</a>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <a href="mailto:e-mail@example.com">e-mail@example.com</a>
        </body>
        </html>"""

        p = Premailer(base_url='http://kungfupeople.com')
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_last_child(self):
        html = """<html>
        <head>
        <style type="text/css">
        div {
            text-align: right;
        }
        div:last-child {
            text-align: left;
        }
        </style>
        </head>
        <body>
        <div>First child</div>
        <div>Last child</div>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        </head>
        <body>
        <div style="text-align:right" align="right">First child</div>
        <div style="text-align:left" align="left">Last child</div>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)
        compare_html(expect_html, result_html)

    def test_last_child_exclude_pseudo(self):
        html = """<html>
        <head>
        <style type="text/css">
        div {
            text-align: right;
        }
        div:last-child {
            text-align: left;
        }
        </style>
        </head>
        <body>
        <div>First child</div>
        <div>Last child</div>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        </head>
        <body>
        <div style="text-align:right" align="right">First child</div>
        <div style="text-align:left" align="left">Last child</div>
        </body>
        </html>"""

        p = Premailer(exclude_pseudoclasses=True)
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_mediaquery(self):
        html = """<html>
        <head>
        <style type="text/css">
        div {
            text-align: right;
        }
        @media print{
            div {
                text-align: center;
                color: white;
            }
            div {
                font-size: 999px;
            }
        }
        </style>
        </head>
        <body>
        <div>First div</div>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <style type="text/css">@media print {
        div {
            text-align: center !important;
            color: white !important
            }
        div {
            font-size: 999px !important
            }
        }</style>
        </head>
        <body>
        <div style="text-align:right" align="right">First div</div>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)
        compare_html(expect_html, result_html)

    def test_child_selector(self):
        html = """<html>
        <head>
        <style type="text/css">
        body > div {
            text-align: right;
        }
        </style>
        </head>
        <body>
        <div>First div</div>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        </head>
        <body>
        <div style="text-align:right" align="right">First div</div>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_doctype(self):
        html = (
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
            '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
            """<html>
            <head>
            </head>
            <body>
            </body>
            </html>"""
        )

        expect_html = (
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
            '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
            """<html>
            <head>
            </head>
            <body>
            </body>
            </html>"""
        )

        p = Premailer()
        result_html = p.transform(html)
        compare_html(expect_html, result_html)

    def test_favour_rule_with_element_over_generic(self):
        html = """<html>
        <head>
        <style>
        div.example {
            color: green;
        }
        .example {
            color: black;
        }
        </style>
        </head>
        <body>
        <div class="example"></div>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        </head>
        <body>
        <div style="color:green"></div>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_favour_rule_with_class_over_generic(self):
        html = """<html>
        <head>
        <style>
        div.example {
            color: green;
        }
        div {
            color: black;
        }
        </style>
        </head>
        <body>
        <div class="example"></div>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        </head>
        <body>
        <div style="color:green"></div>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)
        compare_html(expect_html, result_html)

    def test_favour_rule_with_id_over_others(self):
        html = """<html>
        <head>
        <style>
        #identified {
            color: green;
        }
        div.example {
            color: black;
        }
        </style>
        </head>
        <body>
        <div class="example" id="identified"></div>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        </head>
        <body>
        <div id="identified" style="color:green"></div>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_multiple_style_elements(self):
        """Asserts that rules from multiple style elements are inlined correctly."""

        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        h1, h2 { color:red; }
        strong {
            text-decoration:none
            }
        </style>
        <style type="text/css">
        h1, h2 { color:green; }
        p {
            font-size:120%
            }
        </style>
        </head>
        <body>
        <h1>Hi!</h1>
        <p><strong>Yes!</strong></p>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <h1 style="color:green">Hi!</h1>
        <p style="font-size:120%"><strong style="text-decoration:none">Yes!</strong></p>
        </body>
        </html>"""
        p = Premailer()
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_disabled_validator(self):
        """test disabled_validator"""

        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        h1, h2 { fo:bar; }
        strong {
            color:baz;
            text-decoration:none;
            }
        </style>
        </head>
        <body>
        <h1>Hi!</h1>
        <p><strong>Yes!</strong></p>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <h1 style="fo:bar">Hi!</h1>
        <p><strong style="color:baz; text-decoration:none">Yes!</strong></p>
        </body>
        </html>"""

        p = Premailer(enable_validation=False)
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_fontface_selectors_with_no_selectortext(self):
        """
        @font-face selectors are weird.
        This is a fix for https://github.com/peterbe/django_premailer/issues/71
        """
        html = """<!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Document</title>
            <style>
            @font-face {
                font-family: 'Garamond';
                src:
                    local('Garamond'),
                    local('Garamond-Regular'),
                    url('Garamond.ttf') format('truetype'); /* Safari, Android, iOS */
                    font-weight: normal;
                    font-style: normal;
            }
            </style>
        </head>
        <body></body>
        </html>"""

        p = Premailer(enable_validation=False)
        p.transform(html)  # it should just work

    def test_keyframe_selectors(self):
        """
        keyframes shouldn't be a problem.
        """
        html = """<!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Document</title>
            <style>
            @keyframes fadein {
                from { opacity: 0; }
                to   { opacity: 1; }
            }

            /* Firefox */
            @-moz-keyframes fadein {
                from { opacity: 0; }
                to   { opacity: 1; }
            }

            /* Safari and Chrome */
            @-webkit-keyframes fadein {
                from { opacity: 0; }
                to   { opacity: 1; }
            }

            /* Internet Explorer */
            @-ms-keyframes fadein {
                from { opacity: 0; }
                to   { opacity: 1; }
            }

            /* Opera */
            @-o-keyframes fadein {
                from { opacity: 0; }
                to   { opacity: 1; }
            }
            </style>
        </head>
        <body></body>
        </html>"""

        p = Premailer(enable_validation=False)
        p.transform(html)  # it should just work

    def test_parsing_from_css_local_file(self):
        """Tests that css parsing from a local file works
        """
        html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <h1>Hi!</h1>
        <p><strong>Yes!</strong></p>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <h1 style="color:red">Hi!</h1>
        <p><strong style="text-decoration:none">Yes!</strong></p>
        </body>
        </html>"""

        p = Premailer(css_files=[css_path('test_parsing_from_css_local_file.css')])
        result_html = p.transform(html)
        compare_html(expect_html, result_html)

    def test_ignore_style_elements_with_media_attribute(self):
        """Asserts that style elements with media attributes other than
        'screen' are ignored."""

        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
            h1, h2 { color:red; }
            strong {
                text-decoration:none
            }
        </style>
        <style type="text/css" media="screen">
            h1, h2 { color:green; }
            p {
                font-size:16px;
                }
        </style>
        <style type="text/css" media="only screen and (max-width: 480px)">
            h1, h2 { color:orange; }
            p {
                font-size:120%;
            }
        </style>
        </head>
        <body>
        <h1>Hi!</h1>
        <p><strong>Yes!</strong></p>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css" media="only screen and (max-width: 480px)">
            h1, h2 { color:orange; }
            p {
                font-size:120%;
            }
        </style>
        </head>
        <body>
        <h1 style="color:green">Hi!</h1>
        <p style="font-size:16px"><strong style="text-decoration:none">Yes!</strong></p>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_style_attribute_specificity(self):
        """Stuff already in style attributes beats style tags."""

        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        h1 { color: pink }
        h1.foo { color: blue }
        </style>
        </head>
        <body>
        <h1 class="foo" style="color: green">Hi!</h1>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        </head>
        <body>
        <h1 style="color:green">Hi!</h1>
        </body>
        </html>"""

        p = Premailer()
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_leftover_important(self):
        """Asserts that leftover styles should be marked as !important."""

        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        a { color: red; }
        a:hover { color: green; }
        a:focus { color: blue !important; }
        </style>
        </head>
        <body>
        <a href="#">Hi!</a>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        a { color: red; }
        a:hover { color: green; }
        a:focus { color: blue !important; }
        </style>
        </head>
        <body>
        <a href="#" style="color:red">Hi!</a>
        </body>
        </html>"""

        p = Premailer(keep_style_tags=True)
        result_html = p.transform(html)

        compare_html(expect_html, result_html)

    def test_comments_in_media_queries(self):
        """CSS comments inside a media query block should not be a problem"""
        html = """<!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Document</title>
            <style>
            @media screen {
                /* comment */
            }
            </style>
        </head>
        <body></body>
        </html>"""

        p = Premailer(enable_validation=False)
        result_html = p.transform(html)
        ok_('/* comment */' in result_html)

    def test_existing_style_blocks_are_kept(self):
        """Asserts that leftover styles should be marked as !important."""

        html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        a { color: red; }
        </style>
        </head>
        <body>
        <a href="#">Hi!</a>
        </body>
        </html>"""

        expect_html = """<html>
        <head>
        <title>Title</title>
        <style type="text/css">
        a { color: red; }
        </style>
        <style type="text/css">@media all and (min-width: 600px) {
            a {
                font-size: 12px !important
            }
        }</style>
        </head>
        <body>
        <a href="#" style="color:red">Hi!</a>
        </body>
        </html>"""

        p = Premailer(css_files=[css_path('test_existing_style_blocks_are_kept.css')],
                      keep_style_tags=True)
        result_html = p.transform(html)
        compare_html(expect_html, result_html)