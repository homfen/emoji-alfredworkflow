# !/usr/bin/python
# encoding: utf-8

import sys
from workflow import Workflow3

ICON_DEFAULT = 'icon.png'


def Version(v):
    return '0.1'


def main(wf):

    if wf.update_available:
        wf.start_update()
    else:
        wf.add_item('暂无可用新版本', icon=ICON_DEFAULT)

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3(
        update_settings={
            'github_slug': 'KURANADO2/emoji-alfredworkflow',
            '__workflow_autoupdate': True,
            # 自动检测新版本频率，单位 day
            'frequency': 1
        })

    logger = wf.logger

    sys.exit(wf.run(main))
