#/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from collections import OrderedDict
import os
import re
from typing import Any, Dict, List, Text
import logging

import github3
import yaml

from .utils import extract_info_from_url


__all__ = ['Reaction']  # only expose a few api


class Reaction(object):
    def __init__(self,
        user, # type: Text
        password, # type: Text
        logger, # type: logging.Logger
        posts_location=u'content/post/' # type: Text
        ):
        # type: (...) -> None
        self.user = user
        self.password = password
        self.logger = logger
        self.posts_location = posts_location

        self.client = github3.login(user, password) # type: github3.github.GitHub

    def run(self,
            event, # type: Text
            payload, # type: Dict
            *args,
            **kwargs
            ):
        # (...) -> Dict
        """dispatch event to its real "runner" and run"""
        # python magic, directly call attribute by convention
        # convention: runner == '_' + event
        try:
            runner = getattr(self, '_{}'.format(event))
            if callable(runner):
                runner(event, payload, *args, **kwargs)
        except AttributeError:
            self.logger.info(u'event {} not implemented'.format(event))
            return {
                'event': event,
                'data': u'runner for "{}" is not implemented.'.format(event),
                'status': 'ok'
            }
        except:
            self.logger.exception(u'event {} has an exception'.format(event))
            return {
                'event': event,
                'data': u'something goes wrong with "{}"'.format(event),
                'status': 'error'
            }
        self.logger.info(u'event {} is ok'.format(event))
        return {
            'event': event,
            'data': u'smooth for "{}"'.format(event),
            'status': 'ok'
        }

    def _pull_request(
        self,
        event, # type: Text
        payload # type: Dict
        ):
        # guard: we don't react for self activity
        person = payload['pull_request']['user']['login'] # type: Text
        if person == self.user:
            return

        # do something
        greeting_for_first_time_contributor(event, payload, self.logger, self.client)
        check_article_submission(
            event, payload, self.logger, self.client, self.posts_location)

    def _issues(
        self,
        event, # type: Text
        payload # type: Dict
        ):
        # guard: we don't react for self activity
        person = payload['comment']['user']['login'] # type: Text
        if person == self.user:
            return

        # do something
        say_something_if_mentioned(
            event, payload, self.logger, self.client, self.user)

    def _issue_comment(
        self,
        event, # type: Text
        payload # type: Dict
        ):
        # guard: we don't react for self activity
        person = payload['comment']['user']['login'] # type: Text
        if person == self.user:
            return

        # do something
        say_something_if_mentioned(
            event, payload, self.logger, self.client, self.user)


################################################
# lots of reactions below
################################################

def greeting_for_first_time_contributor(
    event, # type: Text
    payload, # type: Dict
    logger, # type: logging.Logger
    client, # type: github3.github.GitHub
    *args,
    **kwargs
    ):
    # type: (...) -> bool
    """say hi and/or say something about cla to first time contributor"""
    if not (
        event == 'pull_request' and
        payload['action'] == 'opened' and
        payload['pull_request']['author_association'] == 'NONE'):
        return False

    url_info = extract_info_from_url(payload['pull_request']['url'])
    person = payload['pull_request']['user']['login'] # type: Text

    # say hi, post comment on this issue
    issue = client.issue(
        url_info['owner'], url_info['repo'], url_info['number'])
    issue.create_comment(
        u'@{}\n'
        u"Hi, it seems that you're the first time contributor, welcome!\n"
        u'你好，你似乎是第一次投稿，非常欢迎！'
    ).format(person)
    return True


def check_article_submission(
    event, # type: Text
    payload, # type: Dict
    logger, # type: logging.Logger
    client, # type: github3.github.GitHub
    posts_location = u'content/post/', # type: Text
    *args,
    **kwargs
    ):
    # type: (...) -> bool
    """we have something to check and comment for every article pull request"""
    if not (
        event == 'pull_request' and
        payload['action'] == 'opened'):
        return False

    url_info = extract_info_from_url(payload['pull_request']['url'])
    pr = client.pull_request(
        url_info['owner'], url_info['repo'], url_info['number'])
    issue = client.issue(
        url_info['owner'], url_info['repo'], url_info['number'])

    messages = OrderedDict() # type: Dict[Text, Any]

    files_info = {} # type: Dict[Text, github3.pulls.PullFile]
    for single_file in pr.files():
        files_info[single_file.filename] = single_file

    # we only deal with those who make articles
    articles = {} # type: Dict[Text, github3.pulls.PullFile]
    for name, single_file in files_info.items():
        if name.startswith(posts_location):
            articles[name] = single_file
    if not articles:
        return False

    # for first time user, we remind them to add members.yaml
    if payload['pull_request']['author_association'] == 'NONE':
        if 'data/members.yaml' not in files_info:
            messages[u'添加 `data/members.yaml`'] = (
                u"我们注意到你是第一次投稿者，"
                u"也许你想在这次 pr 里"
                u"向 `data/members.yaml` 添加你自己的信息一并提交。"
            )

    # we check the article
    for name, article in articles.items():
        assert name.startswith(posts_location)

        single_article_messages = {} # type: Dict[Text, Text]

        # file name checking
        name_no_parent = name[len(posts_location):].lstrip('/')
        if not name_no_parent:
            # unexpected thing happen??
            continue
        if '/' in name_no_parent:
            single_article_messages[u'文章所在位置: {}'.format(name)] = (
                u"如果你投稿的是文章，不应该创建更深的文件；如果不是请忽略。"
            )
        file_name, ext = os.path.splitext(name.split('/')[-1])
        allowed_file_exts = {
            '.md', '.markdown',
            '.rmd', '.rmarkdown',
            '.txt',
            '.ipynb'
        }
        file_name_warning = u''
        if ext.lower() not in allowed_file_exts:
            file_name_warning += (
                u'只允许这类文件：{t}\n\n'
            ).format(t=allowed_file_exts)
        if re.match(r'\d{4}-\d{2}-\d{2}-.+', file_name) is None:
            file_name_warning += (
                u"文件名格式应该如 `2018-01-01-something.md`\n\n"
            )
        if file_name_warning:
            single_article_messages[u'文件名问题'] = \
                file_name_warning.rstrip()

        # check file content (including yaml meta)
        content = article.contents() # type: github3.repos.contents.Contents
        text = content.decoded.decode('utf-8')
        file_content_warning = _check_article_content(text)
        if file_content_warning:
            single_article_messages[u'文件内容问题'] = \
                file_content_warning

        messages[u'文件 `{}` 问题'.format(name)] = single_article_messages

    if not messages:
        return False

    person = payload['pull_request']['user']['login'] # type: Text

    md_lines = [
        u'# 自动检查',
        u'@{} 欢迎投稿！不过我们发现了一些问题。'.format(person)
    ]
    md_lines += _flattern_messages_to_md_lines(messages, depth=2)
    comment = u'\n\n'.join(md_lines)
    issue.create_comment(comment)
    logger.info('we created comment for some errors in article submission')
    return True

def _check_article_content(
    text # type: Text
    ):
    # type: (...) -> Text
    """a helper function to ensure article content is valid"""
    lines = text.split('\n')
    if not lines:
        return u'没有内容？？\n\n'

    warning = u''
    body_start_line_pos = 0

    # check yaml
    if not re.match(r'\-{3,}', lines[0]):
        warning += u'缺少 yaml meta？？\n\n'
    else:
        meta_delimeter_len = len(lines[0])

        # extract yaml
        yaml_lines = []
        for idx, line in enumerate(lines):
            if idx == 0:
                continue
            if (line.rstrip() == '-' * meta_delimeter_len or
                line.rstrip() == '.' * meta_delimeter_len):
                # we've found the yaml meta end
                body_start_line_pos = idx + 1
                break
            yaml_lines.append(line)

        if body_start_line_pos >= len(lines) - 1:
            # no article body???
            warning += (
                u'yaml 分隔符异常；'
                u'你应该在两行 `---` 之间插入 yaml meta 信息。\n\n'
            )
            return warning.rstrip()

        try:
            yaml_parsed_dict = yaml.safe_load('\n'.join(yaml_lines))
            yaml_is_parsed = True
        except:
            yaml_is_parsed = False
        if yaml_is_parsed:
            if 'meta_extra' not in yaml_parsed_dict:
                warning += (
                    u'请添加一行 `meta_extra: ""` 到 yaml meta 里。\n\n'
                )
            if 'forum_id' not in yaml_parsed_dict:
                warning += (
                    u'请添加一行 `forum_id:` 到 yaml meta 里。'
                    u'编辑部成员会在发布前添加具体信息。\n\n'
                )
            for essential_info in {'author', 'categories', 'tags'}:
                if essential_info not in yaml_parsed_dict:
                    warning += (
                        u'请在 yaml meta 添加 `{info_key}` 值。\n\n'
                    ).format(info_key=essential_info)

        # wild checkings on the real content body
        no_alt_img_pattern = re.compile(r'!\[\]\([^\)]*\)')
        for idx in range(body_start_line_pos, len(lines)):
            if no_alt_img_pattern.findall(lines[idx]):
                warning += (
                    u'似乎第 {pos} 行的图片没有加上文字说明，'
                    u'这对于无障碍阅读很重要，请考虑添加上去。\n\n'
                ).format(pos=idx+1) # line in py starts with 0, thus shift 1 here

    # finally we have full warning
    return warning.rstrip()

def _flattern_messages_to_md_lines(
    messages, # type: Dict
    depth = 1 # type: int
    ):
    # type: (...) -> List[Text]
    """key as the depth-level title, value as the text"""
    res = []
    for k, v in messages.items():
        res.append(u'{} {}'.format(u'#'*depth, u'{}'.format(k).strip()))
        if isinstance(v, dict):
            res += _flattern_messages_to_md_lines(v, depth=depth+1)
        else:
            res.append(u'{}'.format(v).rstrip()) # rstrip to remove extra '\n'
    return res


def say_something_if_mentioned(
    event, # type: Text
    payload, # type: Dict
    logger, # type: logging.Logger
    client, # type: github3.github.GitHub
    client_user # type: Text
    ):
    # type: (...) -> bool
    """echo info if mentioned in issue"""
    if not (
        (
            event == 'issue_comment' and
            payload['action'] in {'created', 'edited'}
        ) or (
            event == 'issues' and
            payload['action'] in {'opened', 'edited'}
        )
    ):
        return False

    person = payload['issue']['sender']['login'] # type: Text
    body = '' # type: Text
    if event == 'issues':
        body = payload['issue']['body']
    elif event == 'issue_comment':
        body = payload['comment']['body']
    else:
        assert False

    # very important to avoid infinite mention!!!
    if person == client_user:
        return False

    pattern = re.compile(
        r'(?:[^a-zA-Z0-9]|^)(@{})(?:[^a-zA-Z0-9]|$)'.format(client_user))
    if pattern.search(body) is None:
        # no mention, no talk
        return False

    # if 'created', we only need to check whether be mentioned
    if payload['action'] == 'created':
        pass

    # if 'edited', we check the 'from' and current,
    # if the 'mention' is the first time, we react.
    elif payload['action'] == 'edited':
        if 'body' not in payload['changes']:
            # body has not been changed,
            # we don't do anything because we had been mentioned.
            return False
        if pattern.search(payload['changes']['body']['from']) is not None:
            # although the body has been changed,
            # we had been mentioned before, so do nothing this time.
            return False

    # huh?
    else:
        assert False

    body_lines = body.split('\n')
    omit_threshold = 3
    ellipsis = u'\n> ...' if len(body_lines) > omit_threshold else u''
    quote_body = u'\n'.join([u'> {}'.format(x) for x in body_lines[:omit_threshold]]) + ellipsis
    comment = (
        u'{quote_body}\n\nHi @{person} you mentioned me!\n'
        u'But I am too busy right now.'
    ).format(quote_body=quote_body, person=person)

    url_info = extract_info_from_url(payload['issue']['url'])
    issue = client.issue(
        url_info['owner'], url_info['repo'], url_info['number'])
    issue.create_comment(comment)
    return True
